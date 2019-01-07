#!/usr/bin/env python3
#oneliner.sh
#benperove@gmail.com

import responder, redis, os, re, time, config
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
    resp.text = logo(ip, time.time()) + get_answer(cat)

#requests for a category + name
@api.route("/{cat}/{name}")
async def cat_name(req, resp, *, cat, name):
    resp.text = logo(ip, time.time()) + get_answer(cat, name)

#requests for category + name with a json response
@api.route("/{cat}/{name}/json")
async def test2(req, resp, *, cat, name):
    resp.media = {"category": cat, "name": name}

#process votes for category + name
@api.route("/{cat}/{name}/vote")
async def vote(req, resp, *, cat, name):
    votes = record_vote(cat, name)
    resp.media = {"category": cat, "name": name, "votes": votes}

#record vote
def record_vote(cat, name):
    with open(config.DATA_DIR + '/' + cat + '/' + name, 'r') as fin:
        data         = fin.readlines()
        label, votes = data[0].split(': ')
        v            = int(votes) + 1
        data[0]      = label + ': ' + str(v) + "\n"
    with open(config.DATA_DIR + '/' + cat + '/' + name, 'w') as fin2:
        fin2.writelines(data)
    c2 = read_file(cat, name)
    return v

#get request answer
def get_answer(cat, name=None):
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
                return read_file(cat, name) + "\n"
            else:
                #cache hit
                print('DEBUG: cache hit') if config.DEBUG else 0
                return f3 + "\n"
        else:
            #name not found in category
            #instead of returning name suggestions, return everything
            ar = ''
            for n in f1:
                if cache_read(cat + '/' + n) is not None:
                    ar += cache_read(cat + '/' + n) + "\n"
                else:
                    ar += read_file(cat, n) + "\n"
            return ar
    #category not found
    return suggest_cat(cat, dirs)

#read file + write cache
def read_file(cat, name):
    fp       = open(config.DATA_DIR + '/' + cat + '/' + name, 'r')
    contents = fp.read()
    c2       = ''
    with open(config.DATA_DIR + '/' + cat + '/' + name, 'r') as fin:
        for line in fin:
            if re.match(r'^#', line):
                c2 += col(line, 'f_light_cyan')
            else:
                c2 += col(line, 'f_white')
    #write to cache
    cache_write(cat + '/' + name, c2)
    return c2

#offer category suggestions
def suggest_cat(cat, dirs):
    cats = ', '.join(dirs)
    return cat + " not found\n" + 'suggestions: ' + cats

#offer name suggestions for category
def suggest_names(cat, name, suggestions):
    names = ', '.join(suggestions)
    return name + " not found in " + cat + "\n" + 'suggestions: ' + names

#strip result metedata
#def strip_metadata(result):
#    return result.split("\n", 2)[2]
#     return result

#colorize text
def col(text, color=None):
    c = {
        #background
        'b_black'       : '40',
        'b_blue'        : '44',
        'b_cyan'        : '46',
        'b_green'       : '42',
        'b_light_gray'  : '47',
        'b_magenta'     : '45',
        'b_red'         : '41',
        'b_yellow'      : '43',
        #foreground
        'f_black'       : '30',
        'f_blue'        : '34',
        'f_brown'       : '33',
        'f_cyan'        : '36',
        'f_green'       : '32',
        'f_light_gray'  : '37',
        'f_normal'      : '39',
        'f_purple'      : '35',
        'f_red'         : '31',
        #compound
        'f_dark_gray'   : '1;30',
        'f_light_blue'  : '1;34',
        'f_light_cyan'  : '1;36',
        'f_light_green' : '1;32',
        'f_light_purple': '1;35',
        'f_light_red'   : '1;31',
        'f_white'       : '1;37',
        'f_yellow'      : '1;33',
        #special
        'blink'         : '5',
        'bold'          : '1',
        'dim'           : '2',
        'hidden'        : '8',
        'reset'         : '0',
        'reverse'       : '7',
        'underline'     : '4',
        #alias
        'b'             : 'bold',
        'blk'           : 'blink',
        'h'             : 'hidden',
        'rev'           : 'reverse',
        'rst'           : 'reset',
        'u'             : 'underline'
    }
    return "\033[" + c[color] + 'm' + text + "\033[0m"

#beautify results
def beautify(text):
    m = re.findall(r"^#", text)
    print(m)
#    if m:
#        return col(text, 'f_blue')
#    return text

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

def cache_delete(key):
    redis.delete(key)

#cache - flush the entire cache db
def cache_clear():
    redis.flushdb()

#calculate request time
def time_elapsed(start_time):
    return "%02.8f" % (time.time() - start_time)

#print logo
def logo(ip=None, start_time=None):
    info = col(ip, 'f_blue') + ' in ' + col(str(time_elapsed(start_time)), 'f_light_blue') + ' seconds'
    logo = """
                   _                       _      
                  | ( )                   | |     
   ___  _ __   ___| |_ _ __   ___ _ __ ___| |__   
  / _ \| '_ \ / _ \ | | '_ \ / _ \ '__/ __| '_ \  
 | (_) | | | |  __/ | | | | |  __/ |_ \__ \ | | | 
  \___/|_| |_|\___|_|_|_| |_|\___|_(_)|___/_| |_| 
   """ + info + """

"""
    return logo

#ain't nothin' to it but to do it
if __name__ == '__main__':
    api.run()
