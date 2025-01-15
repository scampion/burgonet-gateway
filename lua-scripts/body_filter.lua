if ngx.status ~= 200 then
    ngx.log(ngx.ERR, "Request failed ", ngx.status)
    -- forward the error to the client
    return
end

-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    local response_body = ngx.ctx.buffered
    ngx.var.resp_body = response_body
end
