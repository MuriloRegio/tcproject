from copy import copy
from solve import *
from OLD import *

def h(actions, initial_state, positive_goals, negative_goals):
	hmax = 0
	state = initial_state
	new_state = initial_state

	l_applicable = lambda a : a.pos_pre.issubset(state)

	target = Clause(
		"target",
		(positive_goals,negative_goals),
		"",
	)
	# joined_goals = positive_goals.union(negative_goals)

	# WILL ENTER IN A LOOP IF AGENT'S UNABLE TO FULLFIL THE GOAL UNDER ANY CIRCUNSTANCE
	# I.E., ACTION NOT SUPPORTED
	while True:
		if positive_goals.issubset(state):
			break

		for a in actions:
			a.state = state
			for grounded in a.ground(state,axis=1):
				# subgrounds = grounded.ground(joined_goals,axis=1)
				subgrounds = grounded.ground(target)
				if len(subgrounds) == 0:
					new_state = new_state.union(grounded.pos_pos)
				else:
					for g in subgrounds:
						new_state = new_state.union(g.pos_pos)

		if len(state) == len(new_state):
			return float("inf")
		
		state = new_state
		hmax+= 1

	return hmax

def getPlan(initial_state, actions, positive_goals, negative_goals, heuristic):
	l_applicable = lambda a : a.applicable(state)

	from queue import PriorityQueue as PQ
	explored = set([])
	states = PQ()

	target = Clause(
			"goal state",
			(positive_goals,negative_goals),
			"",
			state=initial_state
		)

	states.put((0,0,initial_state,[]))
	print (target)

	while not states.empty():
		cost, count, state, plan = states.get()

		# if any(["has R" in x for x in state]):
		# 	print (state)

		if target.applicable(state):
			# print ('LEAVING FROM SUCCESS')
			return (True,plan)

		possible_actions = []
		for a in actions:
			a.state = state
			for grounded in a.ground(state, axis=1):
				if grounded not in possible_actions:
					possible_actions.append(grounded)

					for new_grounded in grounded.ground(target):
						if new_grounded not in possible_actions: 
							possible_actions.append(new_grounded)

		# for a in possible_actions:
		# 	print ('============')
		# 	print (a)
		# 	print ('============')

		# print ("Found {} possible actions".format(len(filter(l_applicable,possible_actions))))

		#Take a look at applicable
		for a in filter(l_applicable,possible_actions):
			new_state = state.union(a.pos_pos).difference(a.neg_pos)

			# print ('===================================')
			# print (state,a.state,sep='\n')
			# print (a.name)
			# print ('Old ->', a.pos_pos)
			# print ('New ->', a.neg_pos)
			# print ('From ->', state)
			# print ('To ->', new_state)
			# print ('===================================')

			key = frozenset(new_state)

			if key in explored:
				# print ('Already explored!')
				continue

			# print (new_state)
			explored.add(key)

			# print('--------------------------------------------------------')
			# print ('Old -> ')
			# print ([x for x in state if 'at' in x and 'self' in x])
			# print('--------------------------------------------------------')
			# new_cost = cost + heuristic(actions,new_state,positive_goals,negative_goals)
			new_cost = cost + len(plan) + 1
			# print (new_cost, [x for x in state if 'has' in x])
			# new_cost = (cost+1)*(1-target.applicable(new_state))

			# new_cost = target.applicable(new_state)
			if new_cost == float("inf"):
				continue

			count += 1
			new_plan = plan + [a]
			states.put((new_cost,count,new_state,new_plan))
		# input('')
		print('cycle done', states.qsize(), len(explored), sep='\t\t')
		# input('')

	# print ('LEAVING FROM FAILURE')
	#add case of failure, what was the closest it got
	return (False,[[]])

class Planner:
	def __init__(self,getPlan=getPlan,h=h):
		self.planner = getPlan
		self.h = h

	def getPlan(self,initial_state, actions, positive_goals, negative_goals):
		# print ([type(x) for x in [initial_state, actions, positive_goals, negative_goals]])
		# setfy = lambda x : x if type(x) is set else toSet(applyBindings(x,{},actions[0].functions,initial_state))
		setfy = lambda x : x if type(x) is set else toSet(x,{"bindings":{},"functions":actions[0].functions,"state":initial_state})
		eval_initial_state = setfy(initial_state)
		eval_positive_goals = setfy(positive_goals)
		eval_negative_goals = setfy(negative_goals)
		# print (eval_initial_state)
		return self.planner(eval_initial_state, actions, eval_positive_goals, eval_negative_goals, self.h)


if __name__ == "__main__":
	p = Planner()

	from EnvManager import *

	env = {"self" : [1,1], "walls" : 	[(0,0),(0,1),(0,2),
										 (1,0)		,(1,2),
										 (2,0)		,(2,2),
										 (3,0)		,(3,2),
										 (4,0)		,(4,2),
										 (5,0)		,(5,2),
										 (6,0)		,(6,2),
										 (7,0)		,(7,2),
										 (8,0),(8,1),(8,2)],
			"objects":{"box" : (7,1)}
		}

	## PLANNING DOES NOT CHANGE ENV, THUS NEVER FREEING A PREVIOUSLY OCCUPIED SPACE
	functions = {
		"free" 	: lambda _state, _env=env : lambda x, y=_env, z=_state : state_free(x,y,z),
		"close" : lambda _state : lambda x, y : close(x,y),
		"up"	: lambda _state : lambda x : up(x),
		"down"	: lambda _state : lambda x : down(x),
		"left"	: lambda _state : lambda x : left(x),
		"right"	: lambda _state : lambda x : right(x),
	}

	c = [
		Clause(
			"pick",
			Contract_pick()["pre"],
			Contract_pick()["pos"],
			functions
		),
		Clause(
			"drop",
			Contract_drop()["pre"],
			Contract_drop()["pos"],
			functions
		),
	]

	initial_state = "at [1,1] self and hands_free"
	for d in ["up","down","left","right"]:
		c.append(
			Clause(
				"step-"+d,
				Contract_step(d)["pre"],
				Contract_step(d)['pos'],
				functions
			)
		)

		initial_state += " and current {} {}-self".format(eval("{}({})".format(d,env["self"])),d)

	for obj, coord in env['objects'].items():
		initial_state += " and at {} {}".format(list(coord), obj)

	target = "at [7,1] self and has box"

	found,plan = p.getPlan(initial_state,c,target,"")
	if found:
		for act in plan:
			print (act.name)

		from act import ActionMaker
		a = ActionMaker(
				{"step-down":stepDict('down'), "pick" : pickDict()},
				{"step-down":lambda e=env : step(env,"down"), "pick" : lambda x, y=env : pick(x,y)},
			)
		# print (clauseListToDictList(a, plan))
	else:
		print ("Failed")