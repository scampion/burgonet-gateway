// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.
//
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
use log::LevelFilter;
use log4rs::append::console::ConsoleAppender;
use log4rs::append::file::FileAppender;
use log4rs::encode::pattern::PatternEncoder;
use log4rs::config::{Appender, Config, Logger, Root};
use std::io::stdout;

// Pingora-related imports
use pingora::prelude::*;
use pingora_http::ResponseHeader;
use pingora_limits::rate::Rate;
use pingora_proxy::{ProxyHttp, Session};

// Internal modules
mod config;
mod parsers;
mod pii_protection;
mod app;
mod rate_limit;
mod token_limit;
mod service;

use crate::app::gateway::BurgonetGateway;

// Re-exports from internal modules
use config::{ModelConfig, QuotaPeriod, ServerConf};
use parsers::{parse, parser_ollama};
//use quota::{check_quota, extract_usage_keys, get_usage_periods};
use rate_limit::check_rate_limits;

// Constants and lazy statics
use std::sync::Arc;


fn main() {
    env_logger::init();

    let db = Arc::new(Database::create("database.redb").expect("Failed to create database"));
    // create table if not exists
    let write_txn = db.begin_write().expect("Failed to begin write transaction");
    {
        const TOKENS: TableDefinition<&str, &str> = TableDefinition::new("tokens");
        const GROUPS: TableDefinition<&str, &str> = TableDefinition::new("groups");
        const USAGE: TableDefinition<&str, u64> = TableDefinition::new("usage");
        write_txn.open_table(TOKENS);
        write_txn.open_table(GROUPS);
        write_txn.open_table(USAGE);
    }
    write_txn.commit().expect("Failed to commit write transaction");

    if std::env::var("BURGONET_MODE").is_ok() && std::env::var("BURGONET_MODE").unwrap() == "dev" {
        warn!("🛠️ Development mode: populating database with test data 🛠️");
        let write_txn = db.begin_write().expect("Failed to begin write transaction");
        {
            const TOKENS: TableDefinition<&str, &str> = TableDefinition::new("tokens");
            const GROUPS: TableDefinition<&str, &str> = TableDefinition::new("groups");
            let mut table = write_txn.open_table(TOKENS).expect("Failed to open table");
            table.insert("your_token_here", "alice").expect("Failed to insert token");
            let mut table = write_txn.open_table(GROUPS).expect("Failed to open table");
            table.insert("alice", "admin, it, hr").expect("Failed to insert group");
        }
        write_txn.commit().expect("Failed to commit write transaction");
    }

    let conf = ServerConf::from_file_or_exit(
        Opt::parse_args().conf.unwrap_or_else(|| {
            log::error!("Error: No configuration file provided");
            std::process::exit(1);
        })
    );

    info!("Configuration loaded with {} models 👌", conf.models.len());


    // Logger
    let requests = FileAppender::builder()
        .encoder(Box::new(PatternEncoder::new("{d} - {m}{n}")))
        .build("log/requests.log")
        .unwrap();

    let config = Config::builder()
        .appender(Appender::builder().build("stdout", Box::new(stdout)))
        .appender(Appender::builder().build("requests", Box::new(requests)))
        .logger(Logger::builder().build("app::backend::db", LevelFilter::Info))
        .logger(Logger::builder()
            .appender("requests")
            .additive(false)
            .build("app::requests", LevelFilter::Info))
        .build(Root::builder().appender("stdout").build(LevelFilter::Warn))
        .unwrap();

    let handle = log4rs::init_config(config).unwrap();

    // Services

    let mut bgn_server = Server::new(Some(Opt::parse_args())).unwrap();
    bgn_server.bootstrap();

    let conf = Arc::new(conf);

    let mut bgn_gateway = pingora_proxy::http_proxy_service(
        &bgn_server.configuration,
        BurgonetGateway {
            req_metric: register_int_counter!("req_counter", "Number of requests").unwrap(),
            conf: conf.clone(),
            db: db.clone(),
            input_tokens: register_int_counter!("input_tokens", "Number of input tokens").unwrap(),
            output_tokens: register_int_counter!("output_tokens", "Number of output tokens").unwrap(),
        },
    );
    bgn_gateway.add_tcp(&format!("{}:{}", conf.host, conf.port));
    bgn_server.add_service(bgn_gateway);
    info!("Burgonet Gateway started on port http://{}:{}", conf.host, conf.port);

    let mut prometheus_service_http = pingora_core::services::listening::Service::prometheus_http_service();
    prometheus_service_http.add_tcp(&format!("{}:{}", conf.prometheus_host, conf.prometheus_port));
    bgn_server.add_service(prometheus_service_http);
    info!("Prometheus service started on port {}", conf.prometheus_port);

    let mut echo_service_http = service::echo::echo_service_http();
    echo_service_http.add_tcp(&format!("{}:{}", conf.echo_host, conf.echo_port));
    bgn_server.add_service(echo_service_http);
    info!("Echo service started on http://{}:{}", conf.echo_host, conf.echo_port);

    let mut chat_service_http = service::chat::chat_service_http(db.clone());
    chat_service_http.add_tcp(&format!("{}:{}", conf.chat_host, conf.chat_port));
    bgn_server.add_service(chat_service_http);
    info!("Chat service started on http://{}:{}", conf.chat_host, conf.chat_port);

    let mut admin_service_http = service::admin::admin_service_http(db);
    admin_service_http.add_tcp(&format!("{}:{}", conf.admin_host, conf.admin_port));
    bgn_server.add_service(admin_service_http);
    info!("Admin service started on http://{}:{}", conf.admin_host, conf.admin_port);


    bgn_server.run_forever();



}
