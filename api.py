#!/usr/bin/env python3
#oneliner.sh
#benperove@gmail.com

import responder, redis, os, config
from os import listdir
from os.path import isdir, isfile, join

api   = responder.API()
redis = redis.StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB)

#set client ip address and
#specify headers for all requests
@api.route(before_request=True)
def prepare_headers(req, resp):
    global ip
    ip, port = req.headers['host'].split(':')
    resp.headers['x-pizza'] = 'delicious'

#requests for a category
@api.route("/{cat}")
async def cat(req, resp, *, cat):
    resp.text = logo(ip) + get_answer(cat)

#requests for a category + name
@api.route("/{cat}/{name}")
async def cat_name(req, resp, *, cat, name):
    resp.text = logo(ip) + get_answer(cat, name)

#requests for category + name with a json response
@api.route("/{cat}/{name}/json")
async def test2(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name}

#process votes for category + name
@api.route("/{cat}/{name}/vote")
async def vote(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name, "votes": 1}

#get request answer
def get_answer(cat, name = None):
    #get a list of all dirs/categories from data dir
    dirs = [d for d in listdir(config.DATA_DIR) if isdir(join(config.DATA_DIR, d))]
    #if category exists
    if cat in dirs:
        r1 = "cat " + cat + " is in list\n"
        f1 = [f for f in listdir(config.DATA_DIR + '/' + cat) if isfile(join(config.DATA_DIR + '/' + cat, f))]
        if name in f1:
            f2 = "name " + name + " is in cat " + cat
            f3 = cache_read(cat + '/' + name)
            #if cache miss
            if f3 == None:
                #get file + write cache + return contents
                print('DEBUG: cache miss') if config.DEBUG else 0
                return strip_metadata(read_file(cat, name)) + "\n"
            else:
                #cache hit
                print('DEBUG: cache hit') if config.DEBUG else 0
                return strip_metadata(f3) + "\n"
        else:
            #name not found in category
            #instead of returning name suggestions, return everything
            ar = ''
            for n in f1:
                if cache_read(cat + '/' + n) is not None:
                    ar += strip_metadata(cache_read(cat + '/' + n)) + "\n"
                else:
                    ar += strip_metadata(read_file(cat, n)) + "\n"
            return ar
    #category not found
    return suggest_cat(cat, dirs)

#read file + write cache
def read_file(cat, name):
    fp       = open(config.DATA_DIR + '/' + cat + '/' + name, 'r')
    contents = fp.read()
    #write to cache
    cache_write(cat + '/' + name, contents)
    return contents

#offer category suggestions
def suggest_cat(cat, dirs):
    cats = ', '.join(dirs)
    return cat + " not found\n" + 'suggestions: ' + cats

#offer name suggestions for category
def suggest_names(cat, name, suggestions):
    names = ', '.join(suggestions)
    return name + " not found in " + cat + "\n" + 'suggestions: ' + names

#strip result metedata
def strip_metadata(result):
    return result.split("\n", 2)[2]

#update result metadata

#colorize results

#cache - get value
def cache_read(key):
    v = redis.get(key)
    if v is not None:
        return v.decode('utf-8')
    else:
        return None

#cache - set value
def cache_write(key, val):
    redis.set(key, val)

#cache - flush the entire cache db
def cache_clear():
    redis.flushdb()

#oneliner.sh logo
def logo(ip = None):
    logo = """
                   _                       _
                  | (@benperove           | |
   ___  _ __   ___| |_ _ __   ___ _ __ ___| |__
  / _ \| '_ \ / _ \ | | '_ \ / _ \ '__/ __| '_ \
 | (_) | | | |  __/ | | | | |  __/ |_ \__ \ | | |
  \___/|_| |_|\___|_|_|_| |_|\___|_(_)|___/_| |_|
   """ + ip + """

"""
    return logo

#ain't nothin' to it but to do it
if __name__ == '__main__':
    api.run()
