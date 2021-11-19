from environs import Env

env = Env()
env.read_env()

REDIS_DB = env.int('REDIS_DB', 1)
REDIS_HOST = env.str('REDIS_HOST', 'localhost')
REDIS_PORT = env.int('REDIS_HOST', 6379)
REDIS_KEY = env.str('REDIS_KEY', 'deadlink2')
FILEPATH = env.str('FILEPATH', '../profiles/')
PROXY_API = env.str('PROXY_API', '')
SEM = env.int('SEM', 200)
MAX_RETRY_TIME = env.int('MAX_RETRY_TIME', 2)
TIMEOUT = env.int('TIMEOUT', 60)
MAX_WORKER = env.int('MAX_WORKER', 8)
