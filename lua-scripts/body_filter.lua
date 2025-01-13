-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    -- Only log if we have an API key
    if ngx.var.apikey and ngx.var.apikey ~= "" then
        -- Create JSON log entry
        local log_entry = string.format(
            '{"api_key":"%s","response":"%s"}\n',
            ngx.var.apikey,
            ngx.escape_uri(ngx.ctx.buffered)
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
