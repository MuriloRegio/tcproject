from OLD import *
from PIL import Image
import os

def crop(img,coord):
	return img.crop(coord)

def cropContract():
	return {
		"pre" : "at ?coord ?obj",
		"pos" : "have ?obj"
	}

def cropDict():
	return {"step":"return = crop(img___,coord___)",
			"contract":cropContract(),
			"par":"img,coord",
			"name":"crop",
			"return":"obj"}

def paste(img,coord,obj):
	size = (coord[2]-coord[0], coord[3]-coord[1])
	if type(obj) is list:
		obj = crop(img,obj)

	res_obj = obj.resize(size, Image.ANTIALIAS)

	img.paste(res_obj,coord[0:2])

	return img

def pasteContract():
	return {
		"pre" : "have ?obj",
		"pos" : "at ?coord ?obj"
	}

def pasteDict():
	return {"step":"return = paste(img___,coord___,obj___)",
			"contract":pasteContract(),
			"par":"img,coord,obj",
			"name":"paste",
			"return":"img"}

class ActionMaker():
	def __init__(self,known_actions={"crop" : cropDict(), "paste" : pasteDict()}, known_functs = {"crop" : crop, "paste" : paste}):
		self.known_actions = known_actions
		self.known_functs = known_functs

		self.learned_actions = {}
								# {"swap":{
								# 	"step":"im1=crop(img___,coord1___);img2=crop(img___,coord2___);img3=paste(img___,coord2___,img1___);\
								# 		img4=paste(img3___,coord1___,img2___)",
								# 	"contract":{	
								# 				"pre":"(at ?coord1 ?obj1) and (at ?coord2 ?obj2)",
								# 				"pos":"(at ?coord1 ?obj2) and (at ?coord2 ?obj2)" 
								# 			},
								# 	"par":"img,coord1,coord2",
								#	"return":"img"
								# 	}
								# }
		self.learned_contracts = []

		try:
			os.mkdir(".learned")
		except OSError:
			if "a.json" in os.listdir(".learned"):
				with open(".learned/a.json","r") as infile:
					self.learned_actions = eval(infile.read())


	def joinDicts(self, d1,d2, distinct=[],return_name=[None,None]):
		if return_name[0] is not None:
			d1["step"] = d1["step"].replace("return", return_name[0])

		if return_name[1] is not None:
			d2["step"] = d2["step"].replace("return", return_name[1])

		getSplits = lambda x, k : [y.split("=")[k] for y in x.replace(" ","").split(";")]

		f1 = d1["step"].replace(" ","")
		f2 = d2["step"].replace(" ","")

		pars = d1["par"].split(",")
		for par in d2["par"].split(","):
			for elem,newName in distinct:
				if par == elem:
					f2 = f2.replace(par+"___", newName+"___")

					if par not in pars:
						pars.append(par)
					par = newName

			if par not in pars:
				pars.append(par)

		pars = ','.join(pars)


		# assign2 = getSplits(f2,0)
		# assign1 = getSplits(f1,0)

		# calls1 = getSplits(f1,1)
		# calls2 = getSplits(f2,1)

		# join = lambda l1,l2: map(lambda x_y: x_y[0]+"="+x_y[1],zip(l1,l2))

		# functs = ';'.join([';'.join(join(assign1,calls1)),';'.join(join(assign2,calls2))])
		functs = ';'.join([f1,f2])

		#arruma contracts
		d1_cont = {"pre":set(d1["contract"]["pre"].split(" and ")),"pos":set(d1["contract"]["pos"].split(" and "))}
		d2_cont = {"pre":set(d2["contract"]["pre"].split(" and ")),"pos":set(d2["contract"]["pos"].split(" and "))}

		tmp_cont = {"pre":set([]),"pos":set([])}

		for t in d2_cont:
			for i,c in enumerate(d2_cont[t]):
				splits = c.split(' ')

				for j,s in enumerate(splits[1:]):
					for elem,newName in distinct:
						elem = '?' + elem
						if s == elem:
							splits[j+1] = '?'+newName

				# d2_cont[t].remove(c)
				# d2_cont[t].add(' '.join(splits))
				tmp_cont[t].add(' '.join(splits))
		d2_cont = tmp_cont

		for c in d2_cont["pre"]:
			if c in d1_cont["pos"]:
				d1_cont["pos"].remove(c)
			else:
				d1_cont["pre"].add(c)

		for c in d2_cont["pos"]:
			if len(c) > 5 and c[:5] == "not ":
				if c[5:] in d1_cont["pos"]:
					d1_cont["pos"].remove(c[5:])
			d1_cont["pos"].add(c)

		contracts = {}
		contracts["pre"] = ' and '.join(d1_cont["pre"])
		contracts["pos"] = ' and '.join(d1_cont["pos"])

		ret_d = {
			"step" : functs,
			"contract" : contracts,
			"par" : pars,
			"name" : "custom",
		}

		if 'return' in d2:
			ret_d["return"] = d2["return"]

		return ret_d

	def toFunction(self,op):
		try:
			return self.known_actions[op]
		except:
			try:
				return self.learned_actions[op]
			except:
				return None

	def createNew(self,line,s0,goal,args):
		goal = args[1]["formatGoal"].formatGoal(goal)

		found,plan = self.findPlan(s0,goal)

		if found:
			aName = line[:line.index('_')]
			self.learned_actions[aName] = solve.clauseListToDictList(self,plan)
			self.learned_actions[aName]["name"] = aName

			with open(".learned/a.json","w") as outfile:
				outfile.write(str(self.learned_actions))
			#add it to the agent's list
			# return self.execute(line.replace("noop",aName), img,imgpath,det=det)
			return self.execute(line, args)

		return None

	def findPlan(self,s0,goal):
		import solve
		target = solve.Clause("goal",goal,"")

		clauses = []

		l_append = lambda dict : map(lambda f_d : clauses.append(solve.Clause(f_d,f_d[1]["contract"]["pre"],f_d[1]["contract"]["pos"])), dict.items())
		
		l_append(self.known_actions)
		l_append(self.learned_actions)

		assert len(clauses) == len(self.known_actions)+len(self.learned_actions)

		return solve.getPlan(s0,clauses,target.pos_pre,target.neg_pre)

	def execute(self,line,args):
	# def execute(self,line,env):
		pars = line.split("___")
		command = pars[0]
		
		fdict = self.toFunction(command)

		if fdict is None:
			return None

		fixed, args = args
			#	args -> derivated from user speech
			#	fixed -> through other means, e.g., a GUI
		
		args = fixed + [y for p in pars[1:] for x,y in args.items() if x==p]

		# args = [env(label) for label in fdict["par"].split(',')]

		return self.runDict(fdict,args)

	# def execute(self,line,env):
	# 	pars = line.split("___")
	# 	command = pars[0]
		
	# 	fdict = self.toFunction(command)

	# 	if fdict is None:
	# 		return None

	# 	return self.runDict(fdict, env, pars[1:])

	def simulate(self,state,fdict):
		steps = fdict["steps"].split(';')
		getFunc = lambda x : x.split('(')[0]

		for step in steps:
			comm = getFunc(step)
			d = self.toFunction(comm)

			g = apply_bounds(state, d["contract"])

			if applicable(state, g["pre"]):
				state = apply(state, g["pos"])
			else:
				return False
		return True
		
	def getBindings(self, var, env, pars):
		var_bindings = {}
		i = 0
		for label in var:
			if label in env:
				var_bindings[label] = env(label)
			else:
				var_bindings[label] = env(pars[i])
				i+=1
		return var_bindings

	def runDict(self,funcDict,par):
		pars = funcDict["par"].split(",")

		# var = {}
		# i = 0
		# for line in funcDict["step"].replace(" ","").split(";"):
		# 	assign, command = line.split("=")
			
		# 	f = command.split('(')[0]
		#	fdict = self.toFunction(command)

		# 	if not check(fdict["contract"]["pre"], env): # -- format atual state to "s0" --
		# 		return self.createNew(line, s0, fdict["contract"]["pos"], env)
		# 	
		# 	var[assign] = eval(command)

		assert len(par) == len(pars)

		var = {}

		for label,val in zip(pars,par):
			var[label] = val

		assign = None
		for line in funcDict["step"].replace(" ","").split(";"):
			assign, command = line.split("=")
			
			f = command.split('(')[0]
			command = command.replace(f,"self.known_functs['{}']".format(f))

			for label in var:
				func_par = label+"___"
				if func_par in command:
					command = command.replace(func_par,"var['{}']".format(label))

			var[assign] = eval(command)

		return var[assign]


if __name__ == "__main__":
	actor = ActionMaker()

	img = "data/person.jpg"

	im = Image.open(img)

	try:
		with open("example_person_dets.dat","r") as infile:
			dets = eval(infile.read())
	except:
		dets = None

	#res = actor.execute("crop___dog",im,img)
	# res = actor.createNew("noop___dog___horse", "at ?horse dog and at ?dog horse", im, img, "swap",dets)
	# coord = [0,0, im.size[0],im.size[1]]
	# res = actor.execute("crop___"+str(coord),im)

	if res!=None:
		res.show()