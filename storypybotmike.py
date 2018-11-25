import twitter # python-twitter library
import json
import logging
import boto3 # Boto (a species of Amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http if assets are online not deployed in the app
import random
import os # Helps me import files
from objdict import ObjDict # Helps me treat Python as if it's JavaScript haha
# Don't forget to install these with pip -t . so they go in the repo???

localRun = True # If in doubt, you are not deployed
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

	class Entity:
		pass
	
	narrative = Entity()
	narrative.protagonist = Entity()
	narrative.protagonist.name = random.choice(firstNamesCorpus["firstNames"])
	narrative.protagonist.identity = (random.choice(animalsCommonCorpus["animals"])).capitalize()
	narrative.protagonist.startingNaturalMood = random.choice(moodsCorpus["deplorableMoods"])
	narrative.protagonist.endingNaturalMood = random.choice(moodsCorpus["admirableMoods"])
	narrative.mentor = Entity()
	narrative.mentor.name = random.choice(firstNamesCorpus["firstNames"])
	narrative.mentor.identity = random.choice(animalsCommonCorpus["animals"]).capitalize()
	narrative.mentor.naturalMood = random.choice(moodsCorpus["admirableMoods"])
	
	"""
	{
		"Virtues": {
			"Cardinal": ["Prudence", "Courage", "Temperance", "Justice"],
			"HEXACO": ["Honesty", "Emotionality", "Openness to experience", "Conscientiousness", "Extraversion", "Agreeableness", "Un-neuroticism"]
			"Theological": ["Faith", "Hope", "Charity"],
			"Leadership": ["Focus", "Grit"]
		}
	}
	"""
	
	p = narrative.protagonist
	m = narrative.mentor
	
	# Write the story in manuscript form i.e. broken down into sentences short enough to tweet.
	manuscript = ObjDict()
	manuscript.acts = []

	# Act 0 
	manuscript.acts.append(["Here's a folk story."])
	
	# Act 1
	manuscript.acts.append([]) # Add act 1
	manuscript.acts[1].append(p.name + " the " + p.identity + " usually felt " + p.startingNaturalMood + ".")
	
	# Act 2
	manuscript.acts.append([]) # Add act 2
	manuscript.acts[2].append("But one day " + p.name + " met " + m.name + " the " + m.identity + ".")
	
	# Act 3
	manuscript.acts.append([])
	manuscript.acts[3].append("They went on an adventure, after which " + p.name + " felt " + p.endingNaturalMood + " most days.")
		
	logger.info("manuscriptJson is\n" + json.dumps(manuscript))
		
	lenBudget = 266
	
	storySnippet = ""
	
	for act in manuscript.acts:
		for line in act:
			if (len(line) == 0):
				logger.info("Skipping an empty line")
				pass
			elif (len(line) < lenBudget):
				storySnippet += " " + line
				line = ""
			else:
				break; break;
		
	output = "My bot says: " + storySnippet
	
	logger.info(output)
	
	logger.info(str(len(output)) + " of 280 characters")
	
	if len(output) > 280:
		okToTweet = False
		logger.error("Intended tweet is too long")
		
	if len(output) < 13:
		okToTweet = False
		logger.error("Intended tweet is concerningly short")
		
	################# ACT ON TWITTER #################
		
	if (localRun): 
		okToTweet = False;
		logger.warn("localRun is " + str(localRun))
		logger.warn("I think I'm running locally so should not tweet")
		
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
		status = python_twitter.PostUpdate(output)
		logger.info("Tweeted; status = " + str(status))
	else:
		logger.warning("Not OK to tweet");
	
# Configure this in lambda as the handler that Lambda will invoke
def lambda_handler(_event_json, _context):
	logger.info(str(_event_json));
	logger.info(str(_context));
	localRun = False
	main()

def printObj(o):
	print(json.dumps(o, default=lambda o: getattr(o, '__dict__', str(o))))	
	
# Detect 'standalone execution' and run main() if so
if __name__ == "__main__":
	localRun = True
	logger.info("__name__ is __main__")
	main()
# This has to be the last thing...