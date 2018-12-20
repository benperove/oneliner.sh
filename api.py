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
    redis.set('mykey', resp.text)

if __name__ == '__main__':
    api.run()
