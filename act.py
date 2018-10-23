from PIL import Image
import darknet.darknet as dnet

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
			"name":"crop"}

def paste(img,coord,obj):
	size = (coord[2]-coord[0], coord[3]-coord[1])

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
			"name":"paste"}

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
								# 	"par":"img,coord1,coord2"
								# 	}
								# }
		self.learned_contracts = []

		#self.net = dnet.getNet()
		#self.meta = dnet.getMeta()


	def joinDicts(self, d1,d2, rename=[],distinct=[],return_name=["img","img"]):
		d1["step"] = d1["step"].replace("return", return_name[0])
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

		for atual,target in rename:
			if type(target) == int:
				f = getSplits(f1,0)[target]
			else:
				f = target

			f2 = f2.replace(atual+"___",f+"___")
			if atual not in f1:
				pars.remove(atual)

		pars = ','.join(pars)


		assign1 = getSplits(f1,0)
		assign2 = getSplits(f2,0)

		calls1 = getSplits(f1,1)
		calls2 = getSplits(f2,1)

		# for i,c in enumerate(assign2):
		# 	if c in assign1:
		# 		assign2[i] = "im{}".format(str(img_count))
		# 		print assign2
		# 		img_count += 1
		# 		calls2 = map(lambda x : x.replace(c+"___",assign2[i]+"___"),calls2)

		join = lambda l1,l2: map(lambda (x, y): x+"="+y,zip(l1,l2))
		functs = ';'.join([';'.join(join(assign1,calls1)),';'.join(join(assign2,calls2))])

		#arruma contracts
		contracts = None

		return {
			"step" : functs,
			"contract" : contracts,
			"par" : pars,
			"name" : "custom"
		}

	def toFunction(self,op):
		try:
			return self.known_actions[op]
		except:
			try:
				return self.learned_actions[op]
			except:
				return None

	def createNew(self,line,goal,img,imgpath,aName,det=None):
		import solve

		clauses = []
		l_append = lambda dict : map(lambda (f, d) : clauses.append(solve.Clause(f,d["contract"]["pre"],d["contract"]["pos"])), dict.items())

		l_append(self.known_actions)
		l_append(self.learned_actions)

		assert len(clauses) == len(self.known_actions)+len(self.learned_actions)

		if det is None:
			det = dnet.detectBB(self.net, self.meta, imgpath)

		asLogic = set([])
		for k,coord in det.items():
			asLogic.add("at {} {}".format(str(coord).replace(" ",""),k))
			goal = goal.replace("?"+k, str(coord).replace(" ",""))
		target = solve.Clause("goal",goal,"")

		found,plan = solve.getPlan(asLogic,clauses,target.pos_pre,target.neg_pre)

		if found:
			self.learned_actions[aName] = solve.clauseListToDictList(self,plan)
			return self.execute(line.replace("noop",aName), img,imgpath,det=det)

		return None

	def execute(self,line,img,imgpath,det=None):
		args = line.split("___")
		command = args[0]
		del args[0]
		
		fdict = self.toFunction(command)

		if fdict == None:
			return None

		if det == None:
			det = dnet.detectBB(self.net, self.meta, imgpath)

		for i,arg in enumerate(args):
			if arg in det:
				args[i] = det[arg]
			else:
				args[i] = eval(arg)

		args = [img]+args

		return self.runDict(fdict,args)

	def runDict(self,funcDict,par):
		pars = funcDict["par"].split(",")
		assert len(par) == len(pars)

		var = {}

		for i in range(len(par)):
			label = pars[i]
			val = par[i]

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
		res = actor.createNew("noop___dog___horse", "at ?horse dog and at ?dog horse", im, img, "swap",dets)
		# coord = [0,0, im.size[0],im.size[1]]
		# res = actor.execute("crop___"+str(coord),im)

		if res!=None:
			res.show()