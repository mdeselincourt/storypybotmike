import logging
import twitter # python-twitter library
import json
import boto3 # Boto (a species of Amazon river dolphin!) is the AWS Python library
import urllib.request # To be able to fetch data over http if assets are online not deployed in the app
import random
import os # Helps me import files
from objdict import ObjDict # Helps me treat Python as if it's JavaScript haha
from botocore.exceptions import ClientError
import sys

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
	logger.info(" ------- main() running in " + environment + " environment -------")
	## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##
	
	# Set defaults
	okToTweet = False # If in doubt, don't tweet.
	offline = False # Assume you are online
	
	# Handle arguments

	logger.info("Arguments: " + str(sys.argv))
	
	for arg in sys.argv:
		if (arg == "--offline" or arg == "-o"):
			offline = True
			
	# S3 not in use (it's not always-free-tier)
	# s3 = boto3.resource('s3') # Boto will automatically get credentials from the filesystem (running locally) or the function's user account (lambda)	
	# s3ManuscriptOrNone = getManuscriptOrNoneFromS3(s3)
	# logger.info("s3 manu = " + str(s3ManuscriptOrNone))
	
	# Get Manuscript from dynamo (if there is one)															
	if (offline):
		dynamoManuscriptOrNone = None
	else:
		dynamodb = boto3.resource('dynamodb', region_name='us-east-1')											
		dynamoManuscriptOrNone = getManuscriptOrNoneFromDynamo(dynamodb)										
		logger.info("fetched dynamo manuscript = " + str(dynamoManuscriptOrNone))								
																											
	if dynamoManuscriptOrNone == None:																		
		# Write a new story before proceeding																
		corpora = loadCorpora()																				
																											
		narrative = buildNarrative(corpora)																	
																											
		manuscript = createManuscript(narrative, corpora)													
	else:																									
		manuscript = dynamoManuscriptOrNone																	
																											
	# Build an intended output and work out what remains
	outputAndRemainer = chooseOutputAndRemainer(manuscript)													
																											
	output = outputAndRemainer["output"]																	
	remainer = outputAndRemainer["remainer"]															
																											
	logger.info("output = " + str(output))																	
	logger.info("remainer = " + str(remainer))																
														

	# Check whether this intended output is OK to Tweet
	okToTweet = isOkToTweet(environment, output)															
	
	lastTweetId = None
	
	if not offline:
		# Tweet or set status to None
		if (okToTweet):																							
			logger.warning("Tweeting")
			tweetStatus = tweetAndGetStatus(output)
			if (tweetStatus != None):
				lastTweetId = tweetStatus["Id"]
		else:																									
			logger.info("Not invoking tweet()")
			
		# Update records
		if (len(remainer) > 0):
			logger.info("Saving remainer")
			
			newManuscript = {}
			newManuscript["previous"] = manuscript["previous"] + 1
			newManuscript["text"] = remainer
			
			saveManuscriptAndIdToDynamoDB(newManuscript, lastTweetId, dynamodb)
		else:
			logger.info("No remainer; deleting manuscript!")
			deleteManuscriptFromDynamoDB(dynamodb)
		
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
	
def buildNarrative(corpora):
		
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
	
	## BUILD BEATS
	
	beatsDB = []
	
#	b = {}
#	b["if"] = ["character a is kind", "need show-personality scene for a"] 
#	b["then"] = ["spawn or recall character b nonhostile to a", "complete act-of-kindness-template from a to b"]
#	
#	b2 = {}
#	b2["if"] = ["NEED act-of-kindness scene from x to y"]
#	b2["then"] = ["DEPICT y in need", "DEPICT x ..."	
	
	logger.info("str(narrative) = " + str(n))
	
	return n;
	
def getManuscriptOrNoneFromS3(s3):
	try:
		response = s3.Object('storypybotmike', "Manuscript.json").get()
		return json.loads(response['Body'].read().decode('utf-8'))
	except ClientError as ce:
		if ce.response['Error']['Code'] == "NoSuchKey":
			return None
		else:
			raise
	except Exception as ee:
		logger.error("Unexpected exception getting from S3: " + str(ee))
		raise
	
def getManuscriptOrNoneFromDynamo(dynamodb):
	logger.info("getManuscriptOrNoneFromDynamo() running...")
	
	try:
		table = dynamodb.Table('storypybotmike')
		
		response = table.get_item(
			Key={
				'myPartitionKey': 'Manuscript'
			}
		)
		
		try:
			#logger.info("Response['Item'] = " + str(response["Item"]))
			manuscript = json.loads(response['Item']['myJson'])
		except KeyError:
			#logger.info("Expected exception: KeyError => no stored manuscript")
			return None
		
		return manuscript
	except botocore.exceptions.EndpointExceptionError as eee:
		logger.error("EndpointExceptionError getting from dynamoDB: " + str(eee))
		return None
	except Exception as ee:
		logger.error("Unexpected exception getting from dynamoDB: " + str(ee) )
		raise

def createManuscript(narrative, corpora):
	
	logger.info("writeManuscript() running...")	
	
	## Prepare to write manuscript 
	
	p = narrative.protagonist
	m = narrative.mentor
	v = narrative.villain
	
	## Enrich characters with useful shorthands
	p.virtue = p.mainVirtueKey
	p.vice = corpora["superVirtues"][p.lackingVirtueKey]["opposite"]
	v.virtue = corpora["superVirtues"][p.mainVirtueKey]["villainy"]
	v.vice = corpora["superVirtues"][p.lackingVirtueKey]["indulgence"]	
	
	# Write the story in manuscript form i.e. broken down into sentences short enough to tweet.
	manuscript = {}
	manuscript["previous"] = 0
	manuscript["text"] = []
	
	# Act 0 
	
	manuscript["text"].append("Here's another folk story.")
	
	# Act 1
	manuscript["text"].append(p.name + " was " + aan(p.virtue) + " but " + p.vice + " " + p.identity.title() + ".")
	manuscript["text"].append("Like all the animals, " + p.name + " lived under the tyranny of " + v.name + " the " + v.virtue.capitalize() + " " + v.identity.title() + ".")
	
	# Act 2
	manuscript["text"].append("One day, " + m.name + " the " + m.identity.title() + " asked for " + p.name + "'s help to rid them of " + v.name + ".")
	manuscript["text"].append(p.name + " agreed, and together they learned that " + v.name + " was prone to being " + v.vice + "." )
	
	# Act 3
	
	if (narrative.form == "heroic"):
		manuscript["text"].append("By the time they finally met, " + p.name + " had learned to be more " + p.lackingVirtueKey + ", and played on " + v.name + "'s " + v.vice + " side.")
		manuscript["text"].append(v.name + " was vanquished, and the animals lived happily ever after.")
	elif (narrative.form == "tragic"):
		manuscript["text"].append("When they finally met, the " + v.identity + " " + v.name + " was feeling particularly " + v.virtue + ", and " + p.name + " could not help but be " + p.vice + ".")
		manuscript["text"].append(p.name + " was defeated, and " + m.name + " fled to seek a true hero. The end... or is it?")
	else:
		logger.error("No third act!")
		manusript.text.append("... the end, I guess?!")
		
	#logger.info("manuscript json is:\n" + json.dumps(manuscript))
	
	return manuscript
#

def saveManuscriptToS3(manuscript, s3):
	logger.info("saveManuscriptToS3() running...")
			
	try:
		s3.Object('storypybotmike', "Manuscript.json").put(
			Body=(bytes(json.dumps(manuscript, indent=2).encode('UTF-8')))
		)
		logger.info("Manuscript written to S3")
	except:
		logger.error("Exception while trying to write to s3 :(")
	
def saveManuscriptAndIdToDynamoDB(manuscript, lastTweetId, dynamodb):
	logger.info("saveManuscriptToDynamoDB() running...")
	
	try:
		table = dynamodb.Table('storypybotmike')
		
		response1 = table.put_item(
			Item={
				'myPartitionKey': 'Manuscript',
				'myJson': json.dumps(manuscript)
			}
		)
		
		if (lastTweetId != None):
			lastTweetId = "Dummy!"
			logger.critical("WRITING DUMMY lastTweetId!")
			
		response2 = table.put_item(
			Item={
				'myPartitionKey': 'lastTweetId',
				'myJson': json.dumps(lastTweetId)
			}
		)

	except Exception as ee:
		logger.error("Unexpected exception saving to DB " + str(ee))
		raise
		
	## ## ## ## ## ## ## ## ! ! ! ! ! ! ! !
	
def deleteManuscriptFromDynamoDB(dynamodb):
	logger.info("deleteManuscriptFromDynamoDB() running...")
	
	try:
		table = dynamodb.Table('storypybotmike')
	
		response = table.delete_item(Key={'myPartitionKey': 'Manuscript'})
	except Exception as ee:
		logger.error("Unexpected exception deleting from DB " + str(ee))
		raise

def chooseOutputAndRemainer(manuscript):
	logger.info("chooseOutput() running...")
	lenBudget = 251
	linesUnoutput = len(manuscript["text"])
	
	storySnippet = ""
	remainer = []
	
	logger.info("Composing output with " + str(linesUnoutput) + " lines remaining")
	
	for line in manuscript["text"]:
		if (len(line) == 0):
			logger.info("Skipping an empty line")
		elif (len(line) < lenBudget):
			# Add line to selection of story
			storySnippet += " " + line
			linesUnoutput += -1
		else:
			# These lines are remainer
			remainer.append(line)
		# Whichever it was, update remaining budget
		lenBudget = lenBudget - len(line)
		
	logger.info("Finishing tweet off, with " + str(linesUnoutput) + " lines remaining")
		
	output = "Bot here!" + storySnippet
	
	if (linesUnoutput > 0):
		output = output + " " + str(manuscript["previous"] + 1) + "/..."
	else:
		output = output + " " + str(manuscript["previous"] + 1) + "/" + str(manuscript["previous"] + 1)
	
	outputAndRemainer = {}
	outputAndRemainer["output"] = output
	outputAndRemainer["remainer"] = remainer
	
	return outputAndRemainer
#

def isOkToTweet(environment, output):
	
	logger.info("isOkToTweet() running...")
	
	ok = False
	
	## Prerequisites (False->True)
	
	# Turn tweeting ON if we're in the cloud
	if (environment == "Lambda Production"):
		ok = True
	else:
		logger.warning("Environment is not Lambda Production. Not activating tweeting.")
	
	## Validation (True->False)
	
	# Turn tweeting back OFF if the post is unacceptable
	logger.info(str(len(output)) + " of 280 characters")
	
	if len(output) > 280:
		ok = False
		logger.error("Intended tweet is too long, deactivating tweeting")
		
	if len(output) < 13:
		ok = False
		logger.error("Intended tweet is concerningly short, deactivating tweeting")
		
	return ok

def tweetAndGetId(output):
	logger.info("tweetAndGetStatus() running...")
	# Load twitter credentials from file into an object
	try:
		with open('SECRET/twitterCredentials.json') as twitterCredFile:
			logger.info("Loading credentials from file")
			twitterCredentials = json.loads(twitterCredFile.read())
	except:
		logger.critical("Error while opening credentials. If you cloned this, you need to add your own Twitter credentials file, for location see code, for contents see https://annekjohnson.com/blog/2017/06/python-twitter-bot-on-aws-lambda/index.html");
		exit();

	# Log into Twitter
	# "**" expands credentials object into parameters
	logger.info("Logging into Twitter")
	
	try:
		python_twitter = twitter.Api(**twitterCredentials)
		# Use the API
		status = python_twitter.PostUpdate(output)
		# Store the id tweeted
		logger.info("Tweeted; status = " + str(status))
		return status
	except Exception as ee:
		logger.error("Exception while attempting to tweet: " + str(ee))
		raise
#

def aan(s):
	if s[0] in "aeiouAEIOU":
		return ("an " + s)
	else:
		return ("a " + s)

## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## PLOTTER ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##

class Plotter:
	def generatePlot:
		plot["scenes"] = []
		plot["scenes"].append({"purpose": "introduce-protagonist"})
		plot["scenes"].append({"purpose": "inciting-incident"})
		plot["scenes"].append({"purpose": "protagonist-learns"})
		plot["scenes"].append({"purpose": "resolve-climax"})
	
	
## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## EXECUTION HOOKS ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ## ##  
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
# Here's my custom test event
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
			env = "Lambda Production"
			logger.info("event['detail-type'] == 'Scheduled Event'")
		elif (event["detail-type"]  == "Custom Test Event"):
			env = "Lambda Testing"
			logger.info("event['detail-type'] == 'Custom Test Event'")
		else:
			env = None
			logger.error("Unexpected event JSON! Not invoking main()")
	except Exception as ee:
		logger.error("Unidentified Exception whilst looking for event['detail-type']!")
		
	if (env == None):
		logger.info("Not invoking main()")
	else:
		main(env)
		
	logger.info("End of lambda execution")
#
	
# Detect 'standalone execution' and run main() if so
# logger.info("Checking for __main__ execution")
if __name__ == "__main__":
	#logger.info("__name__ is __main__")
	main("Local")
	logger.info("End of local execution")
# This has to be the last thing...

## Design Notes

# Currently we have: 
# 	Establish protagonist's characters			
# 		Describe it!
#	Incite
#		(Introduce Mentor)
# 	Climax
#		Explain victory/defeat using vices/virtues

# Epic "Show don't tell"
# 	(Micro) acts that demonstrate a character's personality so we show not tell
#		Each act might arbitrarily be alone or an interaction
# 			It might be worth introducing plotting for minor characters pretty EARLY to avoid unreadable procgen noise
# 			What about if during story gen the need for certain roles (protagonist-helper, protagonist-helpee, protagonist-negotiator) caused those characters to be spawned
# 			A mid level implementation would be narrative.cast.mentor = narrative.cast.wooee etc. 
# 			But would an Elan style database of facts be more scalable

# Use a:
#	Hash-partitioned (i.e. choose universal, mutually exclusive terms like what country you're in)
#	Semantically hierarchical (i.e. choose choose 
# 	locally sorted database
# 	optimise state->rule comparison (alphabetical)

# But I don't want to prematurely optimise!

# 	best approach would be: naive implementation that can be optimised for speed if and when it becomes necessary

# 	Naive implementation is a simple brute search.

# 	 the system's total knowledge would be a universe from which a searchable DB for the story would be instantiated at universe gen time 
#		tbc whether to serialise the DB or serialise the seeds and regen each time.

# I'd need a pretty abstract representation - Elan's was snatches of speech, successor event rules, parameters...

# Maybe I could do it in NATURAL LANGUAGE first then invent a better encoding.

