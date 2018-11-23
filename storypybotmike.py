import twitter # python-twitter library
import json
import logging
import boto3 # Boto (an amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http
import random
import os # Helps me import files

okToTweet = False # If in doubt, don't tweet!

# Set up logging and ensure it's working
logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("Running and logging.");

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

# Intended for either of two entry points - last line or lambda_handler()
def main():
	logger.info("main() running")

	################# PERFORM LOGIC ##################
		
	#with urllib.request.urlopen("https://raw.githubusercontent.com/dariusk/corpora/master/data/humans/moods.json") as url:
	
	with open('dariusk/moods.json') as moodsCorpus:
		moodsCorpus = json.loads(moodsCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>

	with open('dariusk/firstNames.json') as firstNamesCorpus:
		firstNamesCorpus = json.loads(firstNamesCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>

	with open('dariusk/animals.common.json') as animalsCommonCorpus:
		animalsCommonCorpus = json.loads(animalsCommonCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>

	class Story:
		pass
		
	class Protagonist:
		pass
		
	story = Story()
	story.protagonist = Protagonist()
	story.protagonist.name = random.choice(firstNamesCorpus["firstNames"])
	story.protagonist.identity = (random.choice(animalsCommonCorpus["animals"])).capitalize()
	story.protagonist.startingNaturalMood = random.choice(moodsCorpus["moods"])
	story.protagonist.endingNaturalMood = random.choice(moodsCorpus["moods"])
	
	p = story.protagonist
	
	output = logger.info("Here's a folk story. " + p.name + " the " + p.identity + " usually felt " + p.startingNaturalMood + ". But after an adventure, " + p.name + " felt " + p.endingNaturalMood + " most days.")
		
	################# ACT ON TWITTER #################
		
	if (okToTweet):
		# Load twitter credentials from file into an object
		try:
			with open('SECRET/credentials.json') as credFile:
				logger.info("Loading credentials from file")
				credentials = json.loads(credFile.read())
		except:
			logger.critical("Error while opening credentials. If you cloned this, you need to add your own Twitter credentials file, for location see code, for contents see https://annekjohnson.com/blog/2017/06/python-twitter-bot-on-aws-lambda/index.html");
			exit();

		# Log into Twitter
		# "**" expands credentials object into parameters
		logger.info("Logging into Twitter")
		python_twitter = twitter.Api(**credentials)
		# Use the API
		inputTweets = get_poem_tweets()
		logger.info(inputTweets)
		status = python_twitter.PostUpdate('My bot says: ' + output)
		logger.info("Tweeted; status = " + str(status))
	else:
		logger.info("Not OK to tweet");
	
# Configure this in lambda as the handler that Lambda will invoke
def lambda_handler(_event_json, _context):
	logger.info(str(_event_json));
	logger.info(str(_context));
	main()

def printObj(o):
	print(json.dumps(o, default=lambda o: getattr(o, '__dict__', str(o))))	
	
# Detect 'standalone execution' and run main() if so
if __name__ == "__main__":
    main()
# This has to be the last thing...