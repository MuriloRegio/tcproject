
class Clause:
	def __init__(self,name,preconditions,posconditions,complex_poscondition = lambda x,y : x):
		slots = lambda l : [x for x in l.split("and")]
		clear = lambda l : set(map(lambda x : x.strip(),l))

		positives = lambda l : [x for x in slots(l) if "not" not in x]
		negatives = lambda l : [x.replace("not ","") for x in slots(l) if "not" in x]

		self.name = name

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

		self.complex_poscondition = complex_poscondition

	def __str__(self):
		return self.name+"\n"+\
				str(self.pos_pre)+"\t"+str(self.neg_pre)+"\n"+\
				str(self.pos_pos)+"\t"+str(self.neg_pos)

	def apply(self, state):
		new_state = state.union(self.pos_pos).difference(self.neg_pos)

		return self.complex_poscondition(new_state,self)

	def applicable(self, state):
		if '?' in str(self.pos_pre)+str(self.neg_pre):
			grounded = self.ground(state,axis=1)
			g = map(lambda x : x[0].pos_pre.issubset(state) and not x[0].neg_pre.intersection(state),grounded)
			return any(g)
		return self.pos_pre.issubset(state) and not self.neg_pre.intersection(state)

	def getPossibleBindings(self,c,axis=0):
		tokenize = lambda l : map(lambda x : x.split(' '), l) 
		l_filter = lambda l, v : v[0] == l[0]
		getset = lambda n : [(self.pos_pos,self.pos_pre)[axis],(self.neg_pos,self.pos_pos)[axis]][n]

		tokenized_self_pos = tokenize(getset(0))
		tokenized_self_neg = tokenize(getset(1))

		if axis:
			tokenized_c_pos = [x.split(" ") for x in c if 'not' not in x]
			tokenized_c_neg = [x.split(" ") for x in c if 'not' in x]
		else:
			tokenized_c_pos = tokenize(c.pos_pre)
			tokenized_c_neg = tokenize(c.neg_pre)

		possibilities = []

		for s in tokenized_c_pos:
			for e in filter(lambda x: l_filter(x,s),tokenized_self_pos):
				bindings = {}
				for i in range(len(e)-1):
					if '?' in e[i+1]:
						bindings[e[i+1]] = s[i+1]

				if len(list(bindings))>0:
					possibilities.append(bindings)

		for s in tokenized_c_neg:
			for e in filter(lambda x: l_filter(x,s),tokenized_self_neg):
				bindings = {}
				for i in range(len(e)-1):
					if '?' in e[i+1]:
						bindings[e[i+1]] = s[i+1]

				if len(list(bindings))>0:
					possibilities.append(bindings)

		return possibilities

	def ground(self,c,axis=0):
		possibilities = self.getPossibleBindings(c,axis)

		#matching
		found = []
		for d in possibilities:
			grounded_pos_pre = map(lambda x: applyBindings(x,d),self.pos_pre)
			grounded_neg_pre = map(lambda x: applyBindings(x,d),self.neg_pre)
			grounded_pos_pos = map(lambda x: applyBindings(x,d),self.pos_pos)
			grounded_neg_pos = map(lambda x: applyBindings(x,d),self.neg_pos)

			for d1 in possibilities:
				if d1 == d:
					continue

				grounded_pos_pre = map(lambda x: applyBindings(x,d1),grounded_pos_pre)
				grounded_neg_pre = map(lambda x: applyBindings(x,d1),grounded_neg_pre)
				grounded_pos_pos = map(lambda x: applyBindings(x,d1),grounded_pos_pos)
				grounded_neg_pos = map(lambda x: applyBindings(x,d1),grounded_neg_pos)

				if [('?' not in str(grounded_pos_pre)+str(grounded_neg_pre)),('?' not in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
					break

			if [('?' not in str(grounded_pos_pre)+str(grounded_neg_pre)),('?' not in str(grounded_pos_pos)+str(grounded_neg_pos))][1-axis]:
				grounded_pos_pre = set(grounded_pos_pre)
				grounded_neg_pre = set(grounded_neg_pre)
				grounded_pos_pos = set(grounded_pos_pos)
				grounded_neg_pos = set(grounded_neg_pos)
				found.append((Clause(self.name + " grounded",(grounded_pos_pre,grounded_neg_pre),(grounded_pos_pos,grounded_neg_pos)),self))

		return found

def applyBindings(string, bindings):
	for k,v in bindings.items():
		string = string.replace(k,v)
	return string

def toSet(str):
	slots = lambda l : [x for x in l.split("and")]
	clear = lambda l : set(map(lambda x : x.strip(),l))

	return clear(slots(str))

def h(actions, initial_state, positive_goals, negative_goals):
	hmax = 0
	state = initial_state
	new_state = initial_state

	l_applicable = lambda a : a.applicable(state)
	
	c = Clause(
			"",
			(positive_goals,set([])),
			""
		)

	while True:
		if positive_goals.issubset(state) or c.applicable(state):
			break

		for a in actions:
			for grounded,_ in a.ground(state,axis=1):
				subgrounds = grounded.ground(c)
				if len(subgrounds) == 0:
					new_state = new_state.union(grounded.pos_pos)
				else:
					for g,_ in subgrounds:
						new_state = new_state.union(g.pos_pos)

		if len(state) == len(new_state):
			return float("inf")
		
		state = new_state
		hmax+= 1

	return hmax

def getPlan(initial_state, actions, positive_goals, negative_goals):
	found, plan = getRPlan(initial_state, actions, positive_goals, negative_goals)
	rplan = reversed(plan)
	plan = []
	for act in rplan:
		plan.append(act)
	return found, plan

def getRPlan(initial_state, actions, positive_goals, negative_goals):
	from Queue import PriorityQueue as PQ
	explored = set([])
	states = PQ()

	c = Clause(
			"cur state",
			(positive_goals,negative_goals),
			""
		)

	states.put((0,0,c,[]))

	possible_actions = []
	for a in actions:
		for grounded,_ in a.ground(c):
			possible_actions.append(grounded)

	for a in actions:
		for grounded,_ in a.ground(initial_state,axis=1):
			possible_actions.append(grounded)

	l_applicable = lambda a : bool(a.pos_pos.intersection(c.pos_pre)) or a.neg_pos.intersection(c.neg_pre)

	while not states.empty():
		cost, count, c, plan = states.get()


		if c.applicable(initial_state):
			return (True,plan)

		# for a in actions:
		# 	for grounded,clause in a.ground(c):
		for a in filter(l_applicable,possible_actions):
			new_pos_pre = c.pos_pre.union(a.pos_pre).difference(c.pos_pre.intersection(a.pos_pos))
			new_neg_pre = c.neg_pre.union(a.neg_pre).difference(c.neg_pre.intersection(a.neg_pos))

			key = tuple((frozenset(new_pos_pre),frozenset(new_neg_pre)))

			if key in explored:
				continue

			explored.add(key)

			new_cost = cost + h(actions,initial_state,new_pos_pre,new_neg_pre)

			if new_cost == float("inf"):
				continue

			new_c = Clause(
				"cur state",
				(new_pos_pre,new_neg_pre),
				""
			)

			count += 1
			new_plan = plan + [a]
			states.put((new_cost,count,new_c,new_plan))

	#add case of failure, what was the closest it got
	return (False,[[]])


def phisics(s,c):
	t = c.pos_pos

	for elem in t:
		if "at" in elem:
			coord1 = elem.split(" ")[1]
			coord2 = []
			r = []

			for el in s:
				if "at" in el:
					coord2 = el.split(" ")[1]

					if coord2 == coord1 and el != elem:
						r.append(el)

			s = s.difference(set(r))

	return s

def clauseListToDictList(act,clauses):
	bindings = {}
	steps = {"rename":[], "distinct":[]}
	dDict = None
	count = 0
	change = -1
	for c in clauses:
		fun = c.name.split(" ")[0]
		d = act.getFunctDict(fun)

		if fun == "paste":
			if change < 0:
				change = count
			steps["rename"].append(("obj",count-change-1))

		pos = set([' '.join((' '.join(c.pos_pos), ' '.join(map(lambda x: "not "+x,c.neg_pos))))])
		caux = Clause(fun,d["contract"]["pos"],d["contract"]["pre"])
		possibilities = []

		for p in caux.getPossibleBindings(pos,axis=1):
			for p1 in caux.getPossibleBindings(c):
				aux = p1
				for k,v in p.items():
					if k not in aux:
						aux[k] = v
				possibilities.append(aux)

		for p in possibilities:
			for k,v in p.items():
				k = k.replace("?","")
				if k not in bindings:
					bindings[k] = v
				else:
					if v != bindings[k]:
						i = 0
						while True:
							newKey = k+str(i)
							if newKey in bindings and v == bindings[newKey]:
								change = 1
								for alias,_ in steps["rename"]:
									if alias == k:
										change = 0
								if change:
									steps["distinct"].append((k,newKey))
								break
							if newKey not in bindings:
								bindings[newKey] = v
								steps["distinct"].append((k,newKey))

		if dDict == None:
			dDict = d
		else:
			dDict,count = act.joinDicts(dDict,d,count,steps["rename"],steps["distinct"])

		steps = {"rename":[], "distinct":[]}

		if fun == "paste":
			steps["rename"] = [("img",count-change)]


	return dDict

if __name__ == "__main__":
	c1 = Clause(
		"crop",
		"at ?coord ?obj",
		"have ?obj"
	)
	c2 = Clause(
		"paste",
		"have ?obj",
		"at ?coord ?obj",
		phisics
	)

	target = Clause(
		"target",
		"have dog",
		""
	)

	state = toSet("at 123 dog and at 321 cat")
	#for c in c1.ground(target):
	#	print str(c[0]), str(c[1])

	#print c1.applicable(state)
	plan = getPlan(state, [c1,c2], toSet("at 321 dog and at 123 cat"), set([]))
	if plan[0]:
		from act import ActionMaker
		clauseListToDictList(ActionMaker(),plan)
	else:
		print plan[1]
		for a in plan[1][-1]:
			print a.name
		print len(plan[1][-1])