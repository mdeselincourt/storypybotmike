from nltk import CFG # Representation of a context-free-grammar for code-light text generation
from nltk.parse.generate import generate # For generation of text from a context-free-grammar
import logging
import random
from collections import defaultdict # I think I need this for bendersky's CFG (for defaultdict)

# BEFORE ANYTHING ELSE Set up logging and ensure it's working
logger = logging.getLogger()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger.setLevel(logging.INFO)


def main():
	
	#grammar = CFG.fromstring("""S -> NP VP
	#NP -> Det N
	#PP -> P NP
	#VP -> 'slept'
	#VP -> 'saw' NP
	#VP -> 'walked' PP
	#Det -> 'the'
	#Det -> 'a'
	#N -> 'man'
	#N -> 'park'
	#N -> 'dog'
	#P -> 'in'
	#P -> 'with'""")
	#
	#sentences = generate(grammar, n=2)
	#	
	#logger.warn("Here are some naively CFG-generated sentences")
	#
	#for sentence in sentences:
	#	logger.info(">" + str(sentence))

	p = {}
	p["name"] = "Derpbert"
	
	aGrammar = [
		["$S", "$NP $VP"],
		["$NP", "$Det N | $Det N"],
		["$NP", "I | he | she | Joe"],
		["$VP", "$V $NP | $VP"],
		["$Det", "a | the | my | his"],
		["$N", "elephant | cat | jeans | suit"],
		["$V", "kicked | followed | shot"]
	]
	
	myGrammar = [
		["$root", "$A1 $A2 $A3"],
		
		["$A1", "$pIntroduction"],
		["$A2", "$pStory"],
		["$A3", "$climax"],
		
		["$pIntroduction", "One day there was #pName." ],
		["$pStory", "#pName went on an adventure." ],
		["$pIntroduction", "#pName learned to be more #pVirtue." ],
	]
	
	cfg1 = benderskyCFG()
	
	for rule in myGrammar:
			cfg1.add_prod(*rule)

	for i in range(10):
		logger.info(cfg1.gen_random('$root')) # Call the root 
	

# by Eli Bendersky
class benderskyCFG(object):
	def __init__(self):
		self.prod = defaultdict(list)

	def add_prod(self, lhs, rhs):
		""" Add production to the grammar. 'rhs' can
			be several productions separated by '|'.
			Each production is a sequence of symbols
			separated by whitespace.

			Usage:
				grammar.add_prod('NT', 'VP PP')
				grammar.add_prod('Digit', '1|2|3|4')
		"""
		prods = rhs.split('|')
		for prod in prods:
			self.prod[lhs].append(tuple(prod.split()))

	def gen_random(self, symbol):
		""" Generate a random sentence from the
			grammar, starting with the given
			symbol.
		"""
		sentence = ''

		# select one production of this symbol randomly
		rand_prod = random.choice(self.prod[symbol])

		for sym in rand_prod:
			# for non-terminals, recurse
			if sym in self.prod:
				sentence += self.gen_random(sym)
			else:
				sentence += sym + ' '

		return sentence
		
	def gen_random_convergent(self,	symbol,	cfactor=0.25, pcount=defaultdict(int)):
	
		# Generate a random sentence from the
		#	grammar, starting with the given symbol.
		#
		#		Uses a convergent algorithm - productions
		#		that have already appeared in the
		#		derivation on each branch have a smaller
		#		chance to be selected.	
		#
		#		cfactor - controls how tight the
		#		convergence is. 0 < cfactor < 1.0
		#
		#		pcount is used internally by the
		#		recursive calls to pass on the
		#		productions that have been used in the
		#		branch.

		sentence = ''

		# The possible productions of this symbol are weighted
		# by their appearance in the branch that has led to this
		# symbol in the derivation
		#
		weights = []
		for prod in self.prod[symbol]:
			if prod in pcount:
				weights.append(cfactor ** (pcount[prod]))
			else:
				weights.append(1.0)

		rand_prod = self.prod[symbol][weighted_choice(weights)]

		# pcount is a single object (created in the first call to
		# this method) that's being passed around into recursive
		# calls to count how many times productions have been
		# used.
		# Before recursive calls the count is updated, and after
		#the sentence for this call is ready, it is rolled-back
		#to avoid modifying the parent's pcount.
		
		pcount[rand_prod] += 1

		for sym in rand_prod:
			# for non-terminals, recurse
			if sym in self.prod:
				sentence += self.gen_random_convergent(sym, cfactor=cfactor, pcount=pcount)
			else:
				sentence += sym + ' '

		# backtracking: clear the modification to pcount
		pcount[rand_prod] -= 1
		return sentence

	def weighted_choice(weights):
		rnd = random.random() * sum(weights)
		for i, w in enumerate(weights):
			rnd -= w
			if rnd < 0:
				return i
# end of class benderskyCFG
	
main() # This must be the last thing