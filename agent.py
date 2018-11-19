import os.path
import sys

import apiai

import dialogflow_v2 as dialogflow

class bot:
	def __init__(self,communicational_channel):
		import getpass
		import random
		CLIENT_ACCESS_TOKEN = 'b58c216c5ad84793b84657f5e544e6b8'
		self.ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
		self.last_response = None
		self.token = CLIENT_ACCESS_TOKEN
		self.id = "<{},{}>".format(getpass.getuser(),random.randint(0,10000))

		self.pending_line = None
		self.name = None

		from act import ActionMaker
		self.agent = ActionMaker()
		self.channel = communicational_channel

	def getAnswer(self,query):
		request = self.ai.text_request()
		request.session_id = self.id
		request.query = query
		self.last_response = eval(request.getresponse().read().replace("false","False").replace("true","True"))
		return self.last_response["result"]["fulfillment"]["speech"]

	def proccessAnswer(self,line,state,args):
		s = self.getAnswer(line)

		while ' & ' in s:
			splits = s.split(' & ')
			answer = self.getAnswer(splits[1])
			s = "{} &and& {}".format(splits[0],answer)

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
				# command = command.replace(" ","")
				# if "___this" in command:
				# 	command = command.replace("___this","___{}".format(str(getThisCoords(gui))))

				#				command,params
				r = self.agent.execute(command,args)
				# r = act.execute(command,gui.unresized_image,  gui.file, gui.dets)

				if r is None:
					self.pending_line = command

			elif self.last_response["result"]["metadata"]["intentName"] == "as Logic":
				command = command.replace(" and "," ").replace(" &and& ", " and ").replace(",","")
				#					        command, state,   goal, params
				r = self.agent.createNew(self.pending_line, state,command, args)
				# r = act.createNew(self.pending_line,command,gui.unresized_image,  gui.file, 					 self.name, gui.dets)
				self.pending_line = None
				self.name = None
		
		if r is not None:
			self.channel.put(r)
			# self.channel.put("Save changes?")
			# while len(pending) == 0:
			# 	continue
			# line = pending[0]
			# del pending[0]
			# if "yes" in line or "yeah" in line or "sure" in line:
			# 	self.channel.put([r])
			# else:
			# 	self.channel.put(None)
			self.channel.put("Ok, done")
		elif len(s) == 2 and self.pending_line is None:
			self.channel.put("I failed you.")

if __name__ == '__main__':
	b = bot()

	s = b.getAnswer("can you swap the dog and the cat?")
	if '|' in s:
		command, response = s.split("|")
		print response
		print command
	else:
		print s