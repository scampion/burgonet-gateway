function check_token(token)
    --- Defaults
    local access_redis_host =  ngx.var.access_redis_host == ''
        and '127.0.0.1' or ngx.var.access_redis_host

    local access_redis_port = ngx.var.access_redis_port == ''
        and 6379 or ngx.var.access_redis_port

    local access_token_set = ngx.var.access_token_set == ''
        and 'nginx_tokens:bearer' or ngx.var.access_token_set
    ---

    local redis = require "resty.redis"
    local red = redis:new()

    red:set_timeout(1000)

    local ok, err = red:connect(access_redis_host, access_redis_port)
    if not ok then
        ngx.log(ngx.ERR, "failed to connect to the redis server: ", err)
        ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
        return false
    end

    local exists, err = red:sismember(access_token_set, token)
    if not exists then
        ngx.log(ngx.ERR, "failed to check token: ", err)
        ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
        return false
    end

    return exists == 1
end

function authenticate()
    local header = ngx.req.get_headers()['Authorization']
    if header == nil or header:find(" ") == nil then
        return false
    end

    local divider = header:find(' ')
    if header:sub(0, divider-1):lower() ~= 'bearer' then
        return false
    end

    local token = header:sub(divider+1)
    if token == nil or token == "" then
        return false
    end

    return check_token(token)
end

-- Get API key from Redis
local apikey = nil
local redis = require "resty.redis"
local red = redis:new()
red:set_timeout(1000)

local ok, err = red:connect("redis", 6379)
if ok then
    local model_name = ngx.var.access_model_name or "deepseek"
    local model_version = ngx.var.access_model_version or "v3"
    local redis_key = string.format("api:%s:%s:key", model_name, model_version)
    apikey, err = red:get(redis_key)
    if not apikey then
        ngx.log(ngx.ERR, "failed to get redis key: ", err)
    end
else
    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
end

-- Set API key as nginx variable
if apikey then
    ngx.var.apikey = apikey
end

local authenticated = authenticate()

if not authenticated then
    ngx.header.content_type = 'text/plain'
    ngx.header.www_authenticate = 'Bearer realm=""'
    ngx.status = ngx.HTTP_UNAUTHORIZED
    ngx.say('401 Access Denied')
    return ngx.exit(ngx.HTTP_UNAUTHORIZED)
end
