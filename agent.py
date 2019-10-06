import os
import sys

import apiai

import dialogflow_v2 as dialogflow

class bot:
	def __init__(self,communicational_channel, back_agent = None):
		import getpass
		import random
		CLIENT_ACCESS_TOKEN = 'b58c216c5ad84793b84657f5e544e6b8'
		self.ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
		self.last_response = None
		self.token = CLIENT_ACCESS_TOKEN
		self.id = "<{},{}>".format(os.getlogin(),random.randint(0,10000))

		self.pending_line = None
		self.name = None

		from act import ActionMaker
		self.agent = back_agent
		if back_agent is None:
			self.agent = ActionMaker()
			
		self.channel = communicational_channel

	def getAnswer(self,query):
		request = self.ai.text_request()
		request.session_id = self.id
		request.query = query
		response = request.getresponse().read().decode('unicode_escape')
		
		self.last_response = eval(response.replace("false","False").replace("true","True"))
		return self.last_response["result"]["fulfillment"]["speech"]

	def proccessAnswer(self,line,args):
		s = self.getAnswer(line)

		while ' & ' in s:
			splits = s.split(' & ')
			answer = self.getAnswer(splits[1])
			s = "{} &and& {}".format(splits[0],answer)

		print (s)
		
		if len(s)==0:
			s = self.getAnswer("_-_-DEU RUIM-_-_")
			self.channel.put(s)
			return

		s = s.split("|")

		try:
			if self.last_response["result"]["parameters"]["Unknown"].replace(" ","") in self.agent.learned_actions:
				s[-1] = "Sure, i'll try it"
		except:
			pass

		self.channel.put(s[-1])
		r = None

		if len(s) == 2:
			command  = s[0]
			
			if self.last_response["result"]["metadata"]["intentName"] == "Identify unknown":
				command = command.replace(" and ","___").replace(", ","___").replace(" ","")
				r = self.agent.execute(command,args)

				if r is None:
					self.pending_line = command

			elif self.last_response["result"]["metadata"]["intentName"] == "as Logic":
				command = command.replace(" and "," ").replace(" &and& ", " and ").replace(",","")
				
				r = self.agent.createNew(self.pending_line, command, args)
				
				self.pending_line = None
				self.name = None
		
		if r is not None:
			self.channel.put(r)
			self.channel.put("Ok, done")

		elif len(s) == 2 and self.pending_line is None:
			self.channel.put("I failed you.")

if __name__ == '__main__':
	import queue
	channel = queue.Queue()

	b = bot(channel)

	s = b.getAnswer("can you swap the dog and the cat?")
	if '|' in s:
		command, response = s.split("|")
		print (response)
		print (command)
	else:
		print (s)