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
            -- Check if response is JSON
            local content_type = ngx.header["Content-Type"]
            local response_body = ngx.ctx.buffered
            
            -- Only escape if not JSON
            if not content_type or not string.find(content_type:lower(), "application/json") then
                response_body = '"' .. ngx.escape_uri(response_body) .. '"'
            end

            -- Get current timestamp
            local timestamp = ngx.localtime()
            
            -- Create JSON log entry
            local log_entry = string.format(
                '{"timestamp":"%s","authorization":"%s","response": %s}\n',
                timestamp,
                bearer_token,
                response_body
            )
            
            -- Write to responses.log
        local log_path = "/var/log/nginx/responses.log"
        local file = io.open(log_path, "a")
        if file then
            file:write(log_entry)
            file:close()
        else
            ngx.log(ngx.ERR, "failed to open responses.log for writing")
        end
    end
end
end
