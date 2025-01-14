-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    -- Get Authorization header
    local auth_header = ngx.var.http_authorization
    if auth_header then
        -- Extract Bearer token
        local bearer_token = string.match(auth_header, "Bearer%s+(.+)")
        if bearer_token then
            -- Get current timestamp
            local datetime = ngx.localtime()
            local timestamp = ngx.now()
            
            -- Get response status
            local status = ngx.status
            
            -- Get request details
            local request_method = ngx.var.request_method
            local request_uri = ngx.var.request_uri
            local remote_addr = ngx.var.remote_addr
            
            -- Format response body
            local response_body = ngx.ctx.buffered
            local content_type = ngx.header["Content-Type"] or ""
            
            -- Create JSON log entry
            local log_entry = {
                timestamp = timestamp,
                datetime = datetime,
                status = status,
                method = request_method,
                uri = request_uri,
                remote_addr = remote_addr,
                authorization = bearer_token,
                content_type = content_type,
                response = response_body
            }
            
            -- Convert to JSON string
            local json_log = require("cjson").encode(log_entry)
            
            -- Write to nginx error log
            ngx.log(ngx.INFO, json_log)
        end
    end
end
