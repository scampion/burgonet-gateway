-- Retrieve the token from the request header
local bearer = ngx.req.get_headers()["Authorization"]

-- Check if the Authorization header is present and starts with 'Bearer '
if not bearer or not bearer:lower():find("^bearer ") then
    ngx.exit(ngx.HTTP_UNAUTHORIZED)
end

-- Extract the token (everything after 'Bearer ')
local token = bearer:sub(8)  -- 'Bearer ' is 7 characters long, so we start from the 8th character

-- Check if the token is present and not empty
if not token or token == "" then
    ngx.exit(ngx.HTTP_UNAUTHORIZED)
end

-- Connect to Redis
local redis = require "resty.redis"
local red = redis:new()
local redis_host = ngx.var.redis_host or "redis"
local redis_port = ngx.var.redis_port or 6379

red:set_timeout(1000)
local ok, err = red:connect(redis_host, redis_port)
if not ok then
    ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
    ngx.exit(ngx.HTTP_INTERNAL_SERVER_ERROR)
end

-- Validate token and get user ID
local user_id = red:get("token:" .. token)
if user_id == ngx.null then
    ngx.log(ngx.ERR, "User not found in Redis for token: ", token)
    ngx.exit(ngx.HTTP_UNAUTHORIZED)
end



-- Get the requested route
local route_path = ngx.var.uri
local route_key = "routes:" .. route_path
local blacklist_words = red:hget(route_key, "blacklist_words")
-- log the blacklist words
if blacklist_words then
    -- Check if the request contains any blacklisted words
    local request_body = ngx.req.get_body_data()
    request_body = request_body and request_body:lower()
    ngx.log(ngx.INFO, "🚫 Blacklist words: ", blacklist_words, " in request body: ", request_body)
    if request_body then
        for word in blacklist_words:gmatch("%S+") do
            word = word:lower()
            if request_body:find(word, 1, true) then
                ngx.status = ngx.HTTP_FORBIDDEN
                ngx.header.content_type = "text/plain"
                ngx.say("Request contains blacklisted word: ", word)
                ngx.exit(ngx.HTTP_FORBIDDEN)
            end
        end
    end
end


local disabled_groups = red:hget(route_key, "disabled_groups")
if not disabled_groups then
    ngx.exit(ngx.HTTP_FORBIDDEN)
end

-- Check if user belongs to any disabled group
local user_groups = red:smembers("user:" .. user_id .. ":groups")
for _, group_id in ipairs(user_groups) do
    if disabled_groups:find(group_id, 1, true) then
        ngx.exit(ngx.HTTP_FORBIDDEN)
    end
end

-- Authorization granted
red:set("cache:" .. token, user_id, 3600)

-- Close the connection
ngx.log(ngx.INFO, "Authorization granted for user ID: ", user_id)
