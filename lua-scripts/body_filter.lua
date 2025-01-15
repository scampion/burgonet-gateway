-- Capture response body for logging
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    local response_body = ngx.ctx.buffered
    ngx.var.resp_body = response_body

    -- Handle error responses
    if ngx.status >= 400 then
        -- Get additional request details
        local request_method = ngx.req.get_method()
        local request_uri = ngx.var.request_uri
        local remote_addr = ngx.var.remote_addr
        local upstream_status = ngx.var.upstream_status or "N/A"
        local request_time = ngx.var.request_time or "N/A"
        local model_name = ngx.var.model_name or "N/A"
        -- remove all break lines in response_body
        response_body = string.gsub(response_body, "\n", "")
        -- Construct detailed error message
        local error_details = string.format([[🚨️ Error Requests status: %d Request Method: %s Request URI: %s Client IP: %s Upstream Status: %s Request Time: %s Model Name: %s Response Body: %s ]], ngx.status, request_method, request_uri, remote_addr, upstream_status, request_time, model_name, response_body)
        ngx.log(ngx.ERR, error_details)
        
        -- Replace the response body with the error message
        ngx.arg[1] = response_body
    end
end
