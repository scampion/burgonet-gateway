// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.
// External crates
use async_trait::async_trait;
use base64::engine::general_purpose;
use base64::Engine;
use bytes::Bytes;
use log::{debug, error, info, trace, warn};
use once_cell::sync::Lazy;
use prometheus::register_int_counter;
use redb::{Database, TableDefinition};
use reqwest::Client;
use reqwest::Error as ReqwestError;
use flate2::read::GzDecoder;
use http::header;

// Pingora-related imports
use pingora::prelude::*;
use pingora_http::ResponseHeader;
use pingora_limits::rate::Rate;
use pingora_proxy::{ProxyHttp, Session};
use pingora::protocols::http::SERVER_NAME;

// Internal modules
use crate::config;
use crate::parsers;
use crate::pii_protection;
use crate::token_limit;
use crate::rate_limit;
use crate::app;

// Re-exports from internal modules
use config::{ModelConfig, QuotaPeriod, ServerConf};
use parsers::{parse, parser_ollama};
use token_limit::{check_token_limits, update_usage_periods};
use rate_limit::check_rate_limits;

// Constants and lazy statics
use std::sync::Arc;
use std::io::Read;



const TOKENS: TableDefinition<&str, &str> = TableDefinition::new("tokens");
const USAGE: TableDefinition<&str, u64> = TableDefinition::new("usage");
const GROUPS: TableDefinition<&str, &str> = TableDefinition::new("groups");

fn check_login(req: &pingora_http::RequestHeader) -> bool {
    // implement you logic check logic here
    req.headers.get("Authorization").map(|v| v.as_bytes()) == Some(b"password")
}

fn contains_word_case_insensitive(text: &[u8], word: &str) -> bool {
    // Convert the word to lowercase
    let lowercase_word = word.to_lowercase();

    // Convert the text to lowercase
    let lowercase_text = String::from_utf8_lossy(text).to_lowercase();

    // Check if the lowercase word exists in the lowercase text
    let result = lowercase_text.contains(&lowercase_word);
    info!("result: {:?}", result);
    result
}

pub struct BurgonetGateway {
    pub req_metric: prometheus::IntCounter,
    pub input_tokens: prometheus::IntCounter,
    pub output_tokens: prometheus::IntCounter,
    pub conf: Arc<ServerConf>,
    pub db: Arc<Database>,
}



pub struct GatewayContext {
    pub model: Option<Arc<ModelConfig>>,
    pub read_txn: Option<redb::ReadTransaction>,
    pub write_txn: Option<redb::WriteTransaction>,
    buffer: Vec<u8>,
    token: Option<String>,
    pub user: Option<String>,
    pub time: chrono::DateTime<chrono::Utc>,
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub usage_input: QuotaPeriod,
    pub usage_output: QuotaPeriod,
    pub upstream_headers: ResponseHeader,

}


// Implement Send and Sync since all fields are thread-safe
unsafe impl Send for GatewayContext {}
unsafe impl Sync for GatewayContext {}


#[async_trait]
impl ProxyHttp for BurgonetGateway {
    type CTX = GatewayContext;
    fn new_ctx(&self) -> Self::CTX {
        GatewayContext {
            model: None,
            read_txn: Some(self.db.begin_read().expect("Failed to begin read transaction")),
            write_txn: Some(self.db.begin_write().expect("Failed to begin write transaction")),
            buffer: Vec::new(),
            token: None,
            user: None,
            time: chrono::Utc::now(),
            input_tokens: 0,
            output_tokens: 0,
            usage_input: QuotaPeriod::new(),
            usage_output: QuotaPeriod::new(),
            upstream_headers: ResponseHeader::build_no_case(200, Some(0)).expect("Failed to build response header"),
        }
    }


    async fn request_filter(&self, session: &mut Session, ctx: &mut Self::CTX) -> Result<bool> {
        info!("request_filter");
        trace!("Start of request_filter: {:?}", session.req_header().uri.path());

        // if uri is / or /login, return early a yaml message with the configuration of models
        if session.req_header().uri.path() == "/"  {
            debug!("Returning configuration from request_filter");
            return Ok(true);
        }

        // test if the request contain a bearer token
        let token = session.req_header().headers.get("Authorization")
            .and_then(|v| v.to_str().ok())
            .and_then(|s| s.strip_prefix("Bearer "));

        debug!("token: {:?}", token);


        if let Some(token) = token {
            if let Some(read_txn) = &ctx.read_txn {
                let table = read_txn.open_table(TOKENS).expect("Failed to open table");

                match table.get(token) {
                    Ok(Some(value)) if !value.value().is_empty() => {
                        trace!("Token is valid");
                        ctx.token = Some(token.to_string());
                        ctx.user = Some(value.value().to_string());
                    }
                    _ => {
                        warn!("Invalid token, request : {:?}", session.req_header().uri.path());
                        let _ = session.respond_error(401).await;
                        return Ok(true);
                    }
                }
            }
        } else if self.conf.trust_header_authentication.iter().any(|h| session.req_header().headers.contains_key(h)) {
            let user = self.conf.trust_header_authentication.iter()
                .find_map(|h| session.req_header().headers.get(h))
                .and_then(|v| v.to_str().ok());

            if let Some(user) = user {
                ctx.user = Some(user.to_string());
            }
            debug!("User from trusted header: {:?}", ctx.user);
        } else  {
            let _ = session.respond_error(401).await;
            return Ok(true);
        }

        trace!("request: {:?}", session.req_header().uri.path());

        let model = self.conf.models.iter()
            .find(|m| m.location == session.req_header().uri.path())
            .cloned()
            .map(Arc::new);

        println!("URI {}", session.req_header().uri.path());

        if model.is_none() {
            let _ = session.respond_error(404).await;
            return Ok(true);
        }
        trace!("model: {:?}", model);

        ctx.model = model;
        // Skip quota check if no user is set
        let Some(user) = &ctx.user else {
            return Ok(false);
        };

        // Check rate limits
        if let Err(response) = check_rate_limits(&ctx, session).await {
            return Err(response);
        }

        //
        // get the usage of the user for quota check
        let read_txn = self.db.begin_read().expect("Failed to begin read transaction");


        // Check groups are allowed to access the location
        let table = read_txn.open_table(GROUPS).expect("Failed to open table");
        let groups = match table.get(user.as_ref() as &str) {
            Ok(Some(access_guard)) => access_guard.value().split(',').map(|s| s.trim().to_string()).collect::<Vec<String>>(),
            _ => {
                warn!("User {} not found in groups table", user);
                Vec::new() // Return empty vector if user not found
            }
        };

        let model = ctx.model.as_ref().unwrap();
        let disabled_groups = model.disabled_groups.split(',').map(str::trim).collect::<Vec<&str>>();
        // find if the user group is in the disabled groups
        if groups.iter().any(|g| disabled_groups.contains(&g.as_str())) {
            let error_message = format!("User {} in a disabled group", user);
            warn!("{}", error_message);
            //return Err(Error::explain(HTTPStatus(403), error_message));
            let _ = session.respond_error(401).await;
            return Ok(true);

        }
        // Check token limits
        if let Err(response) = check_token_limits(ctx, session).await {
            return Err(response);
        }

        // change the accept header to  "text/plain"
        let _ = session.req_header_mut().insert_header("Accept", "text/plain");

        trace!("End of request_filter: {:?}", session.req_header().uri.path());
        Ok(false)
    }

    async fn request_body_filter(
        &self,
        _session: &mut Session,
        _body: &mut Option<Bytes>,
        _end_of_stream: bool,
        _ctx: &mut Self::CTX,
    ) -> Result<()>
    where
        Self::CTX: Send + Sync,
    {
        if _session.req_header().uri.path() == "/"  {
            debug!("Returning configuration from request_body_filter");
            return Ok(());
        }

        if let Some(b) = _body {
            _ctx.buffer.extend(&b[..]);
            b.clear();
        }
        if _end_of_stream {
            *_body = Some(Bytes::from(std::mem::take(&mut _ctx.buffer)));

            if let Some(model) = &_ctx.model {
                if let Some(text) = _body.as_ref() {

                    // test if the request body contain a blacklisted word
                    for word in model.blacklist_words.split(',').map(str::trim).filter(|w| !w.is_empty()) {
                        trace!("word: {}", word);
                        trace!("text: {:?}", text);
                        if contains_word_case_insensitive(text, word) {
                            let user = _ctx.user.as_ref().unwrap();
                            warn!("Blacklisted word found in request body: {} and user {}", word, user);
                            return Err(Error::explain(HTTPStatus(403), "Blacklisted word found in request body"));
                        }
                    }

                    // Check PII protection if configured
                    if !model.pii_protection_url.is_empty() {
                        if let Err(e) = pii_protection::check_pii_protection(&model.pii_protection_url, text).await {
                            warn!("PII detected for user : {}", &_ctx.user.as_ref().unwrap());
                            return Err(e);
                        }
                    }
                }
            }
        }
        return Ok(());
    }

    async fn upstream_peer(
        &self,
        session: &mut Session,
        ctx: &mut Self::CTX,
    ) -> Result<Box<HttpPeer>> {


        let model = ctx.model.as_ref().ok_or_else(|| {
            anyhow::anyhow!("No model found for request")
        }).unwrap();

        trace!("model: {:?}", model);

        let proxy_url = url::Url::parse(&model.proxy_pass)
            .map_err(|e| anyhow::anyhow!("Invalid proxy_pass URL: {}", e));

        // extract uri from the proxy_url
        let uri = proxy_url.as_ref().map(|u| u.path()).unwrap().to_string();

        // replace the uri with the path from the request
        session.req_header_mut().set_uri(uri.as_str().parse().unwrap());

        let host = proxy_url.as_ref().map(|u| u.host_str().unwrap());

        trace!("host: {:?}", host);

        let port = proxy_url.as_ref().map(|u| u.port().unwrap_or(443));
        // unwrap is safe because we have already checked the host
        let addr = (host.unwrap(), port.unwrap());

        //let addr = (host.unwrap(), 443);
        trace!("connecting to {addr:?}");

        let tls = proxy_url.as_ref().map(|u| u.scheme() == "https").unwrap();
        trace!("tls: {:?}", tls);
        let peer = Box::new(HttpPeer::new(addr, tls, host.unwrap().to_string()));
        trace!("peer: {:?}", peer);

        // add header Authorization to the request for the peer with the api key
        let api_key = model.api_key.clone();
        let _ = session.req_header_mut().insert_header("Authorization", "Bearer ".to_string() + &api_key);
        // add Content-Type: application/json
        let _ = session.req_header_mut().insert_header("Content-Type", "application/json");

        // add host header
        let _ = session.req_header_mut().insert_header("Host", host.unwrap());

        trace!("session.req_header_mut(): {:?}", session.req_header_mut());
        Ok(peer)
    }


    async fn response_filter(
        &self,
        _session: &mut Session,
        upstream_response: &mut ResponseHeader,
        _ctx: &mut Self::CTX,
    ) -> Result<()>
    where
        Self::CTX:  Send + Sync,
    {

        _ctx.upstream_headers = upstream_response.clone();

        // Add CORS headers
        upstream_response
            .insert_header("Access-Control-Allow-Origin", "*")
            .unwrap();
        upstream_response
            .insert_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            .unwrap();
        upstream_response
            .insert_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            .unwrap();

        // Replace existing header if any
        upstream_response
            .insert_header("Server", "Burgonet")
            .unwrap();
        // Because we don't support h3
        upstream_response.remove_header("alt-svc");

        upstream_response.remove_header("Content-Encoding");
        upstream_response.remove_header("content-encoding");

        upstream_response.remove_header("Content-Length");
        upstream_response
            .insert_header("Transfer-Encoding", "Chunked")
            .unwrap();

        Ok(())
    }

    fn response_body_filter(
        &self,
        _session: &mut Session,
        body: &mut Option<Bytes>,
        end_of_stream: bool,
        _ctx: &mut Self::CTX,
    ) -> Result<Option<std::time::Duration>>
    where
        Self::CTX: Send + Sync,
    {
        if let Some(b) = body {
            _ctx.buffer.extend(&b[..]);
            b.clear();
        }
        if end_of_stream {

            // test if _ctx.upstream_headers contains the header "content-encoding" with value "gzip"
            if let Some(content_encoding) = _ctx.upstream_headers.headers.get("content-encoding") {
                if content_encoding == "gzip" {
                    let mut decoder = flate2::read::GzDecoder::new(&_ctx.buffer[..]);
                    let mut decoded = Vec::new();
                    decoder.read_to_end(&mut decoded).unwrap();
                    _ctx.buffer = decoded;
                }
            }
            let json_body = serde_json::de::from_slice(&_ctx.buffer).unwrap();
            *body = Some(Bytes::from(std::mem::take(&mut _ctx.buffer)));

            if let Some(model) = &_ctx.model {
                match parse(&json_body, &model.parser) {
                    Ok((input_tokens, output_tokens)) => {
                        _ctx.input_tokens = input_tokens;
                        _ctx.output_tokens = output_tokens;
                    }
                    Err(e) => {
                        error!("Error parsing response: {}", e);
                        return Err(Error::explain(ErrorType::InternalError, "Error parsing response"));
                    }
                }
            }
        }
        Ok(None)
    }


    async fn logging(
        &self,
        session: &mut Session,
        _e: Option<&pingora_core::Error>,
        ctx: &mut Self::CTX,
    ) {
        debug!("logging uri path: {:?}", session.req_header().uri.path());
        if session.req_header().uri.path() == "/" {
            let locations: Vec<std::collections::HashMap<String, String>> = self.conf.models.iter().map(|m| {
                let mut map = std::collections::HashMap::new();
                map.insert(m.model_name.clone(), m.location.clone());
                map
            }).collect();

            let json_conf = serde_json::to_string(&locations).unwrap();
            session.set_keepalive(None);
            let mut resp = ResponseHeader::build(200, Some(4)).unwrap();
            resp.insert_header(header::SERVER, &SERVER_NAME[..]).unwrap();
            session.write_response_header(Box::new(resp), true).await;
            session.write_response_body(Some(Bytes::from(json_conf.into_bytes())), true).await;
            debug!("Returning configuration from logging");

        } else {
            let response_code = session
                .response_written()
                .map_or(0, |resp| resp.status.as_u16());
            info!("{} response code: {response_code}", self.request_summary(session, ctx));

            self.req_metric.inc();
            self.input_tokens.inc_by(ctx.input_tokens);
            self.output_tokens.inc_by(ctx.output_tokens);

            //get the current time in hour
            let current_time = std::time::SystemTime::now();
            //format the time to get the current hour YYYY-MM-DD-HH
            let current_hour = chrono::Utc::now().format("%Y%m%d%H").to_string();
            // store in the table usage the number of tokens used by the user with key current_hour:user:input_tokens
            update_usage_periods(ctx);
        }
    }
}
