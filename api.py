#!/usr/bin/env python3

import responder, redis, time, config, secrets, os, re
import hmac, hashlib, base64
from os import listdir
from os.path import isdir, isfile, join
from pyoauth2 import Client
from github import Github

version = '0.9.4'
api     = responder.API()
redis   = redis.StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB)

#set client ip address and
#specify headers for all requests
@api.route(before_request=True)
def prepare_headers(req, resp):
    global ip
    ip = req._starlette.client.host #standalone
    ip = req.headers['x-real-ip'] #nginx proxy
    resp.headers['x-pizza'] = 'delicious' #always

#requests for the main page
@api.route("/")
async def main(req, resp):
    resp.text = logo(ip, time.time()) + 'coming soon'

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
@api.route("/{cat}/{name}/upvote")
async def vote(req, resp, *, cat, name):
    upvotes = record_upvote(cat, name)
    if type(upvotes) == int:
        resp.text = logo(ip, time.time()) + get_answer(cat, name) + 'upvoted!'
    else:
        resp.text = logo(ip, time.time()) + get_answer(cat, name) + upvotes

#process shared oneliners
@api.route("/share")
async def share(req, resp):
#    resp.media = {"test": 123}
    return app.send_static_file('index.html')	

#github login
@api.route("/login")
async def github_login(req, resp):
    global client
    global access_token
    client = Client(secrets.KEY, secrets.SECRET,
                site=config.SITE,
                authorize_url=config.AUTHORIZE_URL,
                token_url=config.TOKEN_URL)
    authorize_url = client.auth_code.authorize_url(redirect_uri=config.CALLBACK, scope=config.SCOPE)
    r = 'Go to the following link in your browser:\n\n'
    r +=  authorize_url + '\n\n'
    resp.text = logo(ip, time.time()) + r

#github oauth2 callback
@api.route("/oauth2")
async def github_callback(req, resp):
     code   = req.params['code']
     code   = code.strip()
     client = Client(secrets.KEY, secrets.SECRET,
                site=config.SITE,
                authorize_url=config.AUTHORIZE_URL,
                token_url=config.TOKEN_URL)
     access_token = client.auth_code.get_token(code, redirect_uri=config.CALLBACK, parse='query')
     ret          = access_token.get('/user')
     session_id   = gen_session()
     cache_write('sessions:' + session_id, access_token.headers['Authorization'])
     cookie       = """<br><br><textarea>
cat > ~/.oneliner.sh.cookie.txt << EOF
oneliner.sh\tFALSE\t/\tFALSE\t0\tsession\t""" + session_id + """
EOF
</textarea><br>
---<br>
and then run:<br>
curl -b ~/.oneliner.sh.cookie.txt https://oneliner.sh/me
</textarea>
"""
     resp.text    = '<html>Welcome, ' + ret.parsed['login'] + '!<br><br>' + cookie + '</html>'

#check login
@api.route("/me")
async def me(req, resp):
    cookie    = req.headers['cookie'].split('session=').pop(1)
    token     = cache_read('sessions:' + cookie).split(' ')[1]
    g         = Github(token)
    resp.text = g.get_user().name + ' is authenticated'

#generate session
def gen_session():
    message   = bytes(ip, 'utf-8')
    secret    = bytes(secrets.SECRET, 'utf-8')
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature.decode('utf-8')

#record vote
def record_upvote(cat, name):
    with open(config.DATA_DIR + '/' + cat + '/' + name, 'r') as fin:
        data      = fin.readlines()
        votes     = data[0].split(' ')[1][1:] #strip the arrow symbolfrom col 2
        v         = int(votes) + 1
        data[0]   = '# ▲' + str(v) + ' oneliner.sh/' + cat + '/' + name + '/upvote\n'
        has_voted = cache_read('upvotes:' + ip + ':/' + cat + '/' + name)
        if has_voted is None:
            cache_write_exp('upvotes:' + ip + ':/' + cat + '/' + name, time.time(), ex=86400)
            with open(config.DATA_DIR + '/' + cat + '/' + name, 'w') as fin2:
                fin2.writelines(data)
                cache_delete(cat + '/' + name)
            return v
        else:
            return 'already upvoted'

#get request answer
def get_answer(cat, name=None):
    #get a list of all dirs/categories from data dir
    dirs = [d for d in listdir(config.DATA_DIR) if isdir(join(config.DATA_DIR, d))]
    #if category exists
    if cat in dirs:
        r1 = 'cat ' + cat + ' is in list\n'
        f1 = [f for f in listdir(config.DATA_DIR + '/' + cat) if isfile(join(config.DATA_DIR + '/' + cat, f))]
        if name in f1:
            f2 = 'name ' + name + ' is in cat ' + cat
            f3 = cache_read(cat + '/' + name)
            #if cache miss
            if f3 == None:
                #get file + write cache + return contents
                print('DEBUG: cache miss') if config.DEBUG else 0
                return read_file(cat, name) + '\n'
            else:
                #cache hit
                print('DEBUG: cache hit') if config.DEBUG else 0
                return f3 + '\n'
        else:
            #name not found in category
            #instead of returning name suggestions, return everything
            #first create a list sorted by upvotes
            ar  = ''
            lst = []
            for s in f1:
                 fc      = read_file(cat, s)
                 line1   = fc.split('\n')[0].split(' ')
                 upvotes = line1[1][1:]
                 slug    = line1[2].split('/')[2]
                 lst     += [[slug, upvotes]]
            nl = sorted(lst, key=lambda k: k[1], reverse=True)
            #build the return string in the correct order
            for n in nl:
                if cache_read(cat + '/' + n[0]) is not None:
                    ar += cache_read(cat + '/' + n[0]) + '\n'
                else:
                    ar += read_file(cat, n[0]) + '\n'
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
            c2 += colorize(line)
    #write to cache
    cache_write(cat + '/' + name, c2)
    return c2

#offer category suggestions
def suggest_cat(cat, dirs):
    cats = ', '.join(dirs)
    return cat + ' not found\n' + 'suggestions: ' + cats

#offer name suggestions for category
def suggest_names(cat, name, suggestions):
    names = ', '.join(suggestions)
    return name + ' not found in ' + cat + '\n' + 'suggestions: ' + names

#color formatting
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
        'b_dark_gray'   : '100',
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
        #custom foreground
        'c_dark_blue'   : '38;5;27',
        'c_light_blue'  : '38;5;39',
        'c_light_green' : '38;5;82',
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
    return '\033[' + c[color] + 'm' + text + '\033[0m'

#colorize results
def colorize(text):
    if re.match(r'^#', text):
        t = col(text, 'f_dark_gray')
    else:
        t = col(text, 'f_white')
    return t

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

def cache_write_exp(key, val, ex):
    redis.set(key, val, ex)

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
    info = col(col(ip, 'c_dark_blue'), 'bold') \
        + col(' in ', 'f_white') \
        + col(col(str(time_elapsed(start_time)), 'c_light_blue'), 'bold') \
        + col(' seconds ', 'f_white') \
        + col(col('v' + version, 'c_light_green'), 'bold')
    logo = """                   _                       _     
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
