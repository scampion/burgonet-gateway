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
    Lazy::new(|| register_int_counter!("chat_req_counter", "Number of chat requests").unwrap());

const CHAT_HISTORY: TableDefinition<&str, &str> = TableDefinition::new("chat_history");

pub struct HttpChatApp {
    pub db: Arc<redb::Database>,
}

pub fn chat_service_http(db: Arc<redb::Database>) -> pingora_core::services::listening::Service<HttpChatApp> {
    pingora_core::services::listening::Service::new(
        "Chat HTTP Service".to_string(),
        HttpChatApp { db },
    )
}

#[derive(Embed)]
#[folder = "www/"]
struct Asset;

#[async_trait]
impl ServeHttp for HttpChatApp {
    async fn response(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        REQ_COUNTER.inc();
        
        let uri = http_stream.req_header().uri.path();
        let method = http_stream.req_header().method.as_str();
        
        match (method, uri) {
            ("GET", "/") => self.handle_static_asset("chat.html"),
            ("GET", path) if self.is_embedded(&path[1..]) => self.handle_static_asset(&path[1..]),
            ("GET", "/api/conversations") => self.handle_get_conversations(),
            ("POST", "/api/conversations") => self.handle_post_conversation(http_stream).await,
            ("DELETE", "/api/conversations") => self.handle_delete_conversation(http_stream).await,
            _ => {
                self.json_response(StatusCode::NOT_FOUND, serde_json::json!({"error": "Not Found"}))
            }
        }
    }
}

impl HttpChatApp {
    fn is_embedded(&self, uri: &str) -> bool {
        Asset::get(uri).is_some()
    }

    fn handle_static_asset(&self, uri: &str) -> Response<Vec<u8>> {
        if let Some(asset) = Asset::get(uri) {
            let body = asset.data.as_ref().to_vec();
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
                None => Bytes::from("{}"),
            },
            Err(_) => {
                return Err(Response::builder()
                    .status(StatusCode::REQUEST_TIMEOUT)
                    .body(format!("Timed out after {}ms", read_timeout).into_bytes())
                    .unwrap());
            }
        };

        match serde_json::from_slice(&body) {
            Ok(json_value) => Ok(json_value),
            Err(e) => {
                error!("Failed to parse JSON: {}", e);
                Err(Response::builder()
                    .status(StatusCode::BAD_REQUEST)
                    .body(format!("Failed to parse JSON: {}", e).into_bytes())
                    .unwrap())
            }
        }
    }

    fn handle_get_conversations(&self) -> Response<Vec<u8>> {
        let read_txn = self.db.begin_read().expect("Failed to begin read transaction");
        let table = read_txn.open_table(CHAT_HISTORY).expect("Failed to open table");
        let mut conversations = Vec::new();

        for entry in table.iter().into_iter().flatten() {
            if let Ok((key, value)) = entry {
                let conversation_id = key.value().to_string();
                let conversation_data = value.value().to_string();
                let mut conversation_map = std::collections::HashMap::new();
                conversation_map.insert(conversation_id, conversation_data);
                conversations.push(conversation_map);
            }
        }
        self.json_response(StatusCode::OK, &conversations)
    }

    async fn handle_post_conversation(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        let json = match self.read_json_body(http_stream).await {
            Ok(json) => json,
            Err(response) => {
                return self.json_response(StatusCode::BAD_REQUEST, serde_json::json!({"error": "Invalid JSON"}));
            }
        };

        {
            let write_txn = self.db.begin_write().expect("Failed to begin write transaction");
            {
                let mut table = write_txn.open_table(CHAT_HISTORY).expect("Failed to open table");
                if let Some(conversation_id) = json.get("id").and_then(|v| v.as_str()) {
                    if let Some(conversation_data) = json.get("data").and_then(|v| v.as_str()) {
                        table.insert(conversation_id, conversation_data).expect("Failed to insert conversation");
                        info!("Conversation {} inserted", conversation_id);
                    }
                }
            }
            write_txn.commit().expect("Failed to commit write transaction");
        }

        self.json_response(StatusCode::OK, serde_json::json!({"status": "ok"}))
    }

    async fn handle_delete_conversation(&self, http_stream: &mut ServerSession) -> Response<Vec<u8>> {
        let json = match self.read_json_body(http_stream).await {
            Ok(json) => json,
            Err(response) => {
                return self.json_response(StatusCode::BAD_REQUEST, serde_json::json!({"error": "Invalid JSON"}));
            }
        };

        {
            let write_txn = self.db.begin_write().expect("Failed to begin write transaction");
            {
                let mut table = write_txn.open_table(CHAT_HISTORY).expect("Failed to open table");
                for conversation_id in json.get("ids").and_then(|v| v.as_array()).unwrap() {
                    if let Some(id_str) = conversation_id.as_str() {
                        table.remove(id_str).expect("Failed to remove conversation");
                        info!("Conversation {} removed", id_str);
                    }
                }
            }
            write_txn.commit().expect("Failed to commit write transaction");
        }

        self.json_response(StatusCode::OK, serde_json::json!({"status": "ok"}))
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
