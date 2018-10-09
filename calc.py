#coding:utf-8 
from Tkinter import *
import time 
root = Tk()

def cacl(input_str):
	ret = 0
	if "x" in input_str: 
		ret = input_str.split("x") 
	return int(ret[0]) * int(ret[1]) 
def callback(n): 
	print n 
def callback1(n): 
	print n 
class App: 
	def __init__(self, master): 
		frame1 = Frame(master) 
		frame1.pack() 
		frame = Frame(master) 
		frame.pack() 
		Button(frame, text="1",command=lambda: callback(1) ).grid(row=0,column=0) 
		Button(frame, text="2",command=lambda: callback(2) ).grid(row=0,column=1) 
		Button(frame, text="3",command=lambda: callback(3) ).grid(row=0,column=2) 
		Button(frame, text="4",command=lambda: callback(4) ).grid(row=1,column=0) 
		Button(frame, text="5",command=lambda: callback(5) ).grid(row=1,column=1) 
		Button(frame, text="6",command=lambda: callback(6) ).grid(row=1,column=2) 
		Button(frame, text="7",command=lambda: callback(7) ).grid(row=2,column=0) 
		Button(frame, text="8",command=lambda: callback(8) ).grid(row=2,column=1) 
		Button(frame, text="9",command=lambda: callback(9) ).grid(row=2,column=2) 
		Button(frame, text="0",command=lambda: callback(0) ).grid(row=3,column=0) 
		Button(frame, text="+",command=lambda: callback1("+") ).grid(row=3,column=1) 
		Button(frame, text="-",command=lambda: callback1("-") ).grid(row=3,column=2) 
		Button(frame, text="*",command=lambda: callback1("*") ).grid(row=4,column=1) 
		Button(frame, text="/",command=lambda: callback1("/") ).grid(row=4,column=2) 
		Button(frame, text="=", command=self.say_hi).grid(row=4,column=0) 
		w = Label(frame1,text="input") 
		w.pack() 
		self.e = Entry(frame1) 
		self.e.pack(padx=5) 
		w1 = Label(frame1,text="result") 
		w1.pack() 
		v = StringVar() 
		e1 = Entry(frame1, textvariable=v) 
		v.set("") 
		self.v = v 
		e1.pack() 
	def say_hi(self): 
		print "hi there, everyone!",self.e.get() 
		input_str = self.e.get() 
		self.v.set(cacl(input_str)) 
app = App(root) 
root.mainloop()