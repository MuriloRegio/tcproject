from PIL import Image
import Recognition.darknet.darknet as dnet

def crop(img,coord):
	return img.crop(coord)

def cropContract(coord,label):
	return {
		"pre" : "at {} {}".format(str(coord),label),
		"pos" : "(not at {} {}) and (has {})".format(str(coord),label,label)
	}

def paste(img,coord,obj):
	size = (coord[2]-coord[0], coord[3]-coord[1])

	res_obj = obj.resize(size, Image.ANTIALIAS)

	img.paste(img1,coord2[0:2])

	return img

class ActionMaker():
	def __init__(self,netpath):
		self.known_actions = ["crop", "paste"]
		self.learned_actions = {"swap":{
									"step":"im1=crop(img___,coord1___);img2=crop(img___,coord2___);img3=paste(img___,coord2___,img1___);img4=paste(img3___,coord1___,img2___)",
									"contract":{	
												"pre":"(at {} {}) and (at {} {})",#.format(str(coord1),label1,str(coord2),label2),
												"pos":"(at {} {}) and (at {} {})" #.format(str(coord1),label2,str(coord2),label1)
											},
									"par":"img,coord1,coord2"
									}
								}
		self.learned_contracts = []

		self.netpath = netpath
		self.net = dnet.load_net(netpath+"cfg/yolov3.cfg", netpath+"yolo.weights", 0)
		self.meta = dnet.load_meta(netpath+"cfg/coco.data")


	def joinDicts(self, d1,d2,img_count, carry=None,distinct=None):
		if "return" in d1["step"]:
			d1["step"] = d1["step"].replace("return", "im{}".format(str(img_count)))
			img_count += 1
		if "return" in d2["step"]:
			d2["step"] = d2["step"].replace("return", "im{}".format(str(img_count)))
			img_count += 1

		getSplits = lambda x, k : [y.split("=")[k] for y in x.replace(" ","").split(";")]

		f1 = d1["step"].replace(" ","")
		f2 = d2["step"].replace(" ","")

		pars = d1["par"].split(",")
		for par in d2["par"].split(","):
			for elem in distinct:
				if par is elem:
					f1 = f1.replace(par+"___", par+"1___")
					f2 = f2.replace(par+"___", par+"2___")

					pars.remove(par)
					par = par+"2"
					pars.append(par+"1")

			if carry is not None:
				try:
					start = f1.rindex(";")
				except:
					start = 0
				end = f1.rindex("=")

				result = f1[start:end]

				f2 = f2.replace(carry,result)

			if par not in pars:
				pars.append(par)


		pars = ','.join(pars)


		assign1 = getSplits(f1,0)
		assign2 = getSplits(f2,0)

		calls1 = getSplits(f1,1)
		calls2 = getSplits(f2,1)

		for i,c in enumerate(assign2):
			if c in assign1:
				assign2[i] = "im{}".format(str(img_count))
				img_count += 1
				calls2 = map(lambda x : x.replace(c+"___",assign2[i]+"___"),calls2)

		join = lambda l1,l2: map(lambda (x, y): x+"="+y,zip(l1,l2))
		functs = ';'.join([';'.join(join(assign1,calls1)),';'.join(join(assign2,calls2))])

		#arruma contracts
		contracts = None

		return {
			"step" : functs,
			"contract" : contracts,
			"par" : pars
		}

	def toFunction(self,op):
		if op == "crop":
			return {"step":"return = crop(img___,coord___)",
					"contract":cropContract,
					"par":"img,coord"}

		elif op == "paste":
			return {"step":"return = paste(img___,coord___,obj___)",
					"contract":pasteContract,
					"par":"img,coord,obj"}
		return None

	def toCustomFunction(self,op):
		try:
			return self.learned_actions[op]
		except:
			return None

	def execute(self,line,img,imgpath):
		args = line.split("___")
		command = args[0]
		del args[0]

		if command == "noop":
			#trata construir uma nova acao
			pass

		det = dnet.detectBB(self.net, self.meta, imgpath)

		for i,arg in enumerate(args):
			if arg in det:
				args[i] = det[arg]
			else:
				args[i] = eval(arg)

		args = [img]+args

		fdict = self.getFunctDict(command)

		assert fdict is not None

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

			for label in var:
				func_par = label+"___"
				if func_par in command:
					command = 	command.replace(func_par,"var['{}']".format(label))

			var[assign] = eval(command)

		return var[assign]


	def getFunctDict(self,funct):
		funcDict = self.toFunction(funct)

		if funcDict == None:
			funcDict = self.toCustomFunction(funct)

		return funcDict

if __name__ == "__main__":
		netpath = "./"
		actor = ActionMaker(netpath)

		print actor.joinDicts(
				actor.toFunction("crop"),
				actor.toFunction("crop"),
				1
			)

		#img = netpath+"data/dog.jpg"

		#im = Image.open(img)

		#res = actor.execute("crop___dog",im,img)
		# coord = [0,0, im.size[0],im.size[1]]
		# res = actor.execute("crop___"+str(coord),im)

		#res.show()