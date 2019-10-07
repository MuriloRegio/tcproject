from OLD import *
import numpy as np

try:
	from tkinter import *
	import tkinter.messagebox
except:
	from Tkinter import *
	import tkMessageBox

from OLD import *
from PIL import Image, ImageTk
import EnvManager as em
import time

import queue

class GUI:
	def __init__(self, env):
		self.env = env
		self.pending = []
		self.queue = queue.Queue()

		gui_dims = map(lambda x : x * env.img_scale, env.size)

		self.mGui = Tk()
		self.mGui.title('Environment Perception')
		# self.mGui.geometry('x'.join(map(str,gui_dims)))
		photoFrame = Frame(self.mGui, bg="black", width=gui_dims[1], height=gui_dims[0])
		photoFrame.pack()
		self.label2 = Label(photoFrame)

		self.top = Tk()
		self.top.title("Chatter")
		messages_frame = Frame(self.top)
		scrollbar = Scrollbar(messages_frame)  # To navigate through past messages.
		# Following will contain the messages.
		self.msg_list = Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.msg_list.pack(side=LEFT, fill=BOTH)
		self.msg_list.pack()
		messages_frame.pack()

		self.entry_field = Entry(self.top)
		self.entry_field.bind("<Return>", self.send)
		self.entry_field.pack()
		send_button = Button(self.top, text="Send", command=self.send)
		send_button.pack()

		self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.mGui.protocol("WM_DELETE_WINDOW", self.on_closing)

		self.top.after(100, self.process_queue)
		self.top.after(100, self.update_img)

		ws = self.top.winfo_screenwidth() # width of the screen
		hs = self.top.winfo_screenheight() # height of the screen
		w = 400 # width for the Tk root
		h = 325 # height for the Tk root
		# calculate x and y coordinates for the Tk root window
		x = (4*ws/5) - (w/3)
		y = (hs/2) - (h/2)

		self.top.geometry('%dx%d+%d+%d' % (w, h, x, y))

	def process_queue(self):
		try:
			msg = self.queue.get(0)
			
			if type(msg) is str:
				for m in msg.split("\\n"):
					self.send(custom_msg=m)
			else:
				print (type(msg))
		except queue.Empty:
			pass
		self.top.after(100, self.process_queue)

	def send(self, event=None, custom_msg = None):  # event is passed by binders.
		"""Handles sending of messages."""
		if custom_msg is None:
			msg = self.entry_field.get()
		else:
			msg = custom_msg

		if len(msg) == 0:
			return

		if msg == "{quit}":
			self.top.quit()

		self.msg_list.insert(END,msg)

		if custom_msg is None:
			self.entry_field.delete(0, 'end')
			self.pending.append(msg)
		else:
			self.msg_list.itemconfig(END, {'fg': 'blue','bg': 'gray'})

		self.msg_list.yview(END)                                  	#Set the scrollbar to the end of the listbox
		self.msg_list.pack()

	def update_img(self):
		tk_image = ImageTk.PhotoImage(Image.fromarray(self.env.st))
		h_box, w_box = self.env.st.shape[:2]

		self.label2.config(image=tk_image, width=w_box, height=h_box)
		self.label2.tk_image = tk_image
		# self.label2.tk_image = ImageTk.PhotoImage(pil_image_resized)
		self.label2.config(image=self.label2.tk_image, width=w_box, height=h_box)
		self.label2.pack()
		self.top.after(100, self.update_img)

	def on_closing(self, event=None):
		"""This function is to be called when the window is closed."""
		self.top.quit()
		self.mGui.quit()


class env:
	def __init__(self, file = "environment_description.dat"):
		self.env = em.read_description(file)
		self.colors = { "R" : (255,0,0),"G" : (0,255,0),"B" : (0,0,255),
						"C" : (0,255,255),"M" : (255,255,0),"Y" : (255,0,255) }

		self.img_scale = 32

		self.stickman = np.asarray(Image.open('data/stickman.jpg').resize
							((self.img_scale,self.img_scale), Image.BICUBIC))
		self.stickman = np.expand_dims(self.stickman,2)

		self.draw()
		
	def run(self, command):
		def update(*args):
			# print (args)
			l = apply(eval("em."+command),*args)
			if command == "pick":
				obj, coord = l
				self.update(coord, 255)
				self.update(self.env["self"], self.stickman*self.colors[obj])
			elif command == "drop":
				obj, coord = l
				self.update(coord, self.colors[obj])
				self.update(self.env["self"], self.stickman)
			else:
				self.update(l, 255)
				self.update(self.env["self"], self.stickman)
			
			# cv2.imshow("Environment State", self.st)
			time.sleep(1)
			return l
		return update

	def __call__(self,arg, local = None):
		if local is not None and arg is str and arg in local:
			return local[arg]
		return self.envQuery(arg)

	def update(self, seed, value):
		x,y = map(lambda x : self.img_scale*x, seed)
		
		self.st[x:x+self.img_scale, y:y+self.img_scale] = value
		
	def statefy(self):
		state = "at {} self".format(self.env["self"])

		for obj, coord in self.env["objects"].items():
			state += " and at {} {}".format(list(coord),obj)

		if self.env["has"] is not None:
			state += " and not hands_free and has {}".format(self.env["has"])
		else:
			state += " and hands_free"

		getPos = lambda x, self=self : eval("em.{}(self.env['self'])".format(x))
		for direction in ["up","down","left","right"]:
			state += " and current {} {}-self".format(getPos(direction),direction)

		return state

	def formatGoal(self,goal):
		splits  = goal.split(' and ')
		rewrite = lambda l : ' '.join([x if x not in self.args else self.args[x] for x in l])

		for i,line in enumerate(splits):
			slots = line.split(" ")

			if slots[0] != 'at':
				splits[i] = rewrite(slots)
				continue

			slots[1]  = "{}".format(self.enf["coordinates"][slots[1]])
			splits[i] = rewrite(slots)

		return ' and '.join(splits)

	def envQuery(self,arg):
		if type(arg) is str:
			if arg == "has":
				return self.env["has"]
			pass
		else:
			if arg in self.env["walls"]:
				return "wall"

			if list(arg) == self.env["self"]:
				return "agent"

			for obj in self.env["objects"]:
				if self.env["objects"][obj] == arg:
					return obj

	def draw(self):
		points = [v for v in self.env["walls"]]

		xmax, ymax = map(lambda x : 1+max(x), zip(*points))

		self.size = (xmax,ymax)

		self.st = np.full((self.img_scale*xmax, self.img_scale*ymax, 3), (255,255,255), dtype = np.uint8)

		for i in range(xmax):
			for j in range(ymax):
				cellType = self.envQuery((i,j))

				if cellType is None:
					continue

				if cellType == "wall":
					value = 0
					
				elif cellType == "agent":
					value = self.stickman

				else:
					value = self.colors[cellType]
					# continue

				x, y = i*self.img_scale, j*self.img_scale
				self.st[x:x+self.img_scale,y:y+self.img_scale] = value

def run(GUI, e):
	# from EnvManager import *
	from act import ActionMaker

	# e = env()
	functions = {
		"free" 	: lambda _state, _env=e.env : lambda x, y=_env, z=_state : em.state_free(x,y,z),
		"close" : lambda _state : lambda x, y : em.close(x,y),
		"up"	: lambda _state : lambda x : em.up(x),
		"down"	: lambda _state : lambda x : em.down(x),
		"left"	: lambda _state : lambda x : em.left(x),
		"right"	: lambda _state : lambda x : em.right(x),
	}

	a = ActionMaker(
			{
				"step_down":  em.stepDict('down'), "step_up":    em.stepDict('up'), 
				"step_right":em.stepDict('right'), "step_left":em.stepDict('left'), 
				"pick" :            em.pickDict(), "drop":           em.dropDict()
			},
			{
				"step_down"  : e.run("step_down"), 
				"step_right" : e.run("step_right"), 
				"step_left"  : e.run("step_left"), 
				"step_up"    : e.run("step_up"), 
				"pick"       : e.run("pick"), 
				"drop"       : e.run("drop"), 
			},
			logical_functions = functions
		)



	from agent import bot
	agt = bot(GUI.queue,a)
	pending = GUI.pending

	e.args = {
		"env":e.env, "statefier":e.statefy, "formatGoal": e, 
		"red box":"R", "green box":"G", "blue box":"B", 
	}

	e.env["coordinates"] = {
		"room_1":[3,5],"room_2":[3,15],"room_3":[3,25],
		"room_4":[15,5],"room_5":[15,15],"room_6":[15,25],
		"corridor":[9,15]
	}

	for obj, coord in self.env["objects"].items():
		e.env["coordinates"][obj] = coord


	while 1:
		time.sleep(1)
		if len(pending) > 0:
			msg = pending[0]
			del pending[0]

			agt.proccessAnswer(msg,args)


if __name__ == "__main__":
	e = env()
	gui = GUI(e)

	import _thread
	_thread.start_new_thread(run, tuple([gui, e]))
	# _thread.start_new_thread(test, tuple([]))

	gui.mGui.mainloop()