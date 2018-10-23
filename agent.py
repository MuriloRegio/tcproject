import os.path
import sys

import apiai

import dialogflow_v2 as dialogflow

class bot:
    def __init__(self):
        import getpass
        import random
        CLIENT_ACCESS_TOKEN = 'b58c216c5ad84793b84657f5e544e6b8'
        self.ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
        self.last_response = None
        self.token = CLIENT_ACCESS_TOKEN
        self.id = "<{},{}>".format(getpass.getuser(),random.randint(0,10000))

    def getAnswer(self,query):
        request = self.ai.text_request()
        request.session_id = self.id
        request.query = query
        self.last_response = eval(request.getresponse().read().replace("false","False").replace("true","True"))
        return self.last_response["result"]["fulfillment"]["speech"]

if __name__ == '__main__':
    b = bot()

    s = b.getAnswer("can you swap the dog and the cat?")
    if '|' in s:
        command, response = s.split("|")
        print response
        print command
    else:
        print s