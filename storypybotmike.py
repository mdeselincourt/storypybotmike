import twitter # python-twitter library
import json
import random
import logging

logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("Loaded. This is the first test log message");


# Load twitter credentials from file
try:
	with open('SECRET/credentials.json') as credFile:
		logger.info("Loading credentials from file")
		credentials = json.loads(credFile.read())
except:
	logger.critical("Error while opening credentials. If you cloned this, you need to add your own Twitter credentials file, for location see code, for contents see https://annekjohnson.com/blog/2017/06/python-twitter-bot-on-aws-lambda/index.html");
	print("Error while opening credentials. If you cloned this you need to add your own Twitter credentials file, for location see code, for contents see https://annekjohnson.com/blog/2017/06/python-twitter-bot-on-aws-lambda/index.html");
	exit();

# Log into Twitter
# "**" expands credentials object into parameters
logger.info("Logging into Twitter")
python_twitter = twitter.Api(**credentials)

## Poem tweets search copied from Anne K Johnson
def get_poem_tweets():
	logger.info("Running poem_tweets()...")
	# - have a poetry or poem hashtag
	# - 'safe' only
	# - no links
	# - no retweets
	query = 'q=%23poetry+OR+%23poem+filter%3Asafe+-filter%3Alinks+-filter%3Aretweets'
	# - English only
	query += '&lang=en'
	# - 3 results
	query += '&count=3'
	results = python_twitter.GetSearch(raw_query=query)
	# - remove any that are reply tweets
	results = list(filter(lambda t: not t.in_reply_to_status_id, results))
	return results

def main():
	logger.info("main() running")
	inputTweets = get_poem_tweets()
	logger.info(inputTweets)
	
	
# Configure this in lambda as the handler that Lambda will invoke
def lambda_handler(_event_json, _context):
	do_tweeting()

# Detect 'standalone execution' and run main() if so
if __name__ == "__main__":
    main()