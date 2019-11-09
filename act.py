from OLD import *
from copy import copy

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
	from PIL import Image
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
	def __init__(self,known_actions={"crop" : cropDict(), "paste" : pasteDict()}, known_functs = {"crop" : crop, "paste" : paste},logical_functions=None):
		self.known_actions 		= known_actions
		self.known_functs		= known_functs
		self.logical_functions 	= logical_functions

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

		import os
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

		for elem,newName in distinct:
			f2 = f2.replace(elem,newName)

		pars = d1["par"].split(",")
		for par in d2["par"].split(","):
			for elem,newName in distinct:
				if par == elem:
					par = newName
					break

			if par not in pars:
				pars.append(par)

		pars = ','.join(pars)

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
			if "not "+c in d1_cont["pos"]:
				d1_cont["pos"].remove("not "+c)

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
		if op in self.known_actions:
			ret = self.known_actions[op]
		elif op in self.learned_actions:
			ret = self.learned_actions[op]
		else:
			return None

		return copy(ret)


	def createNew(self,line,goal,args):
		goal = args["formatGoal"].formatGoal(goal)
		s0   = args["statefier"]()

		max_pars = list(args)+ [""]*(len(line.split('___'))-1)

		found,plan = self.findPlan(s0,goal, informed_pars=max_pars)

		if found:
			aName = line[:line.index('_')]
			self.learned_actions[aName] = plan
			self.learned_actions[aName]["name"] = aName

			with open(".learned/a.json","w") as outfile:
				outfile.write(str(self.learned_actions))
			#add it to the agent's list
			return self.execute(line, args)

		return None

	def findPlan(self,s0,goal,informed_pars=None, changed_action=None):
		import solve
		target = solve.Clause("goal",goal,"")

		clauses = []

		l_append = lambda dict : [clauses.append(
							solve.dict2clause(d,functions=self.logical_functions)
						)
					for f,d in dict.items() if f != changed_action
				]
				
		
		l_append(self.known_actions)
		l_append({})
		# l_append(self.learned_actions)

		found, plan = solve.getPlan(s0,clauses,target.pos_pre,target.neg_pre)

		return found, (None if not found else solve.clauseListToDictList(self,plan,informed_pars))

	def execute(self,line,args):
		pars = line.split("___")
		command = pars[0]
		max_informed_pars = list(args)+[""]*(len(pars)-1)
		
		fdict = self.toFunction(command)

		if fdict is None:
			return None
			
		env = args['env']
		statefier = args['statefier']

		par = [y for p1,p2 in zip(fdict['par'].split(','), pars[1:]) for x,y in args.items() if x==p1 or x==p2]

		pars = fdict["par"].split(",")

		assert len(par) >= len(pars)
		
		return self.match_params(pars,par,fdict,statefier,env, informed_pars=max_informed_pars)
		

	def match_params(self,keys,values,fdict, statefier, env, informed_pars=None):
		from itertools import permutations

		split_pre = fdict["contract"]["pre"].split(' ')
		split_pos = fdict["contract"]["pos"].split(' ')
		steps = fdict["step"].split(";")

		state = statefier()
		possibilities = list(permutations(values,len(keys)))
		ignore = []

		def getDict(possibility):
			tmp_dict = copy(fdict)
			tmp_bind = {}

			tmp_pre = copy(split_pre)
			tmp_pos = copy(split_pos)

			for label,val in zip(keys,possibility):
				tmp_bind[label] = val

				k = "?{}".format(label)
				for i,token in enumerate(tmp_pre):
					if token == k:
						tmp_pre[i] = "{0}".format(val).replace(" ","") # Spaces are evil
				for i,token in enumerate(tmp_pos):
					if token == k:
						tmp_pos[i] = "{0}".format(val).replace(" ","") # Spaces are evil

			tmp_dict["contract"]["pre"] = ' '.join(tmp_pre)
			tmp_dict["contract"]["pos"] = ' '.join(tmp_pos)
			return tmp_dict, tmp_bind

		for index, possibility in enumerate(possibilities):
			tmp_dict, tmp_bind = getDict(possibility)

			try:
				tmp_dict["contract"] = self.getContract(fdict,statefier())
				a = self.simulate(state,steps,tmp_dict["contract"]["pos"],tmp_bind)
			except:
				a = False
				ignore.append(index)

			if a:
				break

		if not a:
			for index, possibility in enumerate(possibilities):
				if index in ignore:
					continue

				tmp_dict, _ = getDict(possibility)
				print ('here', possibility)

				try:
					found, new_plan = self.findPlan(state, tmp_dict["contract"]["pos"], informed_pars=informed_pars, changed_action=tmp_dict["name"])
				except:
					found = False

				print ('-->', found)
				if found:
					break

			return found if not found else self.match_params(keys,values,new_plan, statefier, env, informed_pars=informed_pars)

		return self.runDict(tmp_dict,tmp_bind,env,statefier,informed_pars=informed_pars)

	def getContract(self,incompleteContract,state):
		from solve import dict2clause, toSet
		state   = toSet(state, {"bindings":{},"functions":self.logical_functions,"state":state})
		
		c = dict2clause(incompleteContract,functions=self.logical_functions,state=state)

		possibilities = c.ground(state,axis=1)

		if not len(possibilities):
			return None

		d = possibilities[0]

		pre = ' and '.join(list(d.pos_pre) + ["not {}".format(x) for x in d.neg_pre])
		pos = ' and '.join(list(d.pos_pos) + ["not {}".format(x) for x in d.neg_pos])

		return {"pre" : pre, "pos" : pos}


	def simulate(self,state,steps, poscond,vars):
		from solve import dict2clause, toSet, Clause
		state   = toSet(state, {"bindings":{},"functions":self.logical_functions,"state":state})
		getFunc = lambda x : x.split('=')[-1].split('(')[0]
		getPars = lambda x : x.split('=')[-1].split('(')[1][:-1].split(',')

		goal = Clause("goal", poscond, "")

		for step in steps:
			comm = getFunc(step)
			d = self.toFunction(comm)

			old = getPars(d["step"])
			new = getPars(step)

			c = dict2clause(d,functions=self.logical_functions,state=state)

			tmp = []
			for par,var in zip(old,new):
				if '___' not in par:
					continue

				tmp.append(('?'+par[:-3],vars[var[:-3]]))

			possibilities = c.ground(state,axis=1,restrictions=tmp)
		
			f = 0
			for p in possibilities:
				if p.applicable(state):
					state = p.apply(state)
					f = 1
					break

			if not f:
				return False

		return goal.applicable(state)

	def runDict(self,funcDict,var,env,statefier, informed_pars=None):
		steps = funcDict["step"].replace(" ","").split(";")

		for i,line in enumerate(steps):
			assign  = None
			command = line

			applicable = bool(self.simulate(statefier(), steps[i:], funcDict["contract"]["pos"],var))
			
			if not applicable:
				found, new_plan = self.findPlan(statefier(), funcDict["contract"]["pos"], informed_pars=informed_pars, changed_action=funcDict["name"])
				return found if not found else self.match_params(new_plan["par"].split(','), list(var.values()), new_plan, statefier, env, informed_pars=informed_pars)

			if '=' in line:
				assign, command = line.split("=")
			
			f = command.split('(')[0]
			command = command.replace(f,"self.known_functs['{}']".format(f))

			for label in var:
				func_par = label+"___"
				if func_par in command:
					command = command.replace(func_par,"var['{}']".format(label))

			return_value = eval(command)

			if assign is not None:
				var[assign] = return_value

		return var[assign] if assign is not None else True


if __name__ == "__main__":
	from EnvManager import *

	from AgtSimulator import env
	e = env()
	state = e.statefy()

	functions = {
		"free" 	: lambda _state, _env=e.env : lambda x, y=_env, z=_state : state_free(x,y,z),
		"close" : lambda _state : lambda x, y : close(x,y),
		"up"	: lambda _state : lambda x : up(x),
		"down"	: lambda _state : lambda x : down(x),
		"left"	: lambda _state : lambda x : left(x),
		"right"	: lambda _state : lambda x : right(x),
	}

	a = ActionMaker(
			{
				"step_down":stepDict('down'),"step_up":stepDict('up'), 
				"step_right":stepDict('right'),"step_left":stepDict('left'), 
				"drop_down":dropDict('down'),"drop_up":dropDict('up'), 
				"drop_right":dropDict('right'),"drop_left":dropDict('left'), 
				"pick" : pickDict()
			},
			{
				"step_down"  : lambda e=e.env : step(e,"down"), 
				"step_right" : lambda e=e.env : step(e,"right"), 
				"step_left"  : lambda e=e.env : step(e,"left"), 
				"step_up"    : lambda e=e.env : step(e,"up"), 
				"drop_down"	 : lambda e=e.env : drop(env,"down"), 
				"drop_right" : lambda e=e.env : drop(env,"right"), 
				"drop_left"	 : lambda e=e.env : drop(env,"left"), 
				"drop_up"	 : lambda e=e.env : drop(env,"up"), 
				"pick"       : lambda x, y=e.env : pick(x,y), 
				"drop"       : lambda x, y=e.env : drop(x,y), 
			},
			logical_functions = functions
		)

	e.formatGoal = lambda x : x
	a.createNew("noop___red_box", "has R", {"env":e.env, "statefier":e.statefy, "formatGoal": e, "red_box":"R"})
	# a.execute('place___red box___room_5',args = {
	# 	"env":e.env, "statefier":e.statefy, "formatGoal": e, 
	# 	"red box":"R", "green box":"G", "blue box":"B", 
	# 	"room_1":[3,5],"room_2":[3,15],"room_3":[3,25],
	# 	"room_4":[15,5],"room_5":[15,15],"room_6":[15,25],
	# 	"corridor":[9,15]
	# })

	if "noop" in a.learned_actions:
		print ('->',a.learned_actions["noop"])
