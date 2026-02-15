local key = KEYS[1]

local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local requested = tonumber(ARGV[3])
local now = tonumber(ARGV[4])

-- Fteching the existings state of bucket
local data = redis.call("HMGET",key,"tokens","last_refill")

local tokens = tonumber(data[1])
local last_refill = tonumber(data[2])

-- Initializing the token key bucket if it doesn't exist
if tokens == nil then
    tokens = capacity
    last_refill = now
end

-- Calculating the elapsed time
local elapsed = now - last_refill

-- Handling skewed clocks
if elapsed < 0 then
    elapsed = 0
end

-- Refilling tokens
local refill_tokens = elapsed * rate
tokens = math.min(capacity, tokens + refill_tokens)

-- Checking if enough tokens
if tokens < requested then
    return 0
end

-- Deduct token
tokens = tokens - requested

-- Saving updated state
redis.call("HMSET",key,"tokens",tokens,"last_refill",now)

-- Autocleaning up of resources
local ttl = math.ceil(capacity/rate) + 5
redis.call("EXPIRE",key,ttl)

return 1
