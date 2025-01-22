// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use anyhow::Result;
use base64::engine::general_purpose;
use base64::Engine;
use bytes::Bytes;
use log::{info, warn, error};
use pingora::prelude::*;
use reqwest::Client;
use url::Url;

pub async fn check_pii_protection(
    pii_url: &str,
    request_body: &Bytes
) -> pingora::Result<()> {


    let url = match Url::parse(pii_url) {
        Ok(url) => url,
        Err(e) => {
            return Err(Error::explain(HTTPStatus(403), "Invalid PII protection URL"));
        }
    };
    let body_base64 = general_purpose::STANDARD.encode(request_body);
    let json_payload = format!(r#"{{"text": "{}"}}"#, body_base64);

    let client = reqwest::Client::new();
    let response = match client
        .post(url)
        .header("Content-Type", "application/json")
        .body(json_payload)
        .send()
        .await
    {
        Ok(resp) => resp,
        Err(_) => {
            return Err(Error::explain(HTTPStatus(500), "Failed to contact PII protection service"));
        }
    };

    match response.status().as_u16() {
        200 => Ok(()),
        400 => {
            return Err(Error::explain(HTTPStatus(403), "PII found in request body"))

        }
        _ => {
            return Err(Error::explain(HTTPStatus(403), "PII protection service error"))
        }
    }
}
