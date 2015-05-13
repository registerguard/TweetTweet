# Included in Python
import logging, logging.handlers, urllib2, socket

# Need to pip install these
import feedparser, tweepy, bitly_api

# --- LOGGING ---
log_file_dir = '/Users/USER/PATH/TO/TWEET/logs/'
logger = logging.getLogger(__name__)
# Set logging level
logger.setLevel(logging.DEBUG)
# Set formatting
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# Keep log files tidy, max file size of 256K and have five back files (tweet.log.1)
fileLogger = logging.handlers.RotatingFileHandler(filename=( log_file_dir + 'tweet.log'), maxBytes=256*1024, backupCount=5) # 256 x 1024 = 256K
fileLogger.setFormatter(formatter)
logger.addHandler(fileLogger)
# Uncomment below to print to console while developing
# Not commenting this out will result in Terminal Mail when on cron
#handler = logging.RotatingFileHandler()
#handler.setFormatter(formatter)
#logger.addHandler(handler)

# Start each new log with this line
logger.debug('------------------------')

# --- URLLIB2 ---
# Get your RSS feed, example: http://registerguard.com/csp/cms/sites/rg/feeds/rss.csp?pub=rg&section=local&area=Updates
url = 'RSS_URL'

try:
    # Try to get url, if it takes longer than 30 then time out
    response = urllib2.urlopen(url, timeout=30)
except urllib2.URLError, e:
    # First possible error is from urllib2, see: http://heyman.info/2010/apr/22/python-urllib2-timeout-issue/
    logger.debug('urllib2 timed out on: ' + url)
except socket.timeout:
    # Second possible error is from socket
    logger.debug('socket timed out on: ' + url)

# Open and read data
response = urllib2.urlopen(url)
html = response.read()

# --- FEEDPARSER ---
feed = feedparser.parse(html)
#if the rss feed has items
if feed.entries:
    #initiate new list, this will be populate with unique story IDs
    id_list = []

    #populate list of ids
    for entry in feed.entries:
        id_list.append(entry.id)

    #read past list of ids
    with open('/Users/USER/PATH/TO/FILE/tweet.txt', 'r') as f:
        file_data = f.read()

    # Print out this stuff for testing purposes
    #logger.debug(id_list)
    #logger.debug type(id_list)
    #logger.debug(file_data)

    #set loop var to count which id the loop is on
    loop = 0

    # loop over items in list
    for single_id in id_list:

        #logger.debug('single_id: ' + single_id)

        # if item in list is not in data
        if single_id not in file_data:
            #logger.debug('not in read data: ' + single_id)

            # set these vars
            feed_title = feed.entries[loop].title
            feed_url = feed.entries[loop].link

            # --- TWEEPY ---
            # Credentials available at https://apps.twitter.com
            # Tweepy docs: http://tweepy.readthedocs.org/en/v3.3.0/getting_started.html
            auth = tweepy.OAuthHandler('CONSUMER_KEY', 'CONSUMER_SECRET')
            auth.set_access_token('ACCESS_TOKEN', 'ACCESS_TOKEN_SECRET')
            api = tweepy.API(auth)

            # --- BITLY_API ---
            # Credentials available at https://bitly.com/a/create_oauth_app
            # Bitly_api docs: http://dev.bitly.com/get_started.html
            access_token='ACCESS_TOKEN'
            bitly = bitly_api.Connection(access_token=access_token)
            try:
                # See: http://dev.bitly.com/links.html#v3_shorten
                bitlyurl = bitly.shorten(feed_url)
                shorturl = str(bitlyurl[u'url'])
                #logger.debug('short url')
            except bitly_api.bitly_api.BitlyError, err:
                # If there is an error, then fall back to the long URL that is provided from RSS, will still work
                shorturl = feed_url
                logger.debug(err)

            # construct string to tweet
            # Example: This is a test headline http://rgne.ws/1E5UQmr
            tweet_text = feed_title + ' ' + shorturl
            #logger.debug (tweet_text)

            try:
                # Send the tweet
                # Comment out the following line if you don't want to tweet during dev
                api.update_status(status=tweet_text)
                logger.debug('Success! Tweet sent: ' + tweet_text)
            except tweepy.TweepError, err:
                logger.debug(str(err.message[0]['message']) + ' ' + str(err.message[0]['code']))

        # if item is already in the file then don't do anything
        else:
            logger.debug(single_id + ' is in the file.')

        # add to loop as you loop through tweet.txt
        loop = loop + 1
        #logger.debug(loop)

    # overwrite the file with the new ids
    with open('/Users/rdenton/Desktop/tweet.txt', 'w') as text_file:
        text_file.write('{}'.format(id_list))

#else if the feed does not have items then don't do anything
else:

    logger.debug('No entries')

# end of script
