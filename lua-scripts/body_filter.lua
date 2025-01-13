-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body
if ngx.arg[2] then
    ngx.var.resp_body = ngx.ctx.buffered
end
