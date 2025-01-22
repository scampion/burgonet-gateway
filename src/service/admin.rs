use crate::app::admin::HttpAdminApp;
use pingora::services::listening::Service;
use std::sync::Arc;

pub fn admin_service_http(db: Arc<redb::Database>) -> Service<HttpAdminApp> {
    Service::new("Admin Service HTTP".to_string(), HttpAdminApp{db})
}
