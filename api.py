#!/usr/bin/env python3
"""
oneliner.sh
"""
import responder, redis, time, config, secrets, os, re
import hmac, hashlib, base64, random, string
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
    page = """<html><style>body{background-color: #ABB8C3;}</style><img style="max-width:100%; max-height:100%; height:auto;" src="https://www.dropbox.com/s/ppf98l1hke2etad/carbon.png?raw=1" /></html>"""
    elem = {'title': 'the title', 'result': '123'}
    if is_cli(req):
        resp.text = logo(ip, time.time()) + 'coming soon'
    else:
        #resp.content = api.template('terminal.html', data=elem)
        resp.text = page

#requests for a category
@api.route("/{cat}")
async def cat(req, resp, *, cat):
    resp.text = logo(ip, time.time()) + get_answer(cat)

#requests for a category + command
@api.route("/{cat}/{cmd}")
async def cat_name(req, resp, *, cat, cmd):
    resp.text = logo(ip, time.time()) + get_answer(cat, cmd)

#requests for category + command with a json response
@api.route("/{cat}/{cmd}/json")
async def test2(req, resp, *, cat, cmd):
    resp.media = {"category": cat, "command": cmd}

#process votes for category + command
@api.route("/{cat}/{cmd}/upvote")
async def vote(req, resp, *, cat, cmd):
    upvotes = record_upvote(cat, cmd)
    if type(upvotes) == int:
        resp.text = logo(ip, time.time()) + get_answer(cat, cmd) + 'upvoted!'
    else:
        resp.text = logo(ip, time.time()) + get_answer(cat, cmd) + upvotes

#process shared oneliners
@api.route("/{cat}/{cmd}/add")
async def share(req, resp, *, cat, cmd):
    ls = is_loggedin(req)
    if ls is True:
        #resp.text = 'is logged in'
        user     = await me(req, resp)
        userid   = user.login
        oneliner = await req._starlette.body()
        oneliner = oneliner.decode('utf-8')
        if process_post_request(cat, cmd, oneliner, userid):
            resp.text = cat + '/' + cmd + ' added to the queue by ' + userid
        else:
            resp.text = 'error'
    else:
        resp.text = ls

def is_cli(req):
    if 'user-agent' in req.headers:
        if re.match(r'curl', req.headers['user-agent']):
            return True
        return False
    return True

def process_post_request(cat, cmd, oneliner, userid):
    header = """
# ▲0 oneliner.sh/""" + cat + '/' + cmd + '/upvote'"""
# purpose:
# usage: as is
# variables: 
# contributor: """ + userid + """
# """ + ('-' * 30) + '\n'
    h_oneliner = header + oneliner
    print(h_oneliner)
    if save_oneliner(cat, cmd, h_oneliner):
        return True
    else:
        return False

def save_oneliner(cat, cmd, oneliner):
    nonce = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(9))
    fn       = cat + '/' + cmd
    filename = fn.replace('/', '.') + '.' + nonce
    filename = os.path.join(config.SUBMISSION_PATH, filename)
    if open(filename, 'w').write(oneliner):
        return True
    else:
        return False
    
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
     cookie       = '<br>run this to save a cookie & verify your login:<br><textarea style="margin: 0px; width: 569px; height: 90px;">echo "oneliner.sh FALSE / FALSE 0 session ' + session_id + '" | sed -e "s/\\s/\\t/g" > ~/.oneliner.sh.cookie.txt && curl -L -b ~/.oneliner.sh.cookie.txt oneliner.sh/me</textarea><br>'
     resp.text    = '<html>Welcome, ' + ret.parsed['login'] + '!<br><br>' + cookie + '</html>'

#check login
@api.route("/me")
async def me(req, resp):
    cookie = req.headers['cookie'].split('session=').pop(1)
    token  = cache_read('sessions:' + cookie).split(' ')[1]
    g      = Github(token)
    #return g.get_user()
    resp.text = g.get_user().name + ' is authenticated'
    return g.get_user()

def is_loggedin(req):
    if 'cookie' in req.headers:
        cookie = req.headers['cookie'].split('session=').pop(1)
        if cookie is not None:
            if cache_read('sessions:' + cookie) is not None:
                token = cache_read('sessions:' + cookie).split(' ')[1]
                if token is not None:
                    g = Github(token)
                    if g:
                        print('is_loggedin(): true')
                        return True
                    else:
                        print('is_loggedin(): login error from github api')
                        return 'login error from github api'
                else:
                    print('is_loggedin(): token not found in cache')
                    return 'token not found in cache'
            else:
                print('is_loggedin(): no session found in cache')
                return 'no session found in cache'
        else:
            print('is_loggedin(): cookie format is wrong')
            return 'cookie format is wrong'
    else:
        print('is_loggedin(): no cookie sent')
        return 'no cookie sent'

#generate session
def gen_session():
    message   = bytes(ip, 'utf-8')
    secret    = bytes(secrets.SECRET, 'utf-8')
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature.decode('utf-8')

#record vote
def record_upvote(cat, cmd):
    with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r') as fin:
        data      = fin.readlines()
        votes     = data[0].split(' ')[1][1:] #strip the arrow symbolfrom col 2
        v         = int(votes) + 1
        data[0]   = '# ▲' + str(v) + ' oneliner.sh/' + cat + '/' + cmd + '/upvote\n'
        has_voted = cache_read('upvotes:' + ip + ':/' + cat + '/' + cmd)
        if has_voted is None:
            cache_write_exp('upvotes:' + ip + ':/' + cat + '/' + cmd, time.time(), ex=86400)
            with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'w') as fin2:
                fin2.writelines(data)
                cache_delete(cat + '/' + cmd)
            return v
        else:
            return 'already upvoted'

#get request answer
def get_answer(cat, cmd=None):
    #get a list of all dirs/categories from data dir
    dirs = [d for d in listdir(config.DATA_DIR) if isdir(join(config.DATA_DIR, d))]
    #if category exists
    if cat in dirs:
        r1 = 'cat ' + cat + ' is in list\n'
        f1 = [f for f in listdir(config.DATA_DIR + '/' + cat) if isfile(join(config.DATA_DIR + '/' + cat, f))]
        if cmd in f1:
            f2 = 'cmd ' + cmd + ' is in cat ' + cat
            f3 = cache_read(cat + '/' + cmd)
            #if cache miss
            if f3 == None:
                #get file + write cache + return contents
                print('DEBUG: cache miss') if config.DEBUG else 0
                return read_file(cat, cmd) + '\n'
            else:
                #cache hit
                print('DEBUG: cache hit') if config.DEBUG else 0
                return f3 + '\n'
        else:
            #command not found in category
            #instead of returning command suggestions, return everything
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
def read_file(cat, cmd):
    fp       = open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r')
    contents = fp.read()
    c2       = ''
    with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r') as fin:
        for line in fin:
            c2 += colorize(line)
    #write to cache
    cache_write(cat + '/' + cmd, c2)
    return c2

#offer category suggestions
def suggest_cat(cat, dirs):
    cats = ', '.join(dirs)
    return cat + ' not found\n' + 'suggestions: ' + cats

#offer name suggestions for category
def suggest_names(cat, cmd, suggestions):
    cmds = ', '.join(suggestions)
    return cmd + ' not found in ' + cat + '\n' + 'suggestions: ' + cmds

#color formatting
def col(text, color=None):
    """asdasd"""
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
    logo = r"""                   _                       _     
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
