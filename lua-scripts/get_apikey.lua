local redis = require "resty.redis"
local red = redis:new()

red:set_timeout(1000)  -- 1 second timeout

local ok, err = red:connect("redis", 6379)
if not ok then
    ngx.log(ngx.ERR, "failed to connect to redis: ", err)
    return nil
end

local apikey, err = red:get("api:deepseek:v3:key")
if not apikey then
    ngx.log(ngx.ERR, "failed to get redis key: ", err)
    return nil
end

return apikey
