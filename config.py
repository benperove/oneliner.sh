import os
#github login
SITE          = 'https://api.github.com'
CALLBACK      = 'https://oneliner.sh/oauth2'
AUTHORIZE_URL = 'https://github.com/login/oauth/authorize'
TOKEN_URL     = 'https://github.com/login/oauth/access_token'
SCOPE         = 'user,public_repo'
#redis config
REDIS_HOST = os.environ['REDIS_HOST']
#REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB   = 0
DATA_DIR   = 'oneliners'
DEBUG      = True
#app
SUBMISSION_PATH = 'incoming'
