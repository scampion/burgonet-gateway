local redis = require "resty.redis"
local red = redis:new()
red:set_timeout(1000)

-- Get Redis connection parameters
local access_redis_host = ngx.var.access_redis_host or "redis"
local access_redis_port = ngx.var.access_redis_port or 6379
local access_token_set = ngx.var.access_token_set or "nginx_tokens:bearer"

-- Connect to Redis
local ok, err = red:connect(access_redis_host, access_redis_port)
if not ok then
    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
end

-- Authenticate request
local function authenticate()
    local header = ngx.req.get_headers()['Authorization']
    if not header or not header:find(" ") then
        return false
    end

    local divider = header:find(' ')
    if header:sub(0, divider-1):lower() ~= 'bearer' then
        return false
    end

    local token = header:sub(divider+1)
    if not token or token == "" then
        return false
    end

    -- Check if token exists in Redis set
    local exists, err = red:sismember(access_token_set, token)
    if not exists then
        ngx.log(ngx.ERR, "failed to check token: ", err)
        return false
    end

    return exists == 1
end

-- Only proceed if authentication is successful
if not authenticate() then
    ngx.header.content_type = 'text/plain'
    ngx.header.www_authenticate = 'Bearer realm=""'
    ngx.status = ngx.HTTP_UNAUTHORIZED
    ngx.say('401 Access Denied')
    return ngx.exit(ngx.HTTP_UNAUTHORIZED)
end

