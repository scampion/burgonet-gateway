// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.
use async_trait::async_trait;
use bytes::Bytes;
use http::{Response, StatusCode};
use log::debug;
use once_cell::sync::Lazy;
use pingora_timeout::timeout;
use prometheus::{register_int_counter, IntCounter};
use std::sync::Arc;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use pingora::prelude::*;

use pingora::apps::http_app::ServeHttp;
use pingora::apps::ServerApp;
use pingora::protocols::http::ServerSession;
use pingora::protocols::Stream;
use pingora::server::ShutdownWatch;
use rust_embed::Embed;
use tree_magic;
use redb::TableDefinition;
use redb::ReadableTable;
use log::{error, info, trace, warn};
use std::collections::HashMap;



static REQ_COUNTER: Lazy<IntCounter> =
    Lazy::new(|| register_int_counter!("reg_counter", "Number of requests").unwrap());

const TOKENS: TableDefinition<&str, &str> = TableDefinition::new("tokens");
const USAGE: TableDefinition<&str, u64> = TableDefinition::new("usage");
const GROUPS: TableDefinition<&str, &str> = TableDefinition::new("groups");



pub struct HttpAdminApp {
    pub db: Arc<redb::Database>,
}

pub fn admin_service_http(db: Arc<redb::Database>) -> pingora_core::services::listening::Service<HttpAdminApp> {
    pingora_core::services::listening::Service::new(
        "Admin HTTP Service".to_string(),
        HttpAdminApp { db },
    )
}


#[derive(Debug)]
enum Period {
    Minutely,
    Hourly,
    Daily,
    Weekly,
    Monthly,
    All,
}

impl Period {
    fn from_str(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "minutely" => Self::Minutely,
            "hourly" => Self::Hourly,
            "daily" => Self::Daily,
            "weekly" => Self::Weekly,
            "monthly" => Self::Monthly,
            _ => Self::All,
        }
    }

    fn prefix(&self) -> Option<&str> {
        match self {
            Self::Minutely => Some("M:"),
            Self::Hourly => Some("H:"),
            Self::Daily => Some("d:"),
            Self::Weekly => Some("w:"),
            Self::Monthly => Some("m:"),
            Self::All => None,
        }
    }
}

#[derive(Embed)]
#[folder = "www/"]
struct Asset;


#[async_trait]
impl ServeHttp for HttpAdminApp {
    async fn response(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        REQ_COUNTER.inc();
        
        let uri = http_stream.req_header().uri.path();
        let method = http_stream.req_header().method.as_str();
        
        match (method, uri) {
            ("GET", "/") => self.handle_static_asset("index.html"),
            ("GET", path) if self.is_embedded(&path[1..]) => self.handle_static_asset(&path[1..]),
            ("GET", "/tokens") => self.handle_get_tokens(),
            ("POST", "/tokens") => self.handle_post_tokens(http_stream).await,
            ("DELETE", "/tokens") => self.handle_delete_tokens(http_stream).await,
            ("GET", "/usage") => self.handle_get_usage("all"),
            ("GET", "/usage/minutely") => self.handle_get_usage("minutely"),
            ("GET", "/usage/hourly") => self.handle_get_usage("hourly"),
            ("GET", "/usage/daily") => self.handle_get_usage("daily"),
            ("GET", "/usage/weekly") => self.handle_get_usage("weekly"),
            ("GET", "/usage/monthly") => self.handle_get_usage("monthly"),
            _ => {
                self.json_response(StatusCode::NOT_FOUND, serde_json::json!({"error": "Not Found"}))
            }
        }
        // // Explicitly close the connection for error responses
        // if response.status().is_client_error() || response.status().is_server_error() {
        //     if let Some(stream) = http_stream.downcast_mut::<Stream>() {
        //         self.json_response(StatusCode::NOT_FOUND, serde_json::json!({"error": "Not Found"}));
        //         let _ = stream.shutdown().await; // Gracefully close the TCP stream
        //     }
        // }
        //return self.json_response(StatusCode::NOT_FOUND, serde_json::json!({"error": "Not Found"}))
    }
}

impl HttpAdminApp {
    fn is_embedded(&self, uri: &str) -> bool {
        Asset::get(uri).is_some()
    }

    fn handle_static_asset(&self, uri: &str) -> Response<Vec<u8>> {
        if let Some(asset) = Asset::get(uri) {
            let body = asset.data.as_ref().to_vec();
            // if file ends with .html, set content type to text/html
            let content_type = match uri {
                uri if uri.ends_with(".html") => "text/html",
                uri if uri.ends_with(".css") => "text/css",
                uri if uri.ends_with(".js") => "application/javascript",
                _ => &tree_magic::from_u8(&body),
            };
            return Response::builder()
                .status(StatusCode::OK)
                .header(http::header::CONTENT_TYPE, content_type)
                .header(http::header::CONTENT_LENGTH, body.len())
                .body(body).unwrap();
        }
        return Response::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body("Asset can't be loaded".as_bytes().to_vec())
            .unwrap();
    }

    async fn read_json_body(&self, http_stream: &mut ServerSession) -> Result<serde_json::Value, Response<Vec<u8>>> {
        let read_timeout = 2000;
        let body = match timeout(
            Duration::from_millis(read_timeout),
            http_stream.read_request_body(),
        )
            .await
        {
            Ok(res) => match res.unwrap() {
                Some(bytes) => bytes,
                None => Bytes::from("{}"), // Return an empty JSON object if no body is present
            },
            Err(_) => {
                return Err(Response::builder()
                    .status(StatusCode::REQUEST_TIMEOUT)
                    .body(format!("Timed out after {}ms", read_timeout).into_bytes())
                    .unwrap());
            }
        };

        println!("Body: {:?}", body);

        // Attempt to parse the body as JSON
        match serde_json::from_slice(&body) {
            Ok(json_value) => Ok(json_value),
            Err(e) => {
                error!("Failed to parse JSON: {}", e);
                // If parsing fails, return a 400 Bad Request response with the error message
                Err(Response::builder()
                    .status(StatusCode::BAD_REQUEST)
                    .body(format!("Failed to parse JSON: {}", e).into_bytes())
                    .unwrap())
            }
        }
    }


    async fn handle_post_tokens(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        let json = match self.read_json_body(http_stream).await {
            Ok(json) => json,
            Err(response) => {
                return self.json_response(StatusCode::BAD_REQUEST, serde_json::json!({"error": "Invalid JSON"}));
            }
        };
        {
            let write_txn = self.db.begin_write().expect("Failed to begin write transaction");
            {
                let mut table = write_txn.open_table(TOKENS).expect("Failed to open table");
                if let Some(tokens) = json.get("tokens").and_then(|v| v.as_object()) {
                    for (token, user) in tokens {
                        if let Some(user_str) = user.as_str() {
                            // test if token length is greater than 32 otherwise return error
                            if token.as_str().len() < 32 {
                                error!("Token {} is too short", token.as_str());
                                return self.json_response(StatusCode::BAD_REQUEST, serde_json::json!({"error": "Token is too short"}));
                            } else {
                                table.insert(token.as_str(), user_str).expect("Failed to insert token");
                                info!("Token {} inserted for user {}", token.as_str(), user_str);
                            }
                        }
                    }
                }
            }
            write_txn.commit().expect("Failed to commit write transaction");
        }

        self.json_response(StatusCode::OK, serde_json::json!({"status": "ok"}))
    }

    async fn handle_delete_tokens(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        let json = match self.read_json_body(http_stream).await {
            Ok(json) => json,
            Err(response) => {
                return self.json_response(StatusCode::BAD_REQUEST, serde_json::json!({"error": "Invalid JSON"}));
            }
        };
        {
            let write_txn = self.db.begin_write().expect("Failed to begin write transaction");
            {
                let mut table = write_txn.open_table(TOKENS).expect("Failed to open table");
                for token in json.get("tokens").and_then(|v| v.as_array()).unwrap() {
                    if let Some(token_str) = token.as_str() {
                        table.remove(token_str).expect("Failed to remove token");
                        info!("Token {} removed", token_str);
                    }
                }
            }
            write_txn.commit().expect("Failed to commit write transaction");
        }

        self.json_response(StatusCode::OK, serde_json::json!({"status": "ok"}))
    }

    fn handle_get_tokens(&self) -> Response<Vec<u8>> {
        let read_txn = self.db.begin_read().expect("Failed to begin read transaction");
        let table = read_txn.open_table(TOKENS).expect("Failed to open table");
        let mut tokens = Vec::new();

        for entry in table.iter().into_iter().flatten() {
            if let Ok((key, value)) = entry {
                let token_key = key.value().to_string();
                let user_value = value.value().to_string();
                let mut token_map = std::collections::HashMap::new();
                token_map.insert(token_key, user_value);
                tokens.push(token_map);
            }
        }
        self.json_response(StatusCode::OK, &tokens)
    }

    fn handle_get_usage(&self, period: &str) -> Response<Vec<u8>> {
        let read_txn = self.db.begin_read().expect("Failed to begin read transaction");
        let table = read_txn.open_table(USAGE).expect("Failed to open table");
        let period_enum = Period::from_str(period);
        let usage: Vec<HashMap<String, u64>> = table
            .iter()
            .into_iter()
            .flatten()
            .filter_map(|entry| {
                entry.ok().and_then(|(key, value)| {
                    let user_key = key.value().to_string();
                    let usage_value = value.value();

                    // Filter based on period prefix if applicable
                    match period_enum.prefix() {
                        Some(prefix) if !user_key.starts_with(prefix) => None,
                        _ => {
                            let mut usage_map = HashMap::new();
                            usage_map.insert(user_key, usage_value);
                            Some(usage_map)
                        }
                    }
                })
            })
            .collect();
        self.json_response(StatusCode::OK, &usage)
    }


    fn json_response(&self, status: StatusCode, body: impl serde::Serialize) -> Response<Vec<u8>> {
        let body = serde_json::to_vec(&body).expect("Failed to serialize JSON");
        Response::builder()
            .status(status)
            .header(http::header::CONTENT_TYPE, "application/json")
            .header(http::header::CONTENT_LENGTH, body.len())
            .body(body)
            .unwrap()
    }

}

