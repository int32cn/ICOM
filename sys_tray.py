#encoding:utf-8
''' Flash windows tray icon sample code '''

from Tkinter import Tk, Menu
import tkMessageBox
import os
import time
import threading

icon_state = False    # Show icon0 when False, else show icon1 
tray_root_menu = None
tray_menu = None
show_main_menu_callback = None

def flash_icon(root,icon):
	global icon_state
	print (root,icon)
	while True:
		root.tk.call('winico', 'taskbar', 'modify', icon,
					'-pos', int(not icon_state), '-text', u'Flash Icon APP')
		icon_state = not icon_state
		time.sleep(0.5)

def menu_func(event, x, y):
	if event == 'WM_RBUTTONDOWN':    # Right click tray icon, pop up menu
		tray_menu.tk_popup(x, y)
	elif event == 'WM_LBUTTONDOWN' or event == 'WM_LBUTTONDBLCLK': # (double) click tray icon, pop up main menu
		if show_main_menu_callback is not None:
			show_main_menu_callback()
		tray_root_menu.deiconify()
	#else: #WM_LBUTTONDBLCLK
	#	print ('event:%s\n'%event)
		
def say_hello():
	tkMessageBox.showinfo('msg', 'you clicked say hello button.')

class win_sys_tray():
	def __int__(self):
		self.__root = None
		self.__sysTray = None
		self.__trayIcons = None
		self.__tips_title = None
	def sys_tray_init(self,tips_title,root,icon_path,show_callback,ports_change_refresh,quit_callback=None):
		global tray_menu
		global show_main_menu_callback
		show_main_menu_callback = show_callback
		if root is None:
			root = Tk()
		self.__root = root
		self.__tips_title = tips_title
		if icon_path is None:
			icon_path = os.path.join(os.getcwd(), 'earth.ico')
		#print (root,icon_path)
		root.tk.call('package', 'require', 'Winico')
		self.__trayIcons = root.tk.call('winico', 'createfrom', icon_path)    # New icon resources
		tray_menu = Menu(root, tearoff=0)
		tray_menu.add_command(label='Test Hello', command=say_hello)
		if quit_callback is None:
			tray_menu.add_command(label='Quit', command=root.quit)
		else:
			tray_menu.add_command(label='Quit', command=quit_callback)
		#thread_param = (root,icon)
		#t = threading.Thread(target=flash_icon,args=thread_param)    # Create a new thread
		#t.setDaemon(True)
		#t.start()
		
		#root.withdraw()
		
	def sys_tray_stay(self):
		self.__root.withdraw()
		global tray_root_menu
		tray_root_menu = self.__root
		self.__root.tk.call('winico', 'taskbar', 'add', self.__trayIcons,
					 '-callback', (self.__root.register(menu_func), '%m', '%x', '%y'),
					 '-pos',0,
					 '-text',self.__tips_title)

	def sys_tray_quit(self):
		self.__root.tk.call('winico', 'taskbar', 'del', self.__trayIcons)
		
	def sys_tray_leave(self):
		self.__root.tk.call('winico', 'taskbar', 'del', self.__trayIcons)
		self.__root.deiconify()
		
	def sys_tray_loop(self):
		self.__root.mainloop()
	
if __name__ == '__main__':
	root,icon = sys_tray_init()
	sys_tray_stay(root,icon,'tray demo',None)
	time.sleep(5)
	#sys_tray_leave(root,icon)
	
	root.mainloop()