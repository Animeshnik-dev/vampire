import random
import base64

def build_lua(src: str, seed: int = None) -> str:
    if seed is None: seed = random.randint(1, 2**31)
    rng = random.Random(seed)
    
    encoded = base64.b64encode(src.encode('utf-8')).decode('utf-8')
    salt = "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(8))
    
    lua_code = f"""-- Vampire Obfuscator [🎃 PROTECTED EDITION]
-- Seed: {seed}

local function base64_decode(data)
    local b = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    data = string.gsub(data, '[^'..b..'=]', '')
    return (data:gsub('.', function(x)
        if (x == '=') then return '' end
        local r,f = '', (b:find(x) - 1)
        for i = 6, 1, -1 do r = r .. (f % 2 ^ i - f % 2 ^ (i - 1) > 0 and '1' or '0') end
        return r
    end):gsub('%d%d%d?%d?%d?%d?%d?%d?', function(x)
        if (#x ~= 8) then return '' end
        local c = 0
        for i = 1, 8 do c = c + (x:sub(i, i) == '1' and 2 ^ (8 - i) or 0) end
        return string.char(c)
    end))
end

local _0xSECRET = "{encoded}"
local _0xSALT = "{salt}"

local _0xPAYLOAD = base64_decode(_0xSECRET)
local _0xRUNNER = loadstring(_0xPAYLOAD)
if _0xRUNNER then
    _0xRUNNER()
end
"""
    return lua_code, seed, salt
