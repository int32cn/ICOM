#!/usr/bin/python
# -*- coding= utf-8 -*-
import ctypes
import win32con
from icom_ctrl_msg_id import *

user32 = ctypes.windll.user32
#FindWindow = user32.FindWindowW
#BringWindowToTop = user32.BringWindowToTop
#IsWindowVisible = user32.IsWindowVisible
#IsIconic = user32.IsIconic
#SetForegroundWindow = user32.SetForegroundWindow
#ShowWindow = user32.ShowWindow
#GetWindowText = user32.GetWindowTextW
PostMessage = user32.PostMessageW
GetForegroundWindow = user32.GetForegroundWindow
GetWindowThreadProcessId = user32.GetWindowThreadProcessId

def set_sync_msg_icom_win_title(app_title):
	icom_win_app_title = 'iCOM for Windows'
	icom_win_title = ctypes.create_unicode_buffer(icom_win_app_title)
	#g_icom_win_handle = FindWindow(win32con.NULL,ctypes.byref(icom_win_title))
	del icom_win_title

class win_msg(object):
	def __init__(self,win_pid):
		self.__hwnd = None
		self.__win_pid = win_pid
		self.__send_msg_count = 0
		self.__in_focus = False
	def get_win_handle(self):
		if self.__hwnd:
			return self.__hwnd
		c_pid = ctypes.c_ulong(0)
		focus_win_handle = GetForegroundWindow()
		if focus_win_handle:
			__pid = GetWindowThreadProcessId(focus_win_handle,ctypes.byref(c_pid))
			if self.__win_pid == c_pid.value:
				self.__hwnd = focus_win_handle
		return self.__hwnd
	def is_win_foreground(self,msg_int_type):
		if self.__hwnd:
			if ICOM_CTRL_MSG.ID_TIMER_TIMEOUT == msg_int_type:
				self.__in_focus = True if self.__hwnd == GetForegroundWindow() else False
			return self.__in_focus
		return False
	
	def send_sync_msg(self, msg_para_list):
		msg_int_type = msg_para_list[0]
		hwnd = self.get_win_handle()
		if not hwnd: 
			return False
		if not self.is_win_foreground(msg_int_type):
			return False
		
		if ICOM_CTRL_MSG.ID_TIMER_TIMEOUT == msg_int_type:
			#PostMessage(hwnd,win32con.WM_KEYUP,win32con.VK_F6,0x00000001) #keydown
			PostMessage(hwnd,win32con.WM_KEYUP,win32con.VK_F6,0x00000001|(3<<30)) #keyup
		elif self.__send_msg_count == 0:
			#PostMessage(hwnd,win32con.WM_KEYDOWN,win32con.VK_F5,0x00000001) #key down
			PostMessage(hwnd,win32con.WM_KEYUP,win32con.VK_F5,0x00000001|(3<<30)) #keyup
			#print ('keydown',self.__send_msg_count)
			#self.__send_msg_count = 1
		else:
			PostMessage(hwnd,win32con.WM_KEYUP,win32con.VK_F5,0x00000001|(3<<30)) #keyup
			#print ('keyup',self.__send_msg_count,msg_int_type)
			#self.__send_msg_count = 0
		
		return True
