
try:
	from Tkinter import *
except:
	from tkinter import *

class GUI:
	def __init__(self,win_size_str=None):
		self.root = Tk()
		self.root.title('criterion S')
		self.__tips_msg_var = StringVar()
		self.__tips_msg_var.set('')
		self.__tips_var = StringVar()
		self.__tips_var.set('   Srxlev     =    Qrxlevmeas   -  (  Qrxlevmin     +   Qrxlevminoffset    ) -  Pcompensation')
		self.__Srxlev = StringVar()
		self.__Srxlev.set('')
		self.__Qrxlevmeas = StringVar()
		self.__Qrxlevmeas.set('')
		self.__Qrxlevmin = StringVar()
		self.__Qrxlevmin.set('')
		self.__Qrxlevminoffset = IntVar()
		self.__Qrxlevminoffset.set(0)
		self.__Pcompensation = IntVar()
		self.__Pcompensation.set(0)
		
		self.__tips_var2 = StringVar()
		self.__tips_var2.set('   Squal    =    Qqualmeas   -  (  Qqualmin    +   Qqualminoffset ) ')
		self.__Squal = StringVar()
		self.__Squal.set('')
		self.__Qqualmeas = StringVar()
		self.__Qqualmeas.set('')
		self.__Qqualmin = IntVar()
		self.__Qqualmin.set(-999)
		self.__Qqualminoffset = IntVar()
		self.__Qqualminoffset.set(0)
		
		self.__tips_msg = Frame(self.root, borderwidth=0)
		self.__desc_frame = Frame(self.root, borderwidth=0)
		self.__input_frame = Frame(self.root, borderwidth=0)
		self.__check_frame = Frame(self.root, borderwidth=0)
		
		self.__desc_frame2 = Frame(self.root, borderwidth=0)
		self.__input_frame2 = Frame(self.root, borderwidth=0)
		self.__check_frame2 = Frame(self.root, borderwidth=0)
		
		lb=Entry(self.__tips_msg, relief='flat', state='readonly', bd=0, textvariable=self.__tips_msg_var, takefocus=0, highlightthickness=0,justify=CENTER)
		lb.pack(side=TOP,fill=BOTH,expand=1)
		
		self.__tips_msg.pack(side=TOP,fill=BOTH,expand=0)
		if win_size_str is not None:
			self.root.geometry(win_size_str)
		
	def ShowSrxlevPanel(self):
		lb=Entry(self.__desc_frame, relief='flat', state='readonly', bd=0, textvariable=self.__tips_var, takefocus=0, highlightthickness=0,justify=LEFT)
		lb.pack(side=TOP,fill=BOTH,expand=1)
		
		ety=Entry(self.__desc_frame, width=7, state='readonly', bd=1, textvariable=self.__Srxlev, justify=CENTER)
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame, width=4, bd=1, text=r'=', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame, width=10, bd=1, textvariable=self.__Qrxlevmeas, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qrxlevmeas is Measured cell RX level value (RSRP),find it in *PHY_CELL_SEARCHING_IND message of balong. Qrxlevmeas=sRsrp/8':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame, width=4, bd=1, text=r'/8 - (', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame, width=8,bd=1, textvariable=self.__Qrxlevmin, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qrxlevmin should exist in cell SIB1 message. Qrxlevmin = cellSelectionInfo->q-RxLevMin':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame, width=5, bd=1, text=r'*2 +', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame, width=12,bd=1, textvariable=self.__Qrxlevminoffset, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qrxlevminoffset maybe exist in cell SIB1 message(default 0). Qrxlevmin = cellSelectionInfo->q-RxLevMinOffset':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame, width=5, bd=1, text=r'*2 ) -', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame, width=10,bd=1, textvariable=self.__Pcompensation, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Pcompensation = max(PEMAX – PPowerClass, 0), in most product it is 0':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		
		bn = Button(self.__check_frame, text='Calulate', borderwidth=1, width=10)
		bn.bind('<Button-1>', lambda event: self.calulateSrxlev())
		bn.pack(side=TOP)
		
		self.__desc_frame.pack(side=TOP,fill=X,expand=1)
		self.__input_frame.pack(side=TOP,fill=X,expand=1)
		self.__check_frame.pack(side=TOP,fill=BOTH,expand=1)

	def ShowSqualPanel(self):
		lb=Entry(self.__desc_frame2, relief='flat', state='readonly', bd=0, textvariable=self.__tips_var2, takefocus=0, highlightthickness=0,justify=LEFT)
		lb.pack(side=TOP,fill=BOTH,expand=1)
		
		ety=Entry(self.__desc_frame2, width=7, state='readonly', bd=1, textvariable=self.__Squal, justify=CENTER)
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame2, width=4, bd=1, text=r'=', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame2, width=10, bd=1, textvariable=self.__Qqualmeas, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qqualmeas is Measured cell quality value (RSRQ), find it in *PHY_CELL_SEARCHING_IND message of balong. Qqualmeas=sRsrq':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame2, width=4, bd=1, text=r'- (', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame2, width=8,bd=1, textvariable=self.__Qqualmin, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qqualmin is Minimum required quality level in the cell,(deault value of negative infinity),Qqualmin = CellSelectionInfo-v920->q-QualMin':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame2, width=4, bd=1, text=r'+', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		ety=Entry(self.__desc_frame2, width=12,bd=1, textvariable=self.__Qqualminoffset, justify=CENTER)
		ety.bind('<FocusIn>',lambda event,tips='Qqualminoffset is optional(default 0), Qqualminoffset =  CellSelectionInfo-v920->q-QualMinOffset':self.show_info(tips))
		ety.pack(side=LEFT,fill=X,expand=0)
		lb=Label(self.__desc_frame2, width=4, bd=1, text=r') ', justify=LEFT)
		lb.pack(side=LEFT,fill=X,expand=0)
		
		bn = Button(self.__check_frame2, text='Calulate', borderwidth=1, width=10)
		bn.bind('<Button-1>', lambda event: self.calulateSqual())
		bn.pack(side=TOP)
		
		self.__desc_frame2.pack(side=TOP,fill=X,expand=1)
		self.__input_frame2.pack(side=TOP,fill=X,expand=1)
		self.__check_frame2.pack(side=TOP,fill=BOTH,expand=1)
	def calulateSrxlev(self):
		'''Srxlev    =   Qrxlevmeas   -  (  Qrxlevmin     +   Qrxlevminoffset    ) -  Pcompensation'''
		try:
			Qrxlevmeas = int(self.__Qrxlevmeas.get())
			Qrxlevmin = int(self.__Qrxlevmin.get())
			Qrxlevminoffset = int(self.__Qrxlevminoffset.get()) * 2
			Pcompensation = int(self.__Pcompensation.get())
			if  Qrxlevmeas < -100:
				Srxlev = Qrxlevmeas / 8   -  (  Qrxlevmin * 2     +   Qrxlevminoffset * 2    ) -  Pcompensation
				self.show_info( "%d/8 - (%d*2 + %d*2) - %d = %d" %(Qrxlevmeas,Qrxlevmin,Qrxlevminoffset,Pcompensation,Srxlev) )
			else:
				Srxlev = Qrxlevmeas   -  (  Qrxlevmin * 2     +   Qrxlevminoffset * 2    ) -  Pcompensation
				self.show_info( "%d - (%d*2 + %d*2) - %d = %d" %(Qrxlevmeas,Qrxlevmin,Qrxlevminoffset,Pcompensation,Srxlev) )
			self.__Srxlev.set('%d'%Srxlev)
		except:
			self.__Srxlev.set('')
			self.show_info( 'error,please check input' )
	
	def calulateSqual(self):
		'''   Squal    =    Qqualmeas   -  (  Qqualmin    +   Qqualminoffset ) '''
		try:
			Qqualmeas = int(self.__Qqualmeas.get())
			Qqualmin = int(self.__Qqualmin.get())
			Qqualminoffset = int(self.__Qqualminoffset.get())
			Squal = Qqualmeas   -  (  Qqualmin    +   Qqualminoffset )
			self.show_info( "%d - (%d + %d) = %d" %(Qqualmeas,Qqualmin,Qqualminoffset,Squal) )
			self.__Squal.set('%d'%Squal)
		except:
			self.__Squal.set('')
			self.show_info( 'error,please check input' )
	
	def testUI(self):
		for bdw in range(5):
			setattr(self, 'of%d' % bdw, Frame(self.root, borderwidth=0))
			Label(getattr(self, 'of%d' % bdw),
				  text='borderwidth = %d  ' % bdw).pack(side=LEFT)
			for relief in [RAISED, SUNKEN, FLAT, RIDGE, GROOVE, SOLID]:
				print(getattr(self, 'of%d' % bdw))
				Button(getattr(self, 'of%d' % bdw), text=relief, borderwidth=bdw,
					   relief=relief, width=10,
					   command=lambda s=self, r=relief, b=bdw: s.prt(r,b))\
						  .pack(side=LEFT, padx=7-bdw, pady=7-bdw)
			getattr(self, 'of%d' % bdw).pack()


	def show_info(self, msg):
		self.__tips_msg_var.set(str(msg))


myGUI = GUI('620x400')
myGUI.ShowSrxlevPanel()
myGUI.ShowSqualPanel()
myGUI.testUI()
myGUI.root.mainloop()

