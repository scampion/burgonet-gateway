// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use crate::config::{QuotaPeriod, ModelConfig};
use redb::{ReadTransaction, WriteTransaction, TableDefinition};
use std::collections::HashMap;
use anyhow::Result;
use crate::app::gateway::GatewayContext;
use log::{info, error};
use pingora::Error;
use pingora::http::ResponseHeader;
use pingora::HTTPStatus;
use pingora_proxy::Session;

const USAGE: TableDefinition<&str, u64> = TableDefinition::new("usage");

pub fn extract_usage_keys(user: &str, current_time: chrono::DateTime<chrono::Utc>) -> HashMap<String, String> {
    let mut keys = HashMap::new();

    let current_minute = current_time.format("%Y%m%d%H%M").to_string();
    let current_hour = current_time.format("%Y%m%d%H").to_string();
    let current_day = current_time.format("%Y%m%d").to_string();
    let current_week = current_time.format("%Y%W").to_string();
    let current_month = current_time.format("%Y%m").to_string();

    keys.insert("input_key_minute".to_string(), format!("M:{}:{}:in", current_minute, user));
    keys.insert("output_key_minute".to_string(), format!("M:{}:{}:out", current_minute, user));
    keys.insert("input_key_hour".to_string(), format!("H:{}:{}:in", current_hour, user));
    keys.insert("output_key_hour".to_string(), format!("H:{}:{}:out", current_hour, user));
    keys.insert("input_key_day".to_string(), format!("d:{}:{}:in", current_day, user));
    keys.insert("output_key_day".to_string(), format!("d:{}:{}:out", current_day, user));
    keys.insert("input_key_week".to_string(), format!("W:{}:{}:in", current_week, user));
    keys.insert("output_key_week".to_string(), format!("W:{}:{}:out", current_week, user));
    keys.insert("input_key_month".to_string(), format!("m:{}:{}:in", current_month, user));
    keys.insert("output_key_month".to_string(), format!("m:{}:{}:out", current_month, user));

    keys
}


struct TokenLimitConfig {
    limit: u64,
    remaining: u64,
    reset_seconds: u64,
}

pub async fn check_token_limits(
    ctx: &mut GatewayContext,
    session: &mut Session
) -> pingora::Result<()> {

    let current_time = chrono::Utc::now();
    let read_txn = ctx.read_txn.as_ref().ok_or_else(|| {
        error!("No read transaction available");
        Error::explain(HTTPStatus(500), "Internal server error")
    })?;
    match get_usage_periods(read_txn, &ctx.user.as_ref().unwrap(), current_time) {
        Ok((usage_input, usage_output)) => {
            ctx.usage_input = usage_input;
            ctx.usage_output = usage_output;
        }
        Err(e) => {
            error!("Failed to get usage periods: {}", e);
            return Err(Error::explain(HTTPStatus(500), "Internal server error"));
        }
    }

    let usage_input = &ctx.usage_input;
    let usage_output = &ctx.usage_output;

    if let Some(quotas) = &ctx.model.as_ref().unwrap().quotas {
        for quota in quotas {
            if let Some(max_tokens) = &quota.max_tokens {
                if max_tokens.minute > 0 && usage_input.minute + usage_output.minute > max_tokens.minute {
                    let config = get_token_limit_config(max_tokens.minute, usage_input.minute + usage_output.minute, 60).unwrap();
                    handle_token_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Minutely Token limit exceeded"));
                }
                if max_tokens.hour > 0 && usage_input.hour + usage_output.hour > max_tokens.hour {
                    let config = get_token_limit_config(max_tokens.hour, usage_input.hour + usage_output.hour, 3600).unwrap();
                    handle_token_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Hourly Token limit exceeded"));
                }
                if max_tokens.day > 0 && usage_input.day + usage_output.day > max_tokens.day {
                    let config = get_token_limit_config(max_tokens.day, usage_input.day + usage_output.day, 86400).unwrap();
                    handle_token_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Daily Token limit exceeded"));
                }
                if max_tokens.week > 0 && usage_input.week + usage_output.week > max_tokens.week {
                    let config = get_token_limit_config(max_tokens.week, usage_input.week + usage_output.week, 604800).unwrap();
                    handle_token_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Weekly Token limit exceeded"));
                }
                if max_tokens.month > 0 && usage_input.month + usage_output.month > max_tokens.month {
                    let config = get_token_limit_config(max_tokens.month, usage_input.month + usage_output.month, 2592000).unwrap();
                    handle_token_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Monthly Token limit exceeded"));
                }
            }
        }
    }
    Ok(())
}


fn get_token_limit_config(limit: u64, current: u64, reset_seconds: u64) -> Option<TokenLimitConfig> {
    if limit > 0 && current > limit {
        Some(TokenLimitConfig {
            limit,
            remaining: 0,
            reset_seconds,
        })
    } else {
        None
    }
}


async fn handle_token_limit_exceeded(session: &mut Session, config: TokenLimitConfig) -> pingora::Result<bool> {
    let mut header = ResponseHeader::build(429, None).unwrap();
    header
        .insert_header("X-Token-Limit-Limit", config.limit.to_string())
        .unwrap();
    header
        .insert_header("X-Token-Limit-Remaining", config.remaining.to_string())
        .unwrap();
    header
        .insert_header("X-Token-Limit-Reset", config.reset_seconds.to_string())
        .unwrap();

    session.set_keepalive(None);
    session.write_response_header(Box::new(header), true).await?;
    Ok(true)
}



pub fn get_usage_periods(
    read_txn: &ReadTransaction,
    user: &str,
    current_time: chrono::DateTime<chrono::Utc>
) -> Result<(QuotaPeriod, QuotaPeriod)> {
    let mut usage_input = QuotaPeriod::new();
    let mut usage_output = QuotaPeriod::new();
    
    let keys = extract_usage_keys(user, current_time);
    let table = read_txn.open_table(USAGE)?;

    usage_input.minute = table.get(keys.get("input_key_minute").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_output.minute = table.get(keys.get("output_key_minute").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_input.hour = table.get(keys.get("input_key_hour").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_output.hour = table.get(keys.get("output_key_hour").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_input.day = table.get(keys.get("input_key_day").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_output.day = table.get(keys.get("output_key_day").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_input.week = table.get(keys.get("input_key_week").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_output.week = table.get(keys.get("output_key_week").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_input.month = table.get(keys.get("input_key_month").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    usage_output.month = table.get(keys.get("output_key_month").unwrap().as_str())
        .unwrap_or(None)
        .map(|v| v.value())
        .unwrap_or(0);

    Ok((usage_input, usage_output))
}

pub fn update_usage_periods(ctx: &mut GatewayContext) -> Result<()> {
    let user = ctx.user.as_ref().ok_or_else(|| {
        error!("No user in context");
        anyhow::anyhow!("No user in context")
    })?;

    let keys = extract_usage_keys(user, ctx.time);

    ctx.usage_input.minute = ctx.usage_input.minute + ctx.input_tokens;
    ctx.usage_output.minute = ctx.usage_output.minute + ctx.output_tokens;
    ctx.usage_input.hour = ctx.usage_input.hour + ctx.input_tokens;
    ctx.usage_output.hour = ctx.usage_output.hour + ctx.output_tokens;
    ctx.usage_input.day = ctx.usage_input.day + ctx.input_tokens;
    ctx.usage_output.day = ctx.usage_output.day + ctx.output_tokens;
    ctx.usage_input.week = ctx.usage_input.week + ctx.input_tokens;
    ctx.usage_output.week = ctx.usage_output.week + ctx.output_tokens;
    ctx.usage_input.month = ctx.usage_input.month + ctx.input_tokens;
    ctx.usage_output.month = ctx.usage_output.month + ctx.output_tokens;

    let write_txn = ctx.write_txn.take().ok_or_else(|| {
        error!("No write transaction available");
        Error::explain(HTTPStatus(500), "Internal server error")
    })?;
    {
        let mut table = write_txn.open_table(USAGE)?;
        
        // Create a vector of key-value pairs to insert
        let updates = vec![
            (keys.get("input_key_minute").unwrap().as_str(), ctx.usage_input.minute),
            (keys.get("output_key_minute").unwrap().as_str(), ctx.usage_output.minute),
            (keys.get("input_key_hour").unwrap().as_str(), ctx.usage_input.hour),
            (keys.get("output_key_hour").unwrap().as_str(), ctx.usage_output.hour),
            (keys.get("input_key_day").unwrap().as_str(), ctx.usage_input.day),
            (keys.get("output_key_day").unwrap().as_str(), ctx.usage_output.day),
            (keys.get("input_key_week").unwrap().as_str(), ctx.usage_input.week),
            (keys.get("output_key_week").unwrap().as_str(), ctx.usage_output.week),
            (keys.get("input_key_month").unwrap().as_str(), ctx.usage_input.month),
            (keys.get("output_key_month").unwrap().as_str(), ctx.usage_output.month),
        ];

        // Perform all inserts in a single transaction
        for (key, value) in updates {
            table.insert(key, value)?;
        }
    }

    write_txn.commit()?;
    info!("Updated usage periods for user {}", user);
    Ok(())
}

