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
            local response_body = ngx.ctx.buffered

            -- Create JSON log entry
            local log_entry = {
                timestamp = timestamp,
                datetime = datetime,
                token = bearer_token,
                response = response_body
            }
            
            -- Convert to JSON string
            local json_log = require("cjson").encode(log_entry)
            
            -- Write to nginx error log
            ngx.log(ngx.INFO, json_log)
        end
    end
end
