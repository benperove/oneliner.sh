#!/usr/bin/env python3
#oneliner.sh
#benperove@gmail.com

import responder, redis, os
from os import listdir
from os.path import isdir, isfile, join

api   = responder.API()
redis = redis.StrictRedis(host='localhost', port=6379, db=0)

#specify these headers for all requests
@api.route(before_request=True)
def prepare_headers(req, resp):
    global ip
    ip, port = req.headers['host'].split(':')
    resp.headers['x-pizza'] = 'delicious'

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

#requests for a category
@api.route("/{cat}")
async def cat(req, resp, *, cat):
    resp.text = logo(ip) + get_answer(cat)

#requests for a category and name
@api.route("/{cat}/{name}")
async def cat_name(req, resp, *, cat, name):
    resp.text = logo(ip) + get_answer(cat, name)

#requests for category and name with a json response
@api.route("/{cat}/{name}/json")
async def test2(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name}

#get request answer
def get_answer(cat, name = None):
    dirs = [d for d in listdir('data') if isdir(join('data', d))]
    if cat in dirs:
        r1 = "cat " + cat + " is in list\n"
        f1 = [f for f in listdir('data/' + cat) if isfile(join('data/' + cat, f))]
        if name in f1:
            f2 = "name " + name + " is in cat " + cat
            f3 = cache_read(cat + '/' + name)
            #if nothing is found in cache
            if f3 == None:
                #read the file
                fc = open('data/' + cat + '/' + name, 'r')
                contents = fc.read()
                #write to cache
                cache_write(cat + '/' + name, contents)
                return strip_metadata(contents) + "\n"
            else:
                #cache hit
                print('cache hit')
                return strip_metadata(f3) + "\n"
        else:
            #name not found in category
            #instead of returning name suggestions, return everything
            #return suggest_names(cat, name, f1)
            ar = ''
            for n in f1:
                if cache_read(cat + '/' + n) is not None:
                    ar += strip_metadata(cache_read(cat + '/' + n)) + "\n"
                else:
                    fc = open('data/' + cat + '/' + n, 'r')
                    contents = fc.read()
                    cache_write(cat + '/' + n, contents)
                    ar += strip_metadata(contents) + "\n"
            return ar
    #category not found
    return suggest_cat(cat, dirs)

#process votes for category and name
@api.route("/{cat}/{name}/vote")
async def vote(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name, "votes": 1}

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
    r = redis.get(key)
    if r is not None:
        return r.decode('utf-8')
    else:
        return None

#cache - set value
def cache_write(key, val):
    redis.set(key, val)

#cache - flush the entire cache db
def cache_clear():
    redis.flushdb()

#ain't nothin' to it but to do it
if __name__ == '__main__':
    api.run()
