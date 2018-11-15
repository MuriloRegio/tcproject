import os
import sys
try:
	from tkinter import *
	import tkinter.messagebox
	from tkinter.filedialog import askopenfilename
except:
	from Tkinter import *
	import tkMessageBox
	from tkFileDialog import askopenfilename
from PIL import Image, ImageTk

import thread
import time
import Queue

import darknet.darknet as dnet


class cGUI:
	def __init__(self,queue):
		self.pending = []
		self.coordinates = []
		self.file = None
		self.image = None
		self.unresized_image = None
		self.dets = None

		self.queue = queue

		self.mGui = Tk()
		self.mGui.title('Photo Filters')
		self.mGui.geometry('500x500')
		#self.mGui.resizable(0, 0) #Disable Resizeability
		photoFrame = Frame(self.mGui, bg="black", width=500, height=500)
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

		#Menu Bar
		menubar = Menu(self.mGui)
		filemenu = Menu(menubar)
		#Create the Menu Options that go under drop down
		filemenu.add_command(label="New")
		filemenu.add_command(label="Open", command=self.get_img)
		filemenu.add_command(label="Close", command=self.g_quit)
		#Create the Main Button (e.g file) which contains the drop down options
		menubar.add_cascade(label="File", menu=filemenu)
		self.mGui.config(menu=menubar)


		ws = self.top.winfo_screenwidth() # width of the screen
		hs = self.top.winfo_screenheight() # height of the screen
		w = 400 # width for the Tk root
		h = 325 # height for the Tk root
		# calculate x and y coordinates for the Tk root window
		x = (2*ws/3) - (w/2)
		y = (hs/2) - (h/2)

		self.top.geometry('%dx%d+%d+%d' % (w, h, x, y))

		self.top.after(100, self.process_queue)

		print "Loading Network..."
		self.net = dnet.getNet()
		self.meta = dnet.getMeta()

	def process_queue(self):
		try:
			msg = self.queue.get(0)
			
			if type(msg) is str:
				for m in msg.split("\\n"):
					self.send(custom_msg=m)
			elif msg == "None":
				self.send(custom_msg="Sorry, i couldn't do that")
			elif msg is None:
				self.open_img(self.image, False)
			else:
				if type(msg) is list:
					self.save(msg[0])
				else:
					self.open_img(msg, False)
		except Queue.Empty:
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

	def getPendingMessages(self):
		return self.pending

	def on_closing(self, event=None):
		"""This function is to be called when the window is closed."""
		self.top.quit()

	def g_quit(self):
		mExit=tkMessageBox.askyesno(title="Quit", message="Are You Sure?")
		if mExit:
			self.mGui.quit()
			return

	#open menu
	def get_img(self):
		self.file = askopenfilename(initialdir='D:/Users/')

		if len(self.file) == 0:
			return

		pil_image = Image.open(self.file)
		
		if "data/person.jpg" in self.file:
			with open("example_person_dets.dat",'r') as infile:
				self.dets = eval(infile.read())
		else:
			self.dets = dnet.detectBB(self.net, self.meta, self.file)

		self.open_img(pil_image)


	def open_img(self,pil_image, update_img = True):
		w_box = 500
		h_box = 500

		w, h = pil_image.size

		pil_image_resized = self.resize(w, h, w_box, h_box, pil_image)
		# wr, hr = pil_image_resized.size

		if update_img:
			self.image = pil_image_resized

		tk_image = ImageTk.PhotoImage(pil_image_resized)

		self.label2.config(image=tk_image, width=w_box, height=h_box)
		self.label2.tk_image = ImageTk.PhotoImage(pil_image_resized)
		self.label2.config(image=self.label2.tk_image, width=w_box, height=h_box)
		self.label2.bind("<Button-1>", self.mouse_click)
		self.label2.pack()

	def resize(self,w, h, w_box, h_box, pil_image):
		'''
		resize a pil_image object so it will fit into
		a box of size w_box times h_box, but retain aspect ratio
		'''
		self.unresized_image = pil_image
		f1 = 1.0*w_box/w  # 1.0 forces float division in Python2
		f2 = 1.0*h_box/h
		factor = min([f1, f2])
		#print(f1, f2, factor)  # test
		# use best down-sizing filter
		width = int(w*factor)
		height = int(h*factor)

		ws = self.top.winfo_screenwidth() # width of the screen
		hs = self.top.winfo_screenheight() # height of the screen
		x = (ws/3) - (width/2)
		y = (hs/2) - (height/2)

		self.mGui.geometry('%dx%d+%d+%d' % (width, height, x, y))

		return pil_image.resize((width, height), Image.ANTIALIAS)

	def mouse_click(self,event):
		self.coordinates.append((event.x,event.y))

	def save(self,img):
		self.open_img(img)
		img.save("data/temp.jpg")
		self.file = "data/temp.jpg"

	def revert(self):
		self.open_img(self.image)


def getThisCoords(gui):
	while len(gui.coordinates)<2:
		pass
	c1, c2 = gui.coordinates[:2]

	del gui.coordinates[0]
	del gui.coordinates[1]

	op = lambda x, y: [min,max][x](c1[y],c2[y])

	#		   xmin,    ymin,    xmax,    ymax
	return (op(0,0), op(0,1), op(1,0), op(1,1))

class Goalfy:
	def __init__(self, dets):
		self.dets = dets

	def formatGoal(self,goal):
		for k,coord in self.dets.items():
			goal = goal.replace("?"+k, str(coord).replace(" ",""))
		return goal

def getMessages(gui,send):
	from agent import bot
	from copy import copy
	agt = bot(send)
	pending = gui.getPendingMessages()

	while 1:
		time.sleep(1) # in seconds
		if len(pending)>0:
			args = copy(gui.dets)
			args["formatGoal"] = Goalfy(gui.dets) # a class that implements a method "formatGoal" with arity 1

			fixed = [gui.unresized_image]

			state = set([])
			for k,coord in gui.dets.items():
				state.add("at {} {}".format(str(coord).replace(" ",""),k))

			line = pending[0]
			del pending[0]

			agt.proccessAnswer(line,state,(fixed,args))
			#	(fixed,args) ::
			#	args -> derivated from user speech
			#	fixed -> through other means, e.g., a GUI


if __name__ == "__main__":
	queue = Queue.Queue()

	gui = cGUI(queue)
	gui.send(custom_msg = "Hello World!")

	thread.start_new_thread(getMessages,(gui,queue))


	gui.mGui.mainloop()