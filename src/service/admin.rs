// Copyright (c) 2025 Sébastien Campion, FOSS4. All rights reserved.
//
// This software is provided under the Commons Clause License Condition v1.0.
// See the LICENSE file for full license details.

use crate::app::admin::HttpAdminApp;
use pingora::services::listening::Service;
use std::sync::Arc;

pub fn admin_service_http(db: Arc<redb::Database>) -> Service<HttpAdminApp> {
    Service::new("Admin Service HTTP".to_string(), HttpAdminApp{db})
}
