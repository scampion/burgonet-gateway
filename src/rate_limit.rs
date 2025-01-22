// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use pingora::prelude::*;
use pingora_proxy::Session;
use std::time::Duration;
use crate::config::QuotaPeriod;
use pingora_limits::rate::Rate;
use once_cell::sync::Lazy;
use pingora::prelude::*;
use pingora::http::ResponseHeader;
use crate::app::gateway::GatewayContext;

static RATE_LIMITER_PER_SECOND: Lazy<Rate> = Lazy::new(|| Rate::new(Duration::from_secs(1)));
static RATE_LIMITER_PER_MINUTE: Lazy<Rate> = Lazy::new(|| Rate::new(Duration::from_secs(60)));


/// Represents rate limit configuration
struct RateLimitConfig {
    limit: isize,
    remaining: isize,
    reset_seconds: u64,
}

/// Checks all rate limits for the request
pub async fn check_rate_limits(
    ctx: &GatewayContext,
    session: &mut Session
) -> pingora::Result<()> {
    let curr_second = RATE_LIMITER_PER_SECOND.observe(&ctx.user.as_ref().unwrap(), 1);
    let curr_minute = RATE_LIMITER_PER_MINUTE.observe(&ctx.user.as_ref().unwrap(), 1);

    if let Some(quotas) = &ctx.model.as_ref().unwrap().quotas {
        for quota in quotas {
            if let Some(max_requests) = &quota.max_requests {
                // Check per-second rate limit
                if let Some(config) = get_rate_limit_config(max_requests.second, curr_second, 1) {
                    handle_rate_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Rate limit exceeded"));
                }

                // Check per-minute rate limit
                if let Some(config) = get_rate_limit_config(max_requests.minute, curr_minute, 60) {
                    handle_rate_limit_exceeded(session, config).await?;
                    return Err(Error::explain(HTTPStatus(429), "Rate limit exceeded"));
                }
            }
        }
    }
    Ok(())
}

/// Creates rate limit configuration if limit is exceeded
fn get_rate_limit_config(limit: u64, current: isize, reset_seconds: u64) -> Option<RateLimitConfig> {
    let limit = limit as isize;
    if limit > 0 && current > limit {
        Some(RateLimitConfig {
            limit,
            remaining: 0,
            reset_seconds,
        })
    } else {
        None
    }
}

/// Handles rate limit exceeded response
async fn handle_rate_limit_exceeded(session: &mut Session, config: RateLimitConfig) -> pingora::Result<bool> {
    let mut header = ResponseHeader::build(429, None).unwrap();
    header
        .insert_header("X-Rate-Limit-Limit", config.limit.to_string())
        .unwrap();
    header
        .insert_header("X-Rate-Limit-Remaining", config.remaining.to_string())
        .unwrap();
    header
        .insert_header("X-Rate-Limit-Reset", config.reset_seconds.to_string())
        .unwrap();
    
    session.set_keepalive(None);
    session
        .write_response_header(Box::new(header), true)
        .await?;
    Ok(true)
}

