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
			#print ("hey")
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

		# for e1 in self.neg_pre: How does THIS work?
		# 	if "False" in e1:
		# 		return False
		# 	if "True" in e1:
		# 		continue
		# 	if e1 not state:
		# 		return False

		# return self.pos_pre.issubset(state) and not self.neg_pre.intersection(state)
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
		#print (tokenized_self_pos)
		#print (list(tokenized_self_pos))

		for s in tokenized_c_pos:
			tmp = []
			for e in filter(lambda x: l_filter(x,s),tokenized_self_pos):
				bindings = {}
				for i in range(len(e)-1):
					if '?' in e[i+1]:
						bindings[e[i+1]] = s[i+1]
				# print ('=============/')
				# print (e,s)
				# print (bindings)
				# print ('/=============')
				if len(list(bindings))>0:
					add = 1
					for p in possibilities:
						if not set(bindings).issubset(set(p)):
							for k,v in bindings.items():
								p[k] = v
							add = 0
					if add:
						tmp.append(bindings)
			possibilities = possibilities + tmp

		for s in tokenized_c_neg:
			tmp = []
			for e in filter(lambda x: l_filter(x,s),tokenized_self_neg):
				bindings = {}
				for i in range(len(e)-1):
					if '?' in e[i+1]:
						bindings[e[i+1]] = s[i+1]


				if len(list(bindings))>0:
					add = 1
					for p in possibilities:
						if not set(bindings).issubset(set(p)):
							for k,v in bindings.items():
								p[k] = v
							add = 0
					if add:
						tmp.append(bindings)
			possibilities = possibilities + tmp

		if len(possibilities) == 0:
			return []
		threshold = max(map(len,possibilities))
		# print possibilities
		possibilities = [x for x in possibilities if len(x)==threshold]
		return possibilities

	def ground(self,c,axis=0):
		possibilities = self.getPossibleBindings(c,axis)
		lapply = lambda _d : lambda x,y=_d : applyBindings(x,y,self.functions,self.state)
		#print (possibilities)
		print (len(possibilities))

		#matching
		found = []
		for d in possibilities:
			# grounded_pos_pre = map(lambda x: applyBindings(x,d,self.functions),self.pos_pre)
			# grounded_neg_pre = map(lambda x: applyBindings(x,d,self.functions),self.neg_pre)
			# grounded_pos_pos = map(lambda x: applyBindings(x,d,self.functions),self.pos_pos)
			# grounded_neg_pos = map(lambda x: applyBindings(x,d,self.functions),self.neg_pos)
			grounded_pos_pre = map(lapply(d),self.pos_pre)
			grounded_neg_pre = map(lapply(d),self.neg_pre)
			grounded_pos_pos = map(lapply(d),self.pos_pos)
			grounded_neg_pos = map(lapply(d),self.neg_pos)

			for d1 in possibilities:
				# if d1 == d:
				# 	continue

				# grounded_pos_pre = map(lambda x: applyBindings(x,d1,self.functions),grounded_pos_pre)
				# grounded_neg_pre = map(lambda x: applyBindings(x,d1,self.functions),grounded_neg_pre)
				# grounded_pos_pos = map(lambda x: applyBindings(x,d1,self.functions),grounded_pos_pos)
				# grounded_neg_pos = map(lambda x: applyBindings(x,d1,self.functions),grounded_neg_pos)
				grounded_pos_pre = map(lapply(d1),grounded_pos_pre)
				grounded_neg_pre = map(lapply(d1),grounded_neg_pre)
				grounded_pos_pos = map(lapply(d1),grounded_pos_pos)
				grounded_neg_pos = map(lapply(d1),grounded_neg_pos)

				if [('?' not in str(grounded_pos_pre)+str(grounded_neg_pre)),('?' not in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
					break

			# if [('False' in str(grounded_pos_pre)+str(grounded_neg_pre)),('False' in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
			#	continue
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
		# string = string.replace(k,v)
		tmp.append(token)

	# 	tokens = [x if x != k else v+"-!-" for x in tokens]
	# return ' '.join(tokens).replace("-!-","")
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

# def h(actions, initial_state, positive_goals, negative_goals):
# 	hmax = 0
# 	state = initial_state
# 	new_state = initial_state

# 	l_applicable = lambda a : a.applicable(state)
	
# 	c = Clause(
# 			"",
# 			(positive_goals,set([])),
# 			""
# 		)

# 	while True:
# 		if positive_goals.issubset(state) or c.applicable(state):
# 			break

# 		for a in actions:
# 			for grounded,_ in a.ground(state,axis=1):
# 				subgrounds = grounded.ground(c)
# 				if len(subgrounds) == 0:
# 					new_state = new_state.union(grounded.pos_pos)
# 				else:
# 					for g,_ in subgrounds:
# 						new_state = new_state.union(g.pos_pos)

# 		if len(state) == len(new_state):
# 			return float("inf")
		
# 		state = new_state
# 		hmax+= 1

# 	return hmax

# def getPlan(initial_state, actions, positive_goals, negative_goals):
# 	found, plan = getRPlan(initial_state, actions, positive_goals, negative_goals)
# 	rplan = reversed(plan)
# 	plan = []
# 	for act in rplan:
# 		plan.append(act)
# 	return found, plan

# def getRPlan(initial_state, actions, positive_goals, negative_goals):
# 	l_applicable = lambda a : bool(a.pos_pos.intersection(c.pos_pre)) or bool(a.neg_pos.intersection(c.neg_pre))

# 	from Queue import PriorityQueue as PQ
# 	explored = set([])
# 	states = PQ()

# 	c = Clause(
# 			"cur state",
# 			(positive_goals,negative_goals),
# 			""
# 		)

# 	states.put((0,0,c,[]))

# 	possible_actions = []

# 	# for a in actions:
# 	# 	for grounded,_ in a.ground(c):
# 	# 		#print str(grounded)
# 	# 		possible_actions.append(grounded)

# 	# for a in actions:
# 	# 	# print a
# 	# 	for grounded,_ in a.ground(initial_state,axis=1):
# 	# 		possible_actions.append(grounded)

# 	while not states.empty():
# 		cost, count, c, plan = states.get()

# 		print c
# 		if c.applicable(initial_state):
# 			return (True,plan)

# 		for a in actions:
# 			for grounded,_ in a.ground(c):
# 				if grounded not in possible_actions: 
# 					#Should be the same as defining 'possible_actions'
# 					#as a set, but it isn't
# 					possible_actions.append(grounded)

# 		for a in possible_actions:
# 			for grounded,_ in a.ground(initial_state,axis=1):
# 				if grounded not in possible_actions: 
# 					possible_actions.append(grounded)


# 		for a in filter(l_applicable,possible_actions):
# 			print a
# 			new_pos_pre = c.pos_pre.union(a.pos_pre).difference(c.pos_pre.intersection(a.pos_pos))
# 			new_neg_pre = c.neg_pre.union(a.neg_pre).difference(c.neg_pre.intersection(a.neg_pos))

# 			key = tuple((frozenset(new_pos_pre),frozenset(new_neg_pre)))

# 			if key in explored:
# 				continue

# 			explored.add(key)

# 			# new_cost = cost + h(actions,initial_state,new_pos_pre,new_neg_pre)
# 			new_c = Clause(
# 				"cur state",
# 				(new_pos_pre,new_neg_pre),
# 				""
# 			)

# 			new_cost = new_c.applicable(initial_state)

# 			if new_cost == float("inf"):
# 				continue

# 			count += 1
# 			new_plan = plan + [a]
# 			states.put((new_cost,count,new_c,new_plan))

# 	#add case of failure, what was the closest it got
# 	return (False,[[]])

def clauseListToDictList(act,clauses):
	from re import sub

	bindings = {}
	del_pars = []
	steps = {"return_name":[None,None],"distinct":[]}
	dDict = None

	for c in clauses:
		fun = c.name.split(" ")[0]

		d = {}
		# print (fun)
		# print ([x for x in act.known_actions])
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

		if dDict is None:
			dDict = d
		else:
			# print steps["distinct"]
			# print dDict["contract"],d["contract"]
			dDict = act.joinDicts(dDict,d,distinct=steps["distinct"],return_name=steps["return_name"])

		steps["distinct"] = []

	for p in reversed(del_pars): 
		dDict["par"] = dDict["par"].replace(",{}".format(p),"")

	### Check to remove conditions that don't appear on the parameters
	for contType in dDict["contract"]:
		contract   = dDict["contract"][contType]
		conditions = contract.split(" and ")
		for i in range(len(conditions),0,-1):
			# i = (i+1)*-1
			i-=1

			# print(conditions[i], conditions, i)
			vars = conditions[i].split(' ')[1:]
			d = []
			for par in dDict["par"].split(","):
				tmp = []
				for var in vars:
					tmp.append(par not in var)
				d.append(all(tmp) and len(vars))
				# d.append(any(tmp))

			if all(d) and '?' in conditions[i]:
				del conditions[i]

		dDict["contract"][contType] = " and ".join(conditions)


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
				"pick" : pickDict(), "drop":dropDict()
			},
			{
				"step_down":lambda e=e.env : step(env,"down"), 
				"step_right":lambda e=e.env : step(env,"right"), 
				"step_left":lambda e=e.env : step(env,"left"), 
				"step_up":lambda e=e.env : step(env,"up"), 
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
	dd = dict2clause(dropDict(),functions)
	u  = dict2clause(stepDict("up"),functions)
	d  = dict2clause(stepDict("down"),functions)
	l  = dict2clause(stepDict("left"),functions)
	r  = dict2clause(stepDict("right"),functions)
	actions = [pu,dd,u,d,l,r]

	target = "has M"


	import sys
	dump = open('/tmp/dump.txt','w')
	tmp  = sys.stdout 
	sys.stdout=dump
	plan = getPlan(state, actions, target, "")
	sys.stdout=tmp
	dump.close()

	if plan[0]:
		plan = plan[1]
		# for p in plan:
		# 	print (p.name)
		print (clauseListToDictList(a,plan))
	else:
		print("Failed")