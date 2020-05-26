# -*- coding: utf-8 -*-

##
# CONSTANTS
##
VERSION = "1.4.0"  # should keep up with aspireblockd repo's release tag

DB_VERSION = 24  # a db version increment will cause aspireblockd to rebuild its database off of aspired

UNIT = 100000000

MARKET_PRICE_DERIVE_NUM_POINTS = 8  # number of last trades over which to derive the market price (via WVAP)

# FROM aspired
# NOTE: These constants must match those in aspired/lib/py
REGULAR_DUST_SIZE = 5430
MULTISIG_DUST_SIZE = 5430 * 2
ORDER_BTC_DUST_LIMIT_CUTOFF = MULTISIG_DUST_SIZE

BTC = 'GASP'
XCP = 'ASP'

BTC_NAME = "AspireGas"
XCP_NAME = "Aspire"
APP_NAME = "aspireblock"
ASPIRE_APP_NAME = XCP_NAME.lower()

MAX_REORG_NUM_BLOCKS = 10  # max reorg we'd likely ever see
MAX_FORCED_REORG_NUM_BLOCKS = 20  # but let us go deeper when messages are out of sync

QUOTE_ASSETS = ['GASP', 'XGASP', 'ASP']  # define the priority for quote asset
MARKET_LIST_QUOTE_ASSETS = ['ASP', 'XGASP', 'GASP']  # define the order in the market list

DEFAULT_BACKEND_PORT_TESTNET = 18332
DEFAULT_BACKEND_PORT = 8332

DEFAULT_LOG_SIZE_KB = 20000
DEFAULT_LOG_NUM_FILES = 5

##
# STATE
##
mongo_db = None  # will be set on server init
state = {
    'caught_up': False  # atomic state variable, set to True when aspired AND aspireblockd are caught up
    # the rest of this is added dynamically
}


##
# METHODS
##
def get_dirs():
    import appdirs
    data_dir = appdirs.user_data_dir(appauthor=XCP_NAME, appname=APP_NAME, roaming=True)
    config_dir = appdirs.user_config_dir(appauthor=XCP_NAME, appname=APP_NAME, roaming=True)
    log_dir = appdirs.user_log_dir(appauthor=XCP_NAME, appname=APP_NAME)
    return data_dir, config_dir, log_dir


def init_base(args):
    import os
    import configparser
    import email.utils

    # testnet
    global TESTNET
    if args.testnet:
        TESTNET = args.testnet
    else:
        TESTNET = False

    global net_path_part
    net_path_part = '.testnet' if TESTNET else ''

    # first block
    global BLOCK_FIRST
    BLOCK_FIRST = 0

    global LATEST_BLOCK_INIT
    LATEST_BLOCK_INIT = {'block_index': BLOCK_FIRST, 'block_time': None, 'block_hash': None}

    # init variables used for reparse operations
    global IS_REPARSING
    IS_REPARSING = False
    global QUIT_AFTER_CAUGHT_UP
    QUIT_AFTER_CAUGHT_UP = False

    ##############
    # THINGS WE CONNECT TO

    # backend (e.g. gaspd)
    global BACKEND_CONNECT
    if args.backend_connect:
        BACKEND_CONNECT = args.backend_connect
    else:
        BACKEND_CONNECT = 'localhost'

    global BACKEND_PORT
    if args.backend_port:
        BACKEND_PORT = args.backend_port
    else:
        BACKEND_PORT = DEFAULT_BACKEND_PORT_TESTNET if TESTNET else DEFAULT_BACKEND_PORT
    try:
        BACKEND_PORT = int(BACKEND_PORT)
        assert int(BACKEND_PORT) > 1 and int(BACKEND_PORT) < 65535
    except:
        raise Exception("Please specify a valid port number for the backend-port configuration parameter")

    global BACKEND_USER
    if args.backend_user:
        BACKEND_USER = args.backend_user
    else:
        BACKEND_USER = 'rpc'

    global BACKEND_PASSWORD
    if args.backend_password:
        BACKEND_PASSWORD = args.backend_password
    else:
        BACKEND_PASSWORD = 'rpcpassword'

    global BACKEND_AUTH
    BACKEND_AUTH = (BACKEND_USER, BACKEND_PASSWORD) if (BACKEND_USER and BACKEND_PASSWORD) else None

    global BACKEND_URL
    BACKEND_URL = 'http://' + BACKEND_USER + ':' + BACKEND_PASSWORD + '@' + BACKEND_CONNECT + ':' + str(BACKEND_PORT)

    global BACKEND_URL_NOAUTH
    BACKEND_URL_NOAUTH = 'http://' + BACKEND_CONNECT + ':' + str(BACKEND_PORT) + '/'

    # aspired RPC connection
    global ASPIRE_CONNECT
    if args.aspire_connect:
        ASPIRE_CONNECT = args.aspire_connect
    else:
        ASPIRE_CONNECT = 'localhost'

    global ASPIRE_PORT
    if args.aspire_port:
        ASPIRE_PORT = args.aspire_port
    else:
        ASPIRE_PORT = 14000 if TESTNET else 4000
    try:
        ASPIRE_PORT = int(ASPIRE_PORT)
        assert int(ASPIRE_PORT) > 1 and int(ASPIRE_PORT) < 65535
    except:
        raise Exception("Please specify a valid port number for the aspire-port configuration parameter")

    global ASPIRE_USER
    if args.aspire_user:
        ASPIRE_USER = args.aspire_user
    else:
        ASPIRE_USER = 'rpc'

    global ASPIRE_PASSWORD
    if args.aspire_password:
        ASPIRE_PASSWORD = args.aspire_password
    else:
        ASPIRE_PASSWORD = 'rpcpassword'

    global ASPIRE_RPC
    ASPIRE_RPC = 'http://' + ASPIRE_CONNECT + ':' + str(ASPIRE_PORT) + '/api/'

    global ASPIRE_AUTH
    ASPIRE_AUTH = (ASPIRE_USER, ASPIRE_PASSWORD) if (ASPIRE_USER and ASPIRE_PASSWORD) else None

    # mongodb
    global MONGODB_CONNECT
    if args.mongodb_connect:
        MONGODB_CONNECT = args.mongodb_connect
    else:
        MONGODB_CONNECT = 'localhost'

    global MONGODB_PORT
    if args.mongodb_port:
        MONGODB_PORT = args.mongodb_port
    else:
        MONGODB_PORT = 27017
    try:
        MONGODB_PORT = int(MONGODB_PORT)
        assert int(MONGODB_PORT) > 1 and int(MONGODB_PORT) < 65535
    except:
        raise Exception("Please specify a valid port number for the mongodb-port configuration parameter")

    global MONGODB_DATABASE
    if args.mongodb_database:
        MONGODB_DATABASE = args.mongodb_database
    else:
        MONGODB_DATABASE = 'aspireblockd_testnet' if TESTNET else 'aspireblockd'

    global MONGODB_USER
    if args.mongodb_user:
        MONGODB_USER = args.mongodb_user
    else:
        MONGODB_USER = None

    global MONGODB_PASSWORD
    if args.mongodb_password:
        MONGODB_PASSWORD = args.mongodb_password
    else:
        MONGODB_PASSWORD = None

    # redis-related
    global REDIS_CONNECT
    if args.redis_connect:
        REDIS_CONNECT = args.redis_connect
    else:
        REDIS_CONNECT = '127.0.0.1'

    global REDIS_PORT
    if args.redis_port:
        REDIS_PORT = args.redis_port
    else:
        REDIS_PORT = 6379
    try:
        REDIS_PORT = int(REDIS_PORT)
        assert int(REDIS_PORT) > 1 and int(REDIS_PORT) < 65535
    except:
        raise Exception("Please specify a valid port number for the redis-port configuration parameter")

    global REDIS_DATABASE
    if args.redis_database:
        REDIS_DATABASE = args.redis_database
    else:
        REDIS_DATABASE = 1 if TESTNET else 0
    try:
        REDIS_DATABASE = int(REDIS_DATABASE)
        assert int(REDIS_DATABASE) >= 0 and int(REDIS_DATABASE) <= 16
    except:
        raise Exception("Please specify a valid redis-database configuration parameter (between 0 and 16 inclusive)")

    ##############
    # THINGS WE SERVE

    global RPC_HOST
    if args.rpc_host:
        RPC_HOST = args.rpc_host
    else:
        RPC_HOST = 'localhost'

    global RPC_PORT
    if args.rpc_port:
        RPC_PORT = args.rpc_port
    else:
        RPC_PORT = 14100 if TESTNET else 4100
    try:
        RPC_PORT = int(RPC_PORT)
        assert int(RPC_PORT) > 1 and int(RPC_PORT) < 65535
    except:
        raise Exception("Please specify a valid port number for the rpc-port configuration parameter")

    global RPC_ALLOW_CORS
    if args.rpc_allow_cors:
        RPC_ALLOW_CORS = args.rpc_allow_cors
    else:
        RPC_ALLOW_CORS = True

    # Other things
    global SUBDIR_ASSET_IMAGES
    SUBDIR_ASSET_IMAGES = "asset_img%s" % net_path_part  # goes under the data dir and stores retrieved asset images
    global SUBDIR_FEED_IMAGES
    SUBDIR_FEED_IMAGES = "feed_img%s" % net_path_part  # goes under the data dir and stores retrieved feed images

    ##############
    # OTHER SETTINGS

    # System (logging, pids, etc)
    global ASPIREBLOCKD_DIR
    ASPIREBLOCKD_DIR = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

    global LOG
    if args.log_file is False:  # no file logging
        LOG = None
    elif not args.log_file:  # default location
        LOG = os.path.join(log_dir, 'server%s.log' % net_path_part)
    else:  # user-specified location
        LOG = args.log_file

    global LOG_SIZE_KB
    if args.log_size_kb:
        LOG_SIZE_KB = args.log_size_kb
    else:
        LOG_SIZE_KB = DEFAULT_LOG_SIZE_KB
    try:
        LOG_SIZE_KB = int(LOG_SIZE_KB)
        assert LOG_SIZE_KB > 0
    except:
        raise Exception("Please specify a valid log-size-kb value (in kilobytes)")

    global LOG_NUM_FILES
    if args.log_num_files:
        LOG_NUM_FILES = args.log_num_files
    else:
        LOG_NUM_FILES = DEFAULT_LOG_NUM_FILES
    try:
        LOG_NUM_FILES = int(LOG_NUM_FILES)
        assert LOG_NUM_FILES > 0 and LOG_NUM_FILES <= 100
    except:
        raise Exception("Please specify a valid log-num-files value (must be less than 100)")

    global TX_LOG
    if args.tx_log_file is False:  # no file logging
        TX_LOG = None
    elif not args.tx_log_file:  # default location
        TX_LOG = os.path.join(log_dir, 'server%s.tx.log' % net_path_part)
    else:  # user-specified location
        TX_LOG = args.tx_log_file

    global PID
    if args.pid_file:
        PID = args.pid_file
    else:
        PID = os.path.join(data_dir, 'server%s.pid' % net_path_part)


def load_schemas():
    """initialize json schema for json asset and feed validation"""
    import os
    import json
    assert ASPIREBLOCKD_DIR

    global ASSET_SCHEMA
    ASSET_SCHEMA = json.load(open(os.path.join(ASPIREBLOCKD_DIR, 'schemas', 'asset.schema.json')))

    global FEED_SCHEMA
    FEED_SCHEMA = json.load(open(os.path.join(ASPIREBLOCKD_DIR, 'schemas', 'feed.schema.json')))


def init(args):
    #set up dirs
    global data_dir, config_dir, log_dir
    data_dir, config_dir, log_dir = get_dirs()
    assert data_dir and config_dir and log_dir

    init_base(args)
    load_schemas()
