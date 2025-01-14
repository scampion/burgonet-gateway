-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    local response_body = ngx.ctx.buffered
    -- Check if response is JSON
    local content_type = ngx.header.content_type
    if content_type and string.find(content_type:lower(), "application/json") then
        -- Set the nginx variable for logging
        ngx.var.resp_body = response_body
        -- Also log to error log for debugging
        ngx.log(ngx.INFO, response_body)
    else
        -- Clear the response body for non-JSON content
        ngx.var.resp_body = ''
    end
end
