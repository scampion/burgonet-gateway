-- Capture response body for logging and Redis storage
local redis = require "resty.redis"
local resp_body = ngx.arg[1]
ngx.ctx.buffered = (ngx.ctx.buffered or "") .. resp_body

if ngx.arg[2] then
    -- Set response body for logging
    ngx.var.resp_body = ngx.ctx.buffered
    
    -- Only store responses for API calls
    if ngx.var.apikey and ngx.var.apikey ~= "" then
        -- Limit stored body to first 1000 chars to prevent excessive memory usage
        local stored_body = string.sub(ngx.ctx.buffered, 1, 1000)
        
        -- Connect to Redis
        local red = redis:new()
        red:set_timeout(1000)  -- 1 second timeout
        
        local ok, err = red:connect("redis", 6379)
        if not ok then
            ngx.log(ngx.ERR, "failed to connect to Redis: ", err)
            return
        end
        
        -- Store response body in Redis list
        local redis_key = "resp_body:" .. ngx.var.apikey
        local res, err = red:lpush(redis_key, stored_body)
        if not res then
            ngx.log(ngx.ERR, "failed to store response in Redis: ", err)
        end
        
        -- Set expiration (1 hour) and limit list size (100 items)
        red:expire(redis_key, 3600)
        red:ltrim(redis_key, 0, 99)
        
        -- Close Redis connection
        local ok, err = red:set_keepalive(10000, 100)
        if not ok then
            ngx.log(ngx.ERR, "failed to set keepalive: ", err)
        end
    end
end
