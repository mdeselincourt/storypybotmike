import logging
import twitter # python-twitter library
import json
import boto3 # Boto (a species of Amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http if assets are online not deployed in the app
import random
import os # Helps me import files
from objdict import ObjDict # Helps me treat Python as if it's JavaScript haha

# Don't forget to install these with pip -t . so they go in the repo and can be deployed to AWS

# FIRST Set up logging
logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)
logger.info("Global logging code is running.");

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
	
	manuscript = writeManuscript(narrative, corpora)
	
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
	
	with open('corpora/moods.json') as moodsCorpus:
		moodsCorpusObject = json.loads(moodsCorpus.read()) # Can't json.loads more than once it seems?
		loadedCorpora["moods"] = moodsCorpusObject["moods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		loadedCorpora["admirableMoods"] = moodsCorpusObject["admirableMoods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		loadedCorpora["deplorableMoods"] = moodsCorpusObject["deplorableMoods"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>

	with open('corpora/dariusk.firstNames.json') as firstNamesCorpus:
		loadedCorpora["firstNames"] = json.loads(firstNamesCorpus.read())["firstNames"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>

	with open('corpora/dariusk.animals.common.json') as animalsCommonCorpus:
		loadedCorpora["animals"] = json.loads(animalsCommonCorpus.read())["animals"] # Deserialise the JSON Object's main body into its python equivalent, a <dict>
		
	with open('corpora/superVirtues.json') as superVirtuesCorpus:
		loadedCorpora["superVirtues"] = json.loads(superVirtuesCorpus.read()) # Deserialise the JSON Object's main body into its python equivalent, a <dict>

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
	
	#superVirtues = ["active", "confident", "kind", "positive", "wise"]
	#superVices = ["selfish", "cowardly", "passive", "despairing", "hysterical"]
	#heroisms = ["self-sacrificial", "brave", "tireless", "undespairing", "unflappable"]
	#villainies = ["seductive", "fearless", "relentless", "fanatical", "calculating"]
	#indulgences	= ["greedy", "cowardly", "slothful", "bi-polar", "irrational"]
		
	logger.info("buildNarrative() running...")
	n = ObjDict() # Narrative
	p = ObjDict() #  Protagonist
	v = ObjDict() #  Villain (not antagoist)
	
	n.form = random.choice(["heroic", "tragic"])
	
	## Protagonist

	p.name = random.choice(corpora["firstNames"])
	p.identity = (random.choice(corpora["animals"])).title() # Capitalise each word
	
	SVs = corpora["superVirtues"]

	# Assign protagonist's main virtue and vice
	pvids = random.sample(range(5), 2)
	p.mainVirtueKey = list(SVs.keys())[pvids[0]]
	p.lackingVirtueKey = list(SVs.keys())[pvids[1]]
	
	## Villain
	
	v.name = random.choice(corpora["firstNames"])
	v.identity = (random.choice(corpora["animals"]))

	# Assign protagonist's main virtue and vice
	vvids = random.sample(range(5), 2)
	v.mainVirtueKey = list(SVs.keys())[vvids[0]]
	v.lackingVirtueKey = list(SVs.keys())[vvids[1]]
	
	# Mentor
	m = ObjDict()
	m.name = random.choice(corpora["firstNames"])
	m.identity = random.choice(corpora["animals"])
	
	n.protagonist = p
	n.villain = v
	n.mentor = m
	
	logger.info("str(narrative) = " + str(n))
	
	return n;
#
	
def writeManuscript(narrative, corpora):
	logger.info("writeManuscript() running...")
	p = narrative.protagonist
	m = narrative.mentor
	v = narrative.villain
	
	## Enrich characters with useful shorthands
	p.virtue = p.mainVirtueKey
	p.vice = corpora["superVirtues"][p.lackingVirtueKey]["opposite"]
	v.virtue = corpora["superVirtues"][p.mainVirtueKey]["villainy"]
	v.vice = corpora["superVirtues"][p.lackingVirtueKey]["indulgence"]	
	
	# Write the story in manuscript form i.e. broken down into sentences short enough to tweet.
	manuscript = ObjDict()
	manuscript.acts = []

	# Act 0 
	manuscript.acts.append(["Here's another folk story."])
	
	# Act 1
	manuscript.acts.append([]) # Add act 1
	manuscript.acts[1].append(p.name + " was " + aan(p.virtue) + " but " + p.vice + " " + p.identity.title() + ".")
	manuscript.acts[1].append("Like all the animals, " + p.name + " lived under the tyranny of " + v.name + " the " + v.virtue.capitalize() + " " + v.identity.title() + ".")
	
	# Act 2
	manuscript.acts.append([]) # Add act 2
	manuscript.acts[2].append("One day, " + m.name + " the " + m.identity.title() + " asked for " + p.name + "'s help to rid them of " + v.name + ".")
	manuscript.acts[2].append(p.name + " agreed, and together they learned that " + v.name + " was prone to being " + v.vice + "." )
	
	# Act 3
	manuscript.acts.append([])
	
	if (narrative.form == "heroic"):
		manuscript.acts[3].append("By the time they finally met, " + p.name + " had learned to be more " + p.lackingVirtueKey + ", and played on " + v.name + "'s " + v.vice + " side.")
		manuscript.acts[3].append(v.name + " was vanquished, and the animals lived happily ever after.")
	elif (narrative.form == "tragic"):
		manuscript.acts[3].append("When they finally met, the " + v.identity + " " + v.name + " was feeling particularly " + v.virtue + ", and " + p.name + " could not help but be " + p.vice + ".")
		manuscript.acts[3].append(p.name + " was defeated, and " + m.name + " fled to seek a true hero. The end... or is it?")
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

def aan(s):
	if s[0] in "aeiouAEIOU":
		return ("an " + s)
	else:
		return ("a " + s)

	
# Configure this in lambda as the handler that Lambda will invoke
## Here's an example production event
"""
{
    "version": "0",
    "id": "a97774b7-252a-4905-8970-ce7d09ab32e1",
    "detail-type": "Scheduled Event",
    "source": "aws.events",
    "account": "533996033834",
    "time": "2018-11-27T10:07:56Z",
    "region": "us-east-1",
    "resources": [
        "arn:aws:events:us-east-1:533996033834:rule/pybotSPAM"
    ],
    "detail": {}
}
"""
# Here's my new test event
"""
{
  "version": "0",
  "detail-type": "Custom Test Event",
  "account": "533996033834",
  "region": "us-east-1",
  "detail": {}
}
"""

def lambda_handler(event, _context):
	logger.info("Running lambda_handler()")
	
	try:
		logger.info("event = " + event)
	except:
		logger.info("Event isn't natively loggable")
		
	logger.info("str(event) = " + str(event))		
	
	logger.info("json.dumps(event) = " + json.dumps(event))
	
	try:
		if (event["detail-type"] == "Scheduled Event"):
			logger.info("event['detail-type'] == 'Scheduled Event'; Invoking main('Lambda Production')")
			main("Lambda Production")
		elif (event["detail-type"]  == "Custom Test Event"):
			logger.info("event['detail-type'] == 'Custom Test Event'; Invoking main('Lambda Testing')")
			main("Lambda Testing")
		else:
			logger.error("Unexpected event JSON! Not invoking main()")
	except Exception:
		logger.error("str(Exception) " + str(Exception) + "whilst looking for event['detail-type']! Not invoking main()")
	except:
		logger.error("Unidentified Exception whilst looking for event['detail-type']! Not invoking main()")
		
	logger.info("End of lambda execution")
#
	
# Detect 'standalone execution' and run main() if so
logger.info("Checking for __main__ execution")
if __name__ == "__main__":
	logger.info("__name__ is __main__")
	main("Local")
	logger.info("End of local execution")
# This has to be the last thing...