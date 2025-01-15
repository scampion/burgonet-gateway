-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    local response_body = ngx.ctx.buffered
    ngx.var.resp_body = response_body
    
    -- Handle error responses
    if ngx.status >= 400 then
        ngx.log(ngx.ERR, "Request failed with status: ", ngx.status, " Response: ", response_body)
        
        -- Modify response headers and body
        ngx.header.content_length = nil
        ngx.header.content_type = "application/json"
        
        -- Replace the response body with the error message
        ngx.arg[1] = response_body
    end
end
