#!/usr/bin/env python3

import responder
import redis

api   = responder.API()
redis = redis.StrictRedis(host='localhost', port=6379, db=0)

@api.route(before_request=True)
def prepare_response(req, resp):
    resp.headers['X-Pizza'] = '42'

@api.route("/{cat}/{name}")
async def greet_world(req, resp, *, cat, name):
    resp.text = f"{cat}/{name}!"
    cache_write('mykey', resp.text)

@api.route("/{cat}/{name}/json")
async def test2(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name}

def cache_read(key):
    return redis.get(key)

def cache_write(key, val):
    redis.set(key, val)

def cache_clear():
    redis.flushdb()

if __name__ == '__main__':
    api.run()
