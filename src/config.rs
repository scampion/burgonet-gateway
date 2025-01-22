// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use serde::Deserialize;
use std::fs;
use std::path::Path;
use anyhow::{Context, Result};
use pingora::prelude::*;

#[derive(Debug, Deserialize, Clone)]
pub struct QuotaPeriod {
    #[serde(default)]
    pub second: u64,
    #[serde(default)]
    pub minute: u64,
    #[serde(default)]
    pub hour: u64,
    #[serde(default)]
    pub day: u64,
    #[serde(default)]
    pub week: u64,
    #[serde(default)]
    pub month: u64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct Quota {
    pub max_tokens: Option<QuotaPeriod>,
    pub max_requests: Option<QuotaPeriod>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ModelConfig {
    pub location: String,
    pub model_name: String,
    pub proxy_pass: String,
    #[serde(default)]
    pub api_key: String,
    #[serde(default)]
    pub disabled_groups: String,
    #[serde(default)]
    pub blacklist_words: String,
    #[serde(default)]
    pub pii_protection_url: String,
    #[serde(default)]
    pub parser: String,
    #[serde(default)]
    pub quotas: Option<Vec<Quota>>,
}

#[derive(Debug, Deserialize)]
pub struct ServerConf {
    pub models: Vec<ModelConfig>,
    #[serde(default = "default_db_filepath")]
    pub db_filepath: String,
    #[serde(default = "default_port")]
    pub port: u16,
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_prometheus_host")]
    pub prometheus_host: String,
    #[serde(default = "default_prometheus_port")]
    pub prometheus_port: u16,
    #[serde(default = "default_trust_headers")]
    pub trust_header_authentication: Vec<String>,
}

fn default_trust_headers() -> Vec<String> {
    Vec::new()
}

fn default_port() -> u16 {
    6191
}

fn default_host() -> String {
    "localhost".to_string()
}

fn default_prometheus_host() -> String {
    "127.0.0.1".to_string()
}

fn default_prometheus_port() -> u16 {
    6192
}

fn default_db_filepath() -> String {
    "database.redb".to_string()
}


impl QuotaPeriod {

    // constructor
    pub fn new() -> Self {
        Self {
            second: 0,
            minute: 0,
            hour: 0,
            day: 0,
            week: 0,
            month: 0,
        }
    }

    // fucntion display the quota period
    pub fn display(&self) {
        println!("QuotaPeriod: second: {}, minute: {}, hour: {}, day: {}, week: {}, month: {}", self.second, self.minute, self.hour, self.day, self.week, self.month);
    }

    pub fn to_string(&self) -> String {
        format!("second: {}, minute: {}, hour: {}, day: {}, week: {}, month: {}", self.second, self.minute, self.hour, self.day, self.week, self.month)
    }
}

impl ServerConf {
    /// Load configuration from a YAML file
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let conf_str = fs::read_to_string(&path)
            .with_context(|| format!("Unable to read conf file from {}", path.as_ref().display()))?;

        let conf: Self = serde_yaml::from_str(&conf_str)
            .with_context(|| format!("Unable to parse yaml conf from {}", path.as_ref().display()))?;

        Ok(conf)
    }

    /// Load configuration from a YAML file with error handling for server startup
    pub fn from_file_or_exit<P: AsRef<Path>>(path: P) -> Self {
        let mut conf = Self::from_file(&path).unwrap_or_else(|e| {
            log::error!("Configuration error: {}", e);
            std::process::exit(1);
        });

        // Process each model's API key
        let mut processed_models = Vec::new();
        for model in conf.models {
            let processed_model = if model.api_key.starts_with('$') {
                let var_name = &model.api_key[1..];
                let api_key = std::env::var(var_name).unwrap_or_else(|_| {
                    log::error!("Environment variable {} not found", var_name);
                    "".to_string()
                });
                log::info!("Location {}: using API key from environment variable {}", model.location,var_name);
                ModelConfig {
                    api_key,
                    ..model
                }
            } else {
                model
            };
            processed_models.push(processed_model);
        }

        conf.models = processed_models;
        conf
    }


}
