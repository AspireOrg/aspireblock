from lib import config, util
from datetime import datetime
import sqlite3
import logging
import decimal

D = decimal.Decimal

class Betting:

    def __init__(self, mongo_db):
        self.db = mongo_db

    def parse_broadcast(self, message):
        logging.info('Parsing broadcast message..')
        logging.info(message)

        save = False
        feed = self.db.feeds.find_one({"source": message['source']})
        
        if util.is_valid_url(message['text'], suffix='.json') and message['value'] == -1.0:
            if feed is None: feed = {}
            feed['source'] = message['source']
            feed['info_url'] = message['text']
            feed['info_status'] = 'needfetch' #needfetch, valid (included in CW feed directory), invalid, error 
            feed['fetch_info_retry'] = 0 # retry 3 times to fetch info from info_url
            feed['info_data'] = {}
            feed['fee_fraction_int'] = message['fee_fraction_int']
            feed['locked'] = False
            feed['last_broadcast'] = {}
            save = True
        elif feed is not None:
            if message['locked']:
                feed['locked'] = True
            else:
                feed['last_broadcast'] = {
                    "text": message['text'],
                    "value": message['value']
                }
                feed['fee_fraction_int'] = message['fee_fraction_int']
            save = True

        if save:  
            logging.debug('Save feed: '+feed['info_url'])   
            self.db.feeds.save(feed)
            return True
        return False

    def inc_fetch_retry(self, feed, max_retry = 3, new_status = 'error', errors=[]):
        feed['fetch_info_retry'] += 1
        feed['errors'] = errors
        if feed['fetch_info_retry'] == max_retry:
            feed['info_status'] = new_status
        self.db.feeds.save(feed)

    def sanitize_json_data(self, data):
        # TODO: make this in more elegant way
        data['operator']['name'] = util.sanitize_eliteness(data['operator']['name'])
        if 'description' in data['operator']: data['operator']['description'] = util.sanitize_eliteness(data['operator']['description'])
        data['title'] = util.sanitize_eliteness(data['title'])
        if 'description' in data: data['description'] = util.sanitize_eliteness(data['description'])
        for i in range(len(data["targets"])):
            data["targets"][i]['text'] = util.sanitize_eliteness(data["targets"][i]['text'])
            if 'description' in data["targets"][i]: data["targets"][i]['description'] = util.sanitize_eliteness(data["targets"][i]['description'])
            if 'labels' in data["targets"][i]:
                data["targets"][i]['labels']['equal'] = util.sanitize_eliteness(data["targets"][i]['labels']['equal'])
                data["targets"][i]['labels']['not_equal'] = util.sanitize_eliteness(data["targets"][i]['labels']['not_equal'])
        if 'customs' in data:
            for key in data['customs']:
                if isinstance(data['customs'][key], str): data['customs'][key] = util.sanitize_eliteness(data['customs'][key])
        return data

    def fetch_feed_info(self, feed):
        # sanity check
        if feed['info_status'] != 'needfetch': return False
        if 'info_url' not in feed: return False
        if not util.is_valid_url(feed['info_url'], suffix='.json'): return False

        logging.info('Fetching feed informations: '+feed['info_url'])

        data = util.fetch_json(feed['info_url'])
        if not data: 
            logging.info('Fetching error: '+feed['info_url'])
            self.inc_fetch_retry(feed, errors=['Fetch json failed'])
            return False

        errors = util.is_valid_json(data, config.FEED_SCHEMA)

        if feed['source'] != data['address']:
            errors.append("Invalid address")
       
        if len(errors)>0:
            logging.info('Invalid json: '+feed['info_url'])
            self.inc_fetch_retry(feed, new_status = 'invalid', errors=errors) 
            return False        

        feed['info_status'] = 'valid'

        if 'image' in data['operator']:
            data['operator']['valid_image'] = util.fetch_image(data['operator']['image'], config.SUBDIR_FEED_IMAGES, feed['source']+'_owner')
        
        if 'image' in data:
            data['valid_image'] = util.fetch_image(data['image'], config.SUBDIR_FEED_IMAGES, feed['source']+'_topic')

        for i in range(len(data["targets"])):
            if 'image' in data["targets"][i]:
                image_name = feed['source']+'_tv_'+str(data["targets"][i]['value'])
                data["targets"][i]['valid_image'] = util.fetch_image(data["targets"][i]['image'], config.SUBDIR_FEED_IMAGES, image_name)

        feed['info_data'] = self.sanitize_json_data(data)

        logging.info('Save feed:')
        logging.info(feed)

        self.db.feeds.save(feed)

    def fetch_all_feed_info(self):
        feeds = self.db.feeds.find({'info_status': 'needfetch'})
        for feed in feeds:
            self.fetch_feed_info(feed)

    # TODO: counter cache
    def get_feed_counters(self, feed_address):
        counters = {}        
        sql  = "SELECT COUNT(*) AS bet_count, SUM(wager_quantity) AS wager_quantity, SUM(wager_remaining) AS wager_remaining, status FROM bets "
        sql += "WHERE feed_address=? GROUP BY status ORDER BY status DESC"
        bindings = (feed_address,)        
        counters['bets'] = util.counterpartyd_query(sql, bindings)
        return counters;

    def find_feed(self, url_or_address):
        conditions = {
            '$or': [{'source': url_or_address}, {'info_url': url_or_address}],
            'info_status': 'valid'
        }
        result = {}
        feeds = self.db.feeds.find(spec=conditions, fields={'_id': False}, imit=1)
        for feed in feeds:
            result = feed;
            result['counters'] = self.get_feed_counters(feed['source'])

        return result

    def find_bets(self, bet_type, feed_address, deadline, target_value=1, leverage=5040, limit=50):         
        sql  = "SELECT * FROM bets WHERE counterwager_remaining>0 AND "
        sql += "bet_type=? AND feed_address=? AND target_value=? AND leverage=? AND deadline=? "
        sql += "ORDER BY ((counterwager_quantity+0.0)/(wager_quantity+0.0)) ASC LIMIT ?";
        bindings = (bet_type, feed_address, target_value, leverage, deadline, limit)        
        return util.counterpartyd_query(sql, bindings);

    def get_feeds_by_source(self, addresses):
        conditions = { 'source': { '$in': addresses }}
        feeds = self.db.feeds.find(spec=conditions, fields={'_id': False})
        feeds_by_source = {}
        for feed in feeds: feeds_by_source[feed['source']] = feed
        return feeds_by_source

    def find_user_bets(self, addresses, status='open'):
        logging.error(addresses)
        ins = []

        sql  = "SELECT * FROM bets WHERE status = ? AND source IN ("+",".join(['?' for e in range(0,len(addresses))])+") ";
        sql += "ORDER BY tx_index DESC LIMIT 100"
        bindings = (status,) + tuple(addresses)
        bets = util.counterpartyd_query(sql, bindings);

        sources = {}
        for bet in bets: sources[bet['feed_address']] = True;
        
        return {
            'bets': bets,
            'feeds': self.get_feeds_by_source(sources.keys())
        }
        
        
