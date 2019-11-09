from OLD import *

class Clause:
	def __init__(self,name,preconditions,posconditions,functions={},state=None):
		slots = lambda l : [x for x in l.split(" and ")]
		clear = lambda l : set(map(lambda x : x.strip(),l))

		positives = lambda l : [x for x in slots(l) if "not " not in x]
		negatives = lambda l : [x.replace("not ","") for x in slots(l) if "not " in x]

		self.name  = name
		self.state = state

		if type(preconditions) == tuple:
			self.pos_pre = preconditions[0]
			self.neg_pre = preconditions[1]
		else:
			self.pos_pre = clear(positives(preconditions))
			self.neg_pre = clear(negatives(preconditions))

		if type(posconditions) == tuple:
			self.pos_pos = posconditions[0]
			self.neg_pos = posconditions[1]
		else:
			self.pos_pos = clear(positives(posconditions))
			self.neg_pos = clear(negatives(posconditions))

		self.functions = functions

	def __str__(self):
		return ("Action Name: {}\n"+
				"Positive Pre: {}\n"+
				"Negative Pre: {}\n"+
				"Positive Pos: {}\n"+
				"Negative Pos: {}"
		).format(self.name, self.pos_pre, self.neg_pre,
				self.pos_pos,self.neg_pos
		)

	def apply(self, state):
		return state.union(self.pos_pos).difference(self.neg_pos)

	def applicable(self, state):
		if '?' in str(self.pos_pre)+str(self.neg_pre):
			grounded = self.ground(state,axis=1)
			g = map(lambda x : x[0].pos_pre.issubset(state) and not x[0].neg_pre.intersection(state),grounded)
			return any(g)

		## Guarantees equivalent of self.pos_pre.issubset(state)
		for e1 in self.pos_pre:
			if "False" in e1:
				return False
			if "True" in e1:
				continue
			if e1 not in state:
				return False

		return not self.neg_pre.intersection(state)

	def getPossibleBindings(self,c,axis=0):
		tokenize = lambda l : map(lambda x : x.split(' '), l)
		l_filter = lambda ls, vs : len(ls) == len(vs) and all([l==v for l,v in zip(ls,vs) if '?' not in l])
		getset = lambda n : [(self.pos_pos,self.pos_pre)[axis],(self.neg_pos,self.pos_pos)[axis]][n]

		tokenized_self_pos = tokenize(getset(0))
		tokenized_self_neg = tokenize(getset(1))

		if axis:
			tokenized_c_pos = [x.strip().replace(', ',',').split(" ") for x in c if 'not' not in x and '(' not in x]
			tokenized_c_neg = [x.strip().replace(', ',',').split(" ") for x in c if 'not' in x and '(' not in x]
		else:
			tokenized_c_pos = tokenize(c.pos_pre)
			tokenized_c_neg = tokenize(c.neg_pre)

		possibilities = []

		bindings = {}
		for t in ["pos", "neg"]:
			tokenized_self = eval("tokenized_self_{}".format(t))
			tokenized_c    = eval("tokenized_c_{}".format(t))

			for s in tokenized_c:
				for e in filter(lambda x: l_filter(x,s),tokenized_self):
					for i in range(1,len(e)):
						if '?' in e[i]:
							if e[i] not in bindings:
								bindings[e[i]] = set([])
							bindings[e[i]].add(s[i])

		keys = list(bindings)
		def getAllBindings(curKey):
			if curKey == len(keys):
				return [[]]

			key = keys[curKey]
			tmp = []
			for l in getAllBindings(curKey+1):
				for binding in bindings[key]:
					tmp.append([(key,binding)]+l)
			return tmp

		[possibilities.append(dict(pseudo_dict)) for pseudo_dict in getAllBindings(0)]

		return possibilities

	def ground(self,c,axis=0, restrictions=None):
		possibilities = self.getPossibleBindings(c,axis)
		lapply = lambda _d : lambda x,y=_d : applyBindings(x,y,self.functions,self.state)

		#matching
		found = []
		for d in possibilities:
			if restrictions is not None:
				skip = 0
				for key,value in restrictions:
					if key in d and d[key] != value:
						skip = 1
						break
				if skip:
					continue

			grounded_pos_pre = map(lapply(d),self.pos_pre)
			grounded_neg_pre = map(lapply(d),self.neg_pre)
			grounded_pos_pos = map(lapply(d),self.pos_pos)
			grounded_neg_pos = map(lapply(d),self.neg_pos)

			for d1 in possibilities:
				grounded_pos_pre = map(lapply(d1),grounded_pos_pre)
				grounded_neg_pre = map(lapply(d1),grounded_neg_pre)
				grounded_pos_pos = map(lapply(d1),grounded_pos_pos)
				grounded_neg_pos = map(lapply(d1),grounded_neg_pos)

				if [('?' not in str(grounded_pos_pre)+str(grounded_neg_pre)),('?' not in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
					break

			if [('?' not in str(grounded_pos_pre)+str(grounded_neg_pre)),('?' not in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
				grounded_pos_pre = set(grounded_pos_pre)
				grounded_neg_pre = set(grounded_neg_pre)
				grounded_pos_pos = set(grounded_pos_pos)
				grounded_neg_pos = set(grounded_neg_pos)
				found.append(Clause(self.name + " grounded",(grounded_pos_pre,grounded_neg_pre),(grounded_pos_pos,grounded_neg_pos),functions=self.functions,state=self.state))

		return found

def applyBindings(string, bindings, functions, state):
	tokens = string.replace(", ", ",").split(' ')
	tmp = []
	for token in tokens:
		f = lambda x : x
		if '(' in token:
			i = token.index('(')
			aux = token[:i],token[i+1:-1]
			f = aux[0]
			pars = aux[1].replace(","," ")
			pars = applyBindings(pars,bindings,functions,state)
			pars = pars.replace(" ",",")

			token = "{}({})".format(f,pars)
			if '?' not in pars:
				token = str(eval("functions['{}']({})({})".format(f,state,pars)))
		else:
			for k,v in bindings.items():
				if token == k:
					token = v
					break

		tmp.append(token)

	return ' '.join(tmp)

def toSet(str, evaluator=None):
	slots = lambda l : [x for x in l.split(" and ")]
	clear = lambda l : set(map(lambda x : x.strip(),l))

	if evaluator is not None:
		str = applyBindings(str,evaluator["bindings"],evaluator["functions"],evaluator["state"])

	return clear(slots(str))

def getPlan(initial_state, actions, positive_goals, negative_goals):
	import planner
	p = planner.Planner()
	return p.getPlan(initial_state,actions,positive_goals,negative_goals)

def clauseListToDictList(act,clauses, informed_pars=None):
	from re import sub

	bindings = {}
	del_pars = []
	steps = {"return_name":[None,None],"distinct":[]}
	dDict = None

	for c in clauses:
		fun = c.name.split(" ")[0]

		d = {}

		for k,v in act.toFunction(fun).items():
			d[k] = v

		pos = set(list(c.pos_pos) + list(c.neg_pos))
		caux = Clause(fun,d["contract"]["pos"],d["contract"]["pre"])
		possibilities = []

		for p in caux.getPossibleBindings(pos,axis=1):
			for p1 in caux.getPossibleBindings(c):
				aux = p1

				for k,v in p.items():
					if k not in aux:
						aux[k] = v

				possibilities.append(aux)

		possibilities = possibilities[:1]
		
		for p in possibilities:
			for k,v in p.items():
				k = k.replace("?","")

				if k not in bindings:
					bindings[k] = v

				else:
					original = k
					if v != bindings[original]:
						k = sub("[^a-zA-Z]","",k)
						newKey = k
						i = 0

						while True:
							if newKey in bindings and v == bindings[newKey]:
								steps["distinct"].append((original,newKey))
								break

							if newKey not in bindings:
								bindings[newKey] = v
								steps["distinct"].append((original,newKey))
								break

							newKey = k+str(i)
							i+=1

		if "return" in d:
			ret = "?"+d["return"]
			n = d["return"]
			if ret in possibilities[0]:
				for k,v in bindings.items():
					if v == possibilities[0][ret]:
						n = k
						steps["distinct"].append((n,k))
						del_pars.append(n)
						break

			steps["return_name"] = steps["return_name"][1:] + [n]

		pars = d["par"].split(",")
		for old,new in steps["distinct"]:
			if old in pars:
				i = pars.index(old)
				pars[i] = new

		d["par"] = ','.join(pars)

		if dDict is None:
			dDict = d
		else:
			dDict = act.joinDicts(dDict,d,distinct=steps["distinct"],return_name=steps["return_name"])

		steps["distinct"] = []


	pars_splits = dDict["par"].split(",")


	matching_pars = -1 if informed_pars is None else\
		len(
			[True for x in informed_pars if x in pars_splits or not len(x)]
		)

	if matching_pars < len(pars_splits):
		pars_splits = [
				x for x in pars_splits 
				if x not in del_pars and x+'___' in dDict["step"]
			]

	else:
		pad = ["pad{}".format(i) for i in range(matching_pars-len(pars_splits))]
		pars_splits+= pad
	dDict["par"] = ','.join(pars_splits)


	### Check to remove conditions that don't appear on the parameters
	for contType in dDict["contract"]:
		contract   = dDict["contract"][contType]
		conditions = contract.split(" and ")
		for i in range(len(conditions),0,-1):
			i-=1

			vars = conditions[i].split(' ')[1:]
			d = []
			for par in dDict["par"].split(","):
				tmp = []
				for var in vars:
					tmp.append(par != var[1:] or '?' not in var)
				d.append(all(tmp) and len(vars))

			if all(d) and '?' in conditions[i]:
				del conditions[i]

		dDict["contract"][contType] = " and ".join(conditions)

	### Check to remove pos conditions placeholders that don't appear on the pre conditions
	tokens = dDict["contract"]["pre"].split(" ")
	conditions = dDict["contract"]["pos"].split(" and ")
	for i,c in reversed(enumerate(conditions)):
		for token in c.split(' '):
			if '?' in token and token not in tokens:
				del conditions[i]
				break
	dDict["contract"]["pos"] = " and ".join(conditions)

	return dDict

def dict2clause(aDict,functions=None,state=None):
	return Clause(
		aDict["name"],
		aDict["contract"]["pre"],
		aDict["contract"]["pos"],
		functions,
		state
	)

if __name__ == "__main__":
	from act import ActionMaker
	from EnvManager import *

	from AgtSimulator import env
	e = env()
	state = e.statefy()

	a = ActionMaker(
			{
				"step_down":stepDict('down'),"step_up":stepDict('up'), 
				"step_right":stepDict('right'),"step_left":stepDict('left'), 
				"drop_down":dropDict('down'),"drop_up":dropDict('up'), 
				"drop_right":dropDict('right'),"drop_left":dropDict('left'), 
				"pick" : pickDict()
			},
			{
				"step_down":lambda e=e.env : step(env,"down"), 
				"step_right":lambda e=e.env : step(env,"right"), 
				"step_left":lambda e=e.env : step(env,"left"), 
				"step_up":lambda e=e.env : step(env,"up"), 
				"drop_down":lambda e=e.env : drop(env,"down"), 
				"drop_right":lambda e=e.env : drop(env,"right"), 
				"drop_left":lambda e=e.env : drop(env,"left"), 
				"drop_up":lambda e=e.env : drop(env,"up"), 
				"pick" : lambda x, y=e.env : pick(x,y), 
				"drop" : lambda x, y=e.env : drop(x,y), 
			},
		)


	functions = {
		"free" 	: lambda _state, _env=e.env : lambda x, y=_env, z=_state : state_free(x,y,z),
		"close" : lambda _state : lambda x, y : close(x,y),
		"up"	: lambda _state : lambda x : up(x),
		"down"	: lambda _state : lambda x : down(x),
		"left"	: lambda _state : lambda x : left(x),
		"right"	: lambda _state : lambda x : right(x),
	}

	pu = dict2clause(pickDict(),functions)
	u  = dict2clause(stepDict("up"),functions)
	d  = dict2clause(stepDict("down"),functions)
	l  = dict2clause(stepDict("left"),functions)
	r  = dict2clause(stepDict("right"),functions)
	du  = dict2clause(dropDict("up"),functions)
	dd  = dict2clause(dropDict("down"),functions)
	dl  = dict2clause(dropDict("left"),functions)
	dr  = dict2clause(dropDict("right"),functions)
	actions = [pu,u,d,l,r,du,dd,dl,dr]

	print (e.statefy())
	places = "{}-{}".format([1,6], [1,10]).replace(' ','').split('-')
	# places = "{}-{}".format(list(e.env["objects"]["R"]), list(e.env["objects"]["G"])).replace(' ','').split('-')
	target = "at {} G and at {} R".format(places[0],places[1])
	# target = "at [3,25] G"

	print (target)

	# import sys
	# dump = open('/tmp/dump.txt','w')
	# tmp  = sys.stdout 
	# sys.stdout=dump
	plan = getPlan(state, actions, target, "")
	# sys.stdout=tmp
	# dump.close()


	if plan[0]:
		plan = plan[1]
		print (clauseListToDictList(a,plan))
	else:
		print("Failed")
