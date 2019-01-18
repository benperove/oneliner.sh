#!/usr/bin/env python3
'''
oneliner.sh: be a cli samurai
'''
import os
import re
import time
import hmac
import hashlib
import base64
import random
import string
import responder
import redis
import config
import secrets
from os import listdir
from os.path import isdir, isfile, join
from pyoauth2 import Client
from github import Github

version = '0.9.5'
api     = responder.API()
redis   = redis.StrictRedis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB)

@api.route(before_request=True)
def prepare_headers(req, resp):
    '''set client ip address and'''
    '''specify headers for all requests'''
    global ip
    ip = req._starlette.client.host #standalone
    ip = req.headers['x-real-ip'] #nginx proxy
    resp.headers['x-pizza'] = 'delicious' #always

@api.route("/")
async def main(req, resp):
    '''requests for the main page'''
    page = """<html><style>body{background-color: #ABB8C3;}</style><img style="max-width:100%; max-height:100%; height:auto;" src="https://www.dropbox.com/s/ppf98l1hke2etad/carbon.png?raw=1" /></html>"""
    elem = {'title': 'the title', 'result': '123'}
    if is_cli(req):
        resp.text = banner(ip, time.time()) + 'coming soon'
    else:
        #resp.content = api.template('terminal.html', data=elem)
        resp.text = page

@api.route("/{cat}")
async def cat(req, resp, *, cat):
    '''requests for a category'''
    resp.text = banner(ip, time.time()) + get_answer(cat)

@api.route("/{cat}/{cmd}")
async def cat_name(req, resp, *, cat, cmd):
    '''requests for a category + command'''
    resp.text = banner(ip, time.time()) + get_answer(cat, cmd)

@api.route("/{cat}/{cmd}/json")
async def test2(req, resp, *, cat, cmd):
    '''requests for category + command with a json response'''
    resp.media = {"category": cat, "command": cmd}

@api.route("/{cat}/{cmd}/upvote")
async def vote(req, resp, *, cat, cmd):
    '''process votes for category + command'''
    @api.background.task
    def vote(cat, cmd):
        upvotes = record_upvote(cat, cmd)
        if type(upvotes) == int:
            resp.text = banner(ip, time.time()) + get_answer(cat, cmd) + 'upvoted!'
        else:
            resp.text = banner(ip, time.time()) + get_answer(cat, cmd) + upvotes

    vote(cat, cmd)
    resp.content = 'processing upvote...'

@api.route("/{cat}/{cmd}/add")
async def share(req, resp, *, cat, cmd):
    '''process shared oneliners'''
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
    '''determine if plaintext client in use'''
    if 'user-agent' in req.headers:
        cli_clients = ['curl', 'wget', 'fetch', 'httpie', 'lwp-request', 'openbsd ftp', 'python-requests']
        for client in cli_clients:
            if re.match(client, req.headers['user-agent']):
                return True
        return False
    return False

def process_post_request(cat, cmd, oneliner, userid):
    '''process incoming command additions'''
    header = """# ▲0 oneliner.sh/""" + cat + '/' + cmd + '/upvote'"""
# purpose:
# usage: as is
# variables: 
# contributor: """ + userid + """
# """ + ('-'*30) + '\n'
    oneliner = header + oneliner
    if save_oneliner(cat, cmd, oneliner):
        os.system('bin/collaborator.sh ' + userid)
        return True
    else:
        return False

def save_oneliner(cat, cmd, oneliner):
    '''write the command to a temp file'''
    nonce    = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(9))
    cmd_path = cat + '/' + cmd
    filename = cmd_path.replace('/', '.') + '.' + nonce
    filename = os.path.join(config.SUBMISSION_PATH, filename)
    if open(filename, 'w').write(oneliner):
        return True
    else:
        return False
    
@api.route("/login")
async def github_login(req, resp):
    '''github login'''
    global client
    global access_token
    client = Client(secrets.KEY,
                    secrets.SECRET,
                    site=config.SITE,
                    authorize_url=config.AUTHORIZE_URL,
                    token_url=config.TOKEN_URL)
    authorize_url = client.auth_code.authorize_url(redirect_uri=config.CALLBACK, scope=config.SCOPE)
    response = 'Go to the following link in your browser:\n\n'
    response +=  authorize_url + '\n\n'
    resp.text = banner(ip, time.time()) + response

@api.route("/oauth2")
async def github_callback(req, resp):
    '''github oauth2 callback'''
    code   = req.params['code']
    code   = code.strip()
    client = Client(secrets.KEY,
                    secrets.SECRET,
                    site=config.SITE,
                    authorize_url=config.AUTHORIZE_URL,
                    token_url=config.TOKEN_URL)
    access_token = client.auth_code.get_token(code, redirect_uri=config.CALLBACK, parse='query')
    data         = access_token.get('/user')
    session_id   = gen_session()
    cache_write('sessions:' + session_id, access_token.headers['Authorization'])
    cookie       = '<br>run this to save a cookie & verify your login:<br><textarea style="margin: 0px; width: 569px; height: 90px;">echo "oneliner.sh FALSE / FALSE 0 session ' + session_id + '" | sed -e "s/\\s/\\t/g" > ~/.oneliner.sh.cookie.txt && curl -L -b ~/.oneliner.sh.cookie.txt oneliner.sh/me</textarea><br>'
    resp.text    = '<html>Welcome, ' + data.parsed['login'] + '!<br><br>' + cookie + '</html>'


@api.route("/me")
async def me(req, resp):
    '''check login'''
    cookie    = req.headers['cookie'].split('session=').pop(1)
    token     = cache_read('sessions:' + cookie).split(' ')[1]
    gc        = Github(token)
    resp.text = gc.get_user().name + ' is authenticated'
    return gc.get_user()

def is_loggedin(req):
    '''determine if logged in'''
    if 'cookie' in req.headers:
        cookie = req.headers['cookie'].split('session=').pop(1)
        if cookie is not None:
            if cache_read('sessions:' + cookie) is not None:
                token = cache_read('sessions:' + cookie).split(' ')[1]
                if token is not None:
                    gc = Github(token)
                    if gc:
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

def gen_session():
    '''generate session'''
    message   = bytes(ip, 'utf-8')
    secret    = bytes(secrets.SECRET, 'utf-8')
    signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
    return signature.decode('utf-8')

def record_upvote(cat, cmd):
    '''record vote'''
    with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r') as filename:
        data      = filename.readlines()
        votes     = data[0].split(' ')[1][1:] #strip the arrow symbol from col 2
        votes     = int(votes) + 1
        data[0]   = '# ▲' + str(votes) + ' oneliner.sh/' + cat + '/' + cmd + '/upvote\n'
        has_voted = cache_read('upvotes:' + ip + ':/' + cat + '/' + cmd)
        if has_voted is None:
            cache_write_exp('upvotes:' + ip + ':/' + cat + '/' + cmd, time.time(), ex=86400)
            with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'w') as filename2:
                filename2.writelines(data)
                cache_delete(cat + '/' + cmd)
            return votes
        else:
            return 'already upvoted'

def get_answer(cat, cmd=None):
    '''get request answer'''
    #get a list of all dirs/categories from data dir
    dirs = [d for d in listdir(config.DATA_DIR) if isdir(join(config.DATA_DIR, d))]
    #if category exists
    if cat in dirs:
        cmd_list = [f for f in listdir(config.DATA_DIR + '/' + cat) if isfile(join(config.DATA_DIR + '/' + cat, f))]
        if cmd in cmd_list:
            cache = cache_read(cat + '/' + cmd)
            #if cache miss
            if cache == None:
                #get file + write cache + return contents
                print('DEBUG: cache miss') if config.DEBUG else 0
                return read_file(cat, cmd) + '\n'
            else:
                #cache hit
                print('DEBUG: cache hit') if config.DEBUG else 0
                return cache + '\n'
        else:
            #command not found in category
            #instead of returning command suggestions, return everything
            #first create a list sorted by upvotes
            result   = ''
            tmp_list = []
            for cmd in cmd_list:
                contents = read_file(cat, cmd)
                #parse first header line
                line1    = contents.split('\n')[0].split(' ')
                upvotes  = line1[1][1:]
                vote_url = line1[2].split('/')[2]
                tmp_list += [[vote_url, upvotes]]
            sorted_list = sorted(tmp_list, key=lambda k: k[1], reverse=True)
            #build the result string sorted by upvotes descending
            for cmd in sorted_list:
                if cache_read(cat + '/' + cmd[0]) is not None:
                    result += cache_read(cat + '/' + cmd[0]) + '\n'
                else:
                    result += read_file(cat, cmd[0]) + '\n'
            return result
    #category not found
    return suggest_cat(cat, dirs)

def read_file(cat, cmd):
    '''read file + write cache'''
    filename = open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r')
    contents = filename.read()
    result   = ''
    with open(config.DATA_DIR + '/' + cat + '/' + cmd, 'r') as file:
        for line in file:
            result += colorize(line)
    #write to cache
    cache_write(cat + '/' + cmd, result)
    return result

def suggest_cat(cat, dirs):
    '''offer category suggestions'''
    cats = ', '.join(dirs)
    return cat + ' not found\n' + 'suggestions: ' + cats

def suggest_cmd(cat, cmd, suggestions):
    '''offer name suggestions for category'''
    '''not presently in use'''
    cmds = ', '.join(suggestions)
    return cmd + ' not found in ' + cat + '\n' + 'suggestions: ' + cmds

def col(text, color=None):
    '''apply color formatting'''
    color_dict = {
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
    return '\033[' + color_dict[color] + 'm' + text + '\033[0m'

def colorize(text):
    '''colorize results'''
    if re.match(r'^#', text):
        colorized = col(text, 'f_dark_gray')
    else:
        colorized = col(text, 'f_white')
    return colorized

def cache_read(key):
    '''cache - get value'''
    val = redis.get(key)
    if val is not None:
        return val.decode('utf-8')
    else:
        return None

def cache_write(key, val):
    '''cache - set value'''
    redis.set(key, val)

def cache_write_exp(key, val, ex):
    '''cache - set value with expiration'''
    redis.set(key, val, ex)

def cache_delete(key):
    '''cache - delete key'''
    redis.delete(key)

def cache_clear():
    '''cache - flush the entire cache db'''
    redis.flushdb()

def time_elapsed(start_time):
    '''calculate request time'''
    return "%02.8f" % (time.time() - start_time)

def banner(ip=None, start_time=None):
    '''print banner'''
    info = col(col(ip, 'c_dark_blue'), 'bold') + \
            col(' in ', 'f_white') + \
            col(col(str(time_elapsed(start_time)), 'c_light_blue'), 'bold') + \
            col(' seconds ', 'f_white') + \
            col(col('v' + version, 'c_light_green'), 'bold')
    banner = r"""                   _                       _     
                  | ( )                   | |    
   ___  _ __   ___| |_ _ __   ___ _ __ ___| |__  
  / _ \| '_ \ / _ \ | | '_ \ / _ \ '__/ __| '_ \ 
 | (_) | | | |  __/ | | | | |  __/ |_ \__ \ | | |
  \___/|_| |_|\___|_|_|_| |_|\___|_(_)|___/_| |_|
   """ + info + """

"""
    return banner

if __name__ == '__main__':
    '''ain't nothin' to it but to do it'''
    api.run()
