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
use crate::app::admin::HttpAdminApp;

static REQ_COUNTER: Lazy<IntCounter> =
    Lazy::new(|| register_int_counter!("chat_req_counter", "Number of chat requests").unwrap());

const CHAT_HISTORY: TableDefinition<&str, &str> = TableDefinition::new("chat_history");

pub struct HttpChatApp {
    pub admin: HttpAdminApp,
}

pub fn chat_service_http(db: Arc<redb::Database>) -> pingora_core::services::listening::Service<HttpChatApp> {
    pingora_core::services::listening::Service::new(
        "Chat HTTP Service".to_string(),
        HttpChatApp { 
            admin: HttpAdminApp { db } 
        },
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
            _ => {
                self.admin.json_response(StatusCode::NOT_FOUND, serde_json::json!({"error": "Not Found"}))
            }
        }
    }
}

impl HttpChatApp {
    fn is_embedded(&self, uri: &str) -> bool {
        self.admin.is_embedded(uri)
    }

    fn handle_static_asset(&self, uri: &str) -> Response<Vec<u8>> {
        self.admin.handle_static_asset(uri)
    }

}
