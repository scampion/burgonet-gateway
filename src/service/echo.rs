// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use crate::app::echo::HttpEchoApp;
use pingora::services::listening::Service;

pub fn echo_service_http() -> Service<HttpEchoApp> {
    Service::new("Echo Service HTTP".to_string(), HttpEchoApp)
}
