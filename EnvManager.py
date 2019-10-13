# foo.__code__.co_varname
from OLD import *

def read_description(file, walls = '+-|',objs = "RGBCMY",agt = "A"):
	env = {"walls" : [], "objects" : {}, "self" : None, "has" : None, "facing" : "down"}

	with open(file, 'r') as infile:
		for i,line in enumerate(infile.readlines()):
			line = line.replace('\n','')
			for j, c in enumerate(line):
				if c in walls:
					env["walls"].append((i,j))
				elif c in objs:
					env["objects"][c] = (i,j)
				elif c in agt:
					env["self"] = [i,j]
	return env


#----------------------------------
#----- Auxiliar Definitions -------
#----------------------------------

def free(coord, env):
	tmp =  not (tuple(coord) in env["walls"] or \
			tuple(coord) in [v for _,v in env["objects"].items()])
	# print (coord, tmp, list(coord) in env["walls"])
	return tmp

def state_free(coord, env, state):
	# print(coord, list(coord) in env["walls"])
	if tuple(coord) in env["walls"]:
		return False

	for exp in state:
		tokens = exp.split(' ')
		if tokens[0] != 'at':
			continue
		if eval(tokens[1]) == list(coord):
			return False
	# print (coord, tmp, list(coord) in env["walls"])
	return True

def front(env):
	from copy import copy

	coord  = copy(env["self"])
	direct = env["facing"]
	if direct == "up":
		coord[0]-=1
	if direct == "right":
		coord[1]+=1
	if direct == "left":
		coord[1]-=1
	if direct == "down":
		coord[0]+=1
	return coord

def close(coord0, coord1):
	manh = abs(coord0[0] - coord1[0])
	manh += abs(coord0[1] - coord1[1])
	return manh < 2



#--------------------------------
#----- Action Definitions -------
#--------------------------------


#================================================================================
#Pick Action
def pick(obj, env):
	if obj not in env["objects"]:
		raise ValueError("Invalid Object {}".format(obj))
	if not close(env["objects"][obj], env["self"]):
		raise ValueError("Not close enough to pick object {} at {}".format(obj, str(env["objects"][obj])))
	if env["has"] is not None:
		raise ValueError("Cannot pick up {} while holding {}".format(obj,env["has"]))

	was = env["objects"][obj]
	del env["objects"][obj]
	env["has"] = obj
	return (obj, was)

def Contract_pick():
	return {"pre" : "hands_free and at ?coord self and is close(?coord, ?dest) and at ?dest ?obj",
			"pos" : "not hands_free and has ?obj and not at ?dest ?obj"}

def pickDict():
	return {
				"step":"pick(obj___,env___)",
			"contract":Contract_pick(),
				 "par":"obj,env",
				"name":"pick",
			}
#================================================================================

#================================================================================
#Drop Action
def drop(dest, env):
	if env["has"] is None:
		raise ValueError("Cannot drop while not holding anything!")
	if not free(dest, env):
		raise ValueError("Destination is already occupied")
	if not close(dest, env["self"]):
		raise ValueError("Not close enough to drop object {} at {}".format(obj, str(env["objects"][obj])))
	
	obj = env["has"]
	env["objects"][env["has"]] = dest
	env["has"] = None
	
	return (obj, dest)

def Contract_drop():
	return {"pre" : "has ?obj and at ?coord self and is close(?coord, ?dest) and is free(?dest)",
			"pos" : "hands_free and not has ?obj and not is free(?dest) and at ?dest ?obj"}

def dropDict():
	return {
				"step":"drop(dest___,env___)",
			"contract":Contract_drop(),
				 "par":"dest,env",
				"name":"drop",
			}
#================================================================================

#================================================================================
#Step Action
def step(env, direction):
	env["facing"] = direction
	if not free(front(env), env):
		raise ValueError("Path is blocked")

	was = env["self"]
	env["self"] = front(env)
	return was

def Contract_step(direction):
	return {"pre" : "at ?coord self and is free(?coord_{0}) and current ?coord_left left-self and current ?coord_up up-self \
						and current ?coord_right right-self and current ?coord_down down-self".format(direction).replace("\t",""),
			"pos" : "at {0}(?coord) self and current {0}(?coord_left) left-self and current {0}(?coord_up) up-self and \
						current {0}(?coord_right) right-self and current {0}(?coord_down) down-self and \
						not at ?coord self and not current ?coord_left left-self and not current ?coord_up up-self \
						and not current ?coord_right right-self and not current ?coord_down down-self".format(direction).replace("\t","")}

def stepDict(direction):
	return {
				"step":"step_{}(env___)".format(direction),
			"contract":Contract_step(direction),
				 "par":"env",
				"name":"step_{}".format(direction),
			}

def step_up(env):
	return step(env,'up')

def step_left(env):
	return step(env,'left')

def step_right(env):
	return step(env,'right')

def step_down(env):
	return step(env,'down')
#================================================================================



#================================================================================
#All possible step-directions auxiliar functions
def left(coord):
	c = list(coord)
	c[1]-=1
	return c

def right(coord):
	c = list(coord)
	c[1]+=1
	return c

def up(coord):
	c = list(coord)
	c[0]-=1
	return c

def down(coord):
	c = list(coord)
	c[0]+=1
	return c
#================================================================================











def toString(env):
	points = [v for v in env["walls"]]

	xmax, ymax = map(lambda x : 1+max(x), zip(*points))

	st = []
	for _ in range(xmax):
		st.append([])
		for _ in range(ymax):
			st[-1].append('.')

	for (x,y) in points:
		st[x][y] = '+'

	for k,(x,y) in env["objects"].items():
		st[x][y] = k

	x,y = env["self"]
	st[x][y] = 'A'

	return st


if __name__ == "__main__":
	file = "environment_description.dat"
	env = read_description(file)

	print ('\n'.join(map(''.join,toString(env))))
	print ()
	step(env)
	print ('\n'.join(map(''.join,toString(env))))
