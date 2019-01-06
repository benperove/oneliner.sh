#!/usr/bin/env python3
#oneliner.sh
#benperove@gmail.com

import responder
import redis

api   = responder.API()
redis = redis.StrictRedis(host='localhost', port=6379, db=0)

#specify these headers for all requests
@api.route(before_request=True)
def prepare_headers(req, resp):
    resp.headers['X-Pizza'] = 'delicious'

#oneliner.sh logo
def logo(ip = None):
    logo = """
                   _                       _     
                  |  @benperove           | |    
   ___  _ __   ___| |_ _ __   ___ _ __ ___| |__  
  / _ \| '_ \ / _ \ | | '_ \ / _ \ '__/ __| '_ \ 
 | (_) | | | |  __/ | | | | |  __/ |_ \__ \ | | |
  \___/|_| |_|\___|_|_|_| |_|\___|_(_)|___/_| |_|
   """ + ip + """

"""
    return logo

#requests for a category and name
@api.route("/{cat}/{name}")
async def greet_world(req, resp, *, cat, name):
    ip, port  = req.headers['host'].split(':')
    resp.text = logo(ip) + f"{cat}/{name}!"
    cache_write(cat, name)

#requests for category and name with a json response
@api.route("/{cat}/{name}/json")
async def test2(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name}

#todo

#get a list of all the categories

#offer search suggestions

#process votes

#update result metadata

#colorize

#get 

#cache - get value
def cache_read(key):
    return redis.get(key)

#cache - set value
def cache_write(key, val):
    redis.set(key, val)

#cache - flush the entire cache db
def cache_clear():
    redis.flushdb()

#ain't nothin' to it but to do it
if __name__ == '__main__':
    api.run()
