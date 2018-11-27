import twitter # python-twitter library
import json
import logging
import boto3 # Boto (a species of Amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http if assets are online not deployed in the app
import random
import os # Helps me import files
from objdict import ObjDict # Helps me treat Python as if it's JavaScript haha
# from nltk import CFG # Representation of a context-free-grammar for code-light text generation
# from nltk.parse.generate import generate # For generation of text from a context-free-grammar

# Don't forget to install these with pip -t . so they go in the repo???

# THIS CODE DOESN'T GET INVOKED WHEN YOU ENTER VIA LAMBDA

# BEFORE ANYTHING ELSE Set up logging and ensure it's working
logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("Running global code. Logging is loaded.");

## Poem tweets search copied from Anne K Johnson
def get_poem_tweets():
	logger.info("Running get_poem_tweets()...")
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

	corpora = loadCorpora()
	
	narrative = buildNarrative(corpora)
	
	#testCFG()
	
	manuscript = writeManuscript(narrative)
	
	output = chooseOutput(manuscript)
		
	logger.info(output)
	
	### To Tweet or not to Tweet
	
	## Prerequisites
	
	# Turn tweeting ON if we're in the cloud
	if (environment == "Lambda Production"):
		okToTweet = True
	else:
		logger.warning("Environment is not Lambda Production. Not activating tweeting.")
	
	## Validation
	
	# Turn tweeting back OFF if the post is unacceptable
	logger.info(str(len(output)) + " of 280 characters")
	
	if len(output) > 280:
		okToTweet = False
		logger.error("Intended tweet is too long, deactivating tweeting")
		
	if len(output) < 13:
		okToTweet = False
		logger.error("Intended tweet is concerningly short, deactivating tweeting")
		
	################# ACT ON TWITTER #################

	if (okToTweet):
		tweet(output)
	else:
		logger.warning("Skipping tweeting step");
	#
#
	
## Load Corpora ##
def loadCorpora():
	logger.info("loadCorpora() running...")
	loadedCorpora = {}
	
	with open('dariusk/moods.json') as moodsCorpus:
		moodsCorpusObject = json.loads(moodsCorpus.read()) # Can't json.loads more than once it seems?
		loadedCorpora["moods"] = moodsCorpusObject["moods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		loadedCorpora["admirableMoods"] = moodsCorpusObject["admirableMoods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		loadedCorpora["deplorableMoods"] = moodsCorpusObject["deplorableMoods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>

	with open('dariusk/firstNames.json') as firstNamesCorpus:
		loadedCorpora["firstNames"] = json.loads(firstNamesCorpus.read())["firstNames"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>

	with open('dariusk/animals.common.json') as animalsCommonCorpus:
		loadedCorpora["animals"] = json.loads(animalsCommonCorpus.read())["animals"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		
	return loadedCorpora
#
	
## Build Narrative ##
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
def buildNarrative(corpora):
	logger.info("buildNarrative() running...")
	newNarrative = ObjDict()
	newNarrative.form = random.choice(["Heroic", "Tragic"])
	newNarrative.protagonist = ObjDict()
	newNarrative.protagonist.name = random.choice(corpora["firstNames"])
	newNarrative.protagonist.identity = (random.choice(corpora["animals"])).capitalize()
	newNarrative.protagonist.startingFlawMood = random.choice(corpora["deplorableMoods"])
	newNarrative.protagonist.startingVirtueMood = random.choice(corpora["admirableMoods"])
	newNarrative.protagonist.learnedVirtueMood = random.choice(corpora["admirableMoods"])
	newNarrative.mentor = ObjDict()
	newNarrative.mentor.name = random.choice(corpora["firstNames"])
	newNarrative.mentor.identity = random.choice(corpora["animals"]).capitalize()
	newNarrative.mentor.naturalMood = random.choice(corpora["admirableMoods"])
	#logger.info("Narrative object to json:\n" + json.dumps(newNarrative))
	return newNarrative;
#
	
def writeManuscript(narrative):
	logger.info("writeManuscript() running...")
	p = narrative.protagonist
	m = narrative.mentor
	
	# Write the story in manuscript form i.e. broken down into sentences short enough to tweet.
	manuscript = ObjDict()
	manuscript.acts = []

	# Act 0 
	manuscript.acts.append(["Here's a folk story."])
	
	# Act 1
	manuscript.acts.append([]) # Add act 1
	manuscript.acts[1].append(p.name + " the " + p.identity + " often felt " + p.startingVirtueMood + ", but sometimes felt " + p.startingFlawMood + ".")
	
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
		manusript.acts[3].append("... the end, I guess?")
		
	#logger.info("manuscript json is:\n" + json.dumps(manuscript))
	
	return manuscript
#
	
def chooseOutput(manuscript):
	logger.info("chooseOutput() running...")
	lenBudget = 266
	
	storySnippet = ""
	
	for act in manuscript.acts:
		for line in act:
			if (len(line) == 0):
				logger.info("Skipping an empty line") # On assumption that we will empty tweeted lines and store what's left
				pass
			elif (len(line) < lenBudget):
				storySnippet += " " + line
				line = ""
			else:
				break; break;
		
	output = "Bot here!" + storySnippet
	
	return output
#

def tweet(output):
	logger.info("tweet() running...")
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
#
	
# Configure this in lambda as the handler that Lambda will invoke
def lambda_handler(event, _context):
	logger.info("Running lambda_handler() with event \n" + str(event) + "\n and context \n" + str(_context))
	
	logger.info("json.dumps(event) = " + json.dumps(event))
	
	try:
		if (event["testing"] == "True"):
			logger.info("Invoking main('Lambda Testing')")
			main("Lambda Testing")
		else:
			logger.warn("Testing is findable but not what we expected")
	except:
		try:
			if (event["detail-type"] == "Scheduled Event"):
				logger.warn("Lambda event is as expected, invoking main('Lambda Production')")
				main("Lambda Production")
		except:
			logger.error("Exception while looking for event['detail-type']")
		
		
	logger.info("End of lambda execution")
#

# Shorthand for turning a Python Object to JSON
def printObj(o):
	print(json.dumps(o, default=lambda o: getattr(o, '__dict__', str(o))))	
#
	
def testCFG():
	logger.error("I haven't imported NLTK because it's big")
	grammar = CFG.fromstring("""S -> NP VP
    NP -> Det N
    PP -> P NP
    VP -> 'slept'
    VP -> 'saw' NP
    VP -> 'walked' PP
    Det -> 'the'
    Det -> 'a'
    N -> 'man'
    N -> 'park'
    N -> 'dog'
    P -> 'in'
    P -> 'with'""")
	
	sentences = generate(grammar, n=2)
		
	logger.warn("Here are some sample CFG-generated sentences")
	
	for sentence in sentences:
		logger.info(">" + str(sentence))
#
	
# Detect 'standalone execution' and run main() if so
logger.info("Checking for __main__ execution")
if __name__ == "__main__":
	logger.info("__name__ is __main__")
	
	event = json.loads('{"testing": "True"}')
	
	logger.info("event: " + json.dumps(event))
	
	if (event["testing"] == "True"):
		logger.info("event['testing'] is True")
	else:
		logger.info("event['testing'] is not True")
		
	localRun = True
	main("Local")
	logger.info("End of local execution")
# This has to be the last thing...