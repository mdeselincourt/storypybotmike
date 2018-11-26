import twitter # python-twitter library
import json
import logging
import boto3 # Boto (a species of Amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http if assets are online not deployed in the app
import random
import os # Helps me import files
from objdict import ObjDict # Helps me treat Python as if it's JavaScript haha
# Don't forget to install these with pip -t . so they go in the repo???

# THIS CODE DOESN'T GET INVOKED WHEN YOU ENTER VIA LAMBDA

# BEFORE ANYTHING ELSE Set up logging and ensure it's working
logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("Running global code and logging.");

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
def main(environment):
	logger.info("main() running in " + environment + " environment")

	okToTweet = False; # If in doubt, don't tweet.

	################# PERFORM LOGIC ##################
		
	#with urllib.request.urlopen("https://raw.githubusercontent.com/dariusk/corpora/master/data/humans/moods.json") as url:
	
	with open('dariusk/moods.json') as moodsCorpus:
		moodsCorpus = json.loads(moodsCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>

	with open('dariusk/firstNames.json') as firstNamesCorpus:
		firstNamesCorpus = json.loads(firstNamesCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>

	with open('dariusk/animals.common.json') as animalsCommonCorpus:
		animalsCommonCorpus = json.loads(animalsCommonCorpus.read()) # Deserialise the JSON Object into its python equivalent, a <dict>


	
	narrative = ObjDict()
	narrative.form = random.choice(["Heroic", "Tragic"])
	""" 
		Heroic form: 
			P will overcome their known flaws and thus succeed.
		Tragic form:
			P's known flaws will cause their downfall despite their known virtues.
			
		Choose the ending then set up the first act without giving it away.
	"""
	
	narrative.protagonist = ObjDict()
	narrative.protagonist.name = random.choice(firstNamesCorpus["firstNames"])
	narrative.protagonist.identity = (random.choice(animalsCommonCorpus["animals"])).capitalize()
	narrative.protagonist.startingFlawMood = random.choice(moodsCorpus["deplorableMoods"])
	narrative.protagonist.startingVirtueMood = random.choice(moodsCorpus["admirableMoods"])
	narrative.protagonist.learnedVirtueMood = random.choice(moodsCorpus["admirableMoods"])
	narrative.mentor = ObjDict()
	narrative.mentor.name = random.choice(firstNamesCorpus["firstNames"])
	narrative.mentor.identity = random.choice(animalsCommonCorpus["animals"]).capitalize()
	narrative.mentor.naturalMood = random.choice(moodsCorpus["admirableMoods"])
	
	logger.info("Narrative object:\n" + json.dumps(narrative))
	
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
	manuscript.acts[1].append(p.name + " the " + p.identity + " often felt " + p.startingVirtueMood + " but sometimes felt " + p.startingFlawMood + ".")
	
	# Act 2
	manuscript.acts.append([]) # Add act 2
	manuscript.acts[2].append("One day " + p.name + " met " + m.name + " the " + m.identity + ".")
	
	# Act 3
	manuscript.acts.append([])
	
	if (narrative.form == "Heroic"):
		manuscript.acts[3].append("They went on an adventure and " + p.name + " learned to feel more " +  p.learnedVirtueMood + ", and never felt " + p.startingFlawMood + " again.")
	elif (narrative.form == "Tragic"):
		manuscript.acts[3].append("They went on an adventure, but " + p.name + " acted really " + p.startingFlawMood + " and this led to " + p.name + "'s downfall.")
	else:
		logger.error("No third act!")
		manusript.acts[3].append("... the end I guess?")
		
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
	
	### To Tweet or not to Tweet
	
	## Prerequisites
	
	# Turn tweeting ON if we're in the cloud
	if (environment == "Lambda"):
		okToTweet = True
	else:
		logger.warning("I think I'm not running in a safe environment so I won't tweet")
	
	## Validation
	
	# Turn tweeting back OFF if the post is unacceptable
	logger.info(str(len(output)) + " of 280 characters")
	
	if len(output) > 280:
		okToTweet = False
		logger.error("Intended tweet is too long")
		
	if len(output) < 13:
		okToTweet = False
		logger.error("Intended tweet is concerningly short")
		
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
		status = python_twitter.PostUpdate(output)
		logger.info("Tweeted; status = " + str(status))
	else:
		logger.warning("Not OK to tweet");
	
# Configure this in lambda as the handler that Lambda will invoke
def lambda_handler(_event_json, _context):
	logger.info("Running lambda_handler with event \n" + str(_event_json) + "\n and context \n" + str(_context))
	main("Lambda")

def printObj(o):
	print(json.dumps(o, default=lambda o: getattr(o, '__dict__', str(o))))	
	
# Detect 'standalone execution' and run main() if so
if __name__ == "__main__":
	localRun = True
	logger.info("__name__ is __main__")
	main("Local")
# This has to be the last thing...