#!/usr/bin/env python
# Module	 : SysTrayIcon.py
# Synopsis   : Windows System tray icon.
# Programmer : Simon Brunning - simon@brunningonline.net
# Date	   : 11 April 2005
# Notes	  : Based on (i.e. ripped off from) Mark Hammond's
#			  win32gui_taskbar.py and win32gui_menu.py demos from PyWin32
'''TODO

For now, the demo at the bottom shows how to use it...'''
		 
import os
import sys
from win32api import GetSystemMetrics as win32apiGetSystemMetrics
import win32con
import win32gui_struct
import ctypes
import ctypes.wintypes as wintypes 
from threading import Thread, Lock
import time
#try:
import win32gui
#except ImportError:
#import winxpgui as win32gui
import devport
import winip as osip

user32 = ctypes.windll.user32
RegisterDeviceNotification = user32.RegisterDeviceNotificationW
UnregisterDeviceNotification = user32.UnregisterDeviceNotification
#GetWindowText = user32.GetWindowTextW
#GW_HWNDNEXT 2 Returns a handle to the window below the given window.
#GW_HWNDPREV 3 Returns a handle to the window above the given window.

class GUID(ctypes.Structure):
	_pack_ = 1
	_fields_ = [("Data1", ctypes.c_ulong),
				("Data2", ctypes.c_ushort),
				("Data3", ctypes.c_ushort),
				("Data4", ctypes.c_ubyte * 8)]
				
class DEV_BROADCAST_DEVICEINTERFACE(ctypes.Structure):
	_pack_ = 1
	_fields_ = [("dbcc_size",  wintypes.DWORD), 
				("dbcc_devicetype",  wintypes.DWORD), 
				("dbcc_reserved",  wintypes.DWORD), 
				("dbcc_classguid",  GUID), 
				("dbcc_name",  ctypes.c_wchar*260)]

class DEV_BROADCAST_HDR(ctypes.Structure):
	_fields_ = [("dbch_size", wintypes.DWORD),
				("dbch_devicetype", wintypes.DWORD),
				("dbch_reserved", wintypes.DWORD)]


#GUID_DEVCLASS_PORTS = GUID(0x4D36E978, 0xE325, 0x11CE,
#		(ctypes.c_ubyte*8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18))
GUID_DEVINTERFACE_USB_DEVICE = GUID(0xA5DCBF10, 0x6530,0x11D2, 
		(ctypes.c_ubyte*8)(0x90, 0x1F, 0x00,0xC0, 0x4F, 0xB9, 0x51, 0xED))

class SysTrayIcon(object):
	QUIT = 'QUIT'
	SPECIAL_ACTIONS = [QUIT]
	
	FIRST_ID = 1023
	ID_TIMER = 123
	ID_TIMER_FIRST_ONCE = 124
	ID_TIMER_EXTERN = 125
	WM_USER_NOTIFY = 20
	WM_USER_IP_CHANGED = 21
	
	CHANGE_TYPE_PORTS_ARRIVAL = 0
	CHANGE_TYPE_PORTS_REMOVE = 1
	CHANGE_TYPE_IP_ADDR = 2
	
	def __init__(self,
				 instance_num,
				 icon,
				 tray_ctrl_Q,
				 hover_text,
				 menu_options,
				 on_ports_change,
				 on_quit=None,
				 default_menu_index=None,
				 window_class_name=None,realtime=None):
		self._ports_change_count = 0
		self._ports_change_type = ''
		self._ipaddr_change_count = 0
		self._instance_num = instance_num
		self.icon = icon
		self.tray_ctrl_Q = tray_ctrl_Q
		self.__menu_extra = {}
		self.__realtime = realtime if realtime else 0
		self.__dev_change_delay_timer_len = 50 if self.__realtime else 300
		self.hover_text = hover_text
		self._on_ports_change = on_ports_change
		self.on_quit = on_quit
		self._show_main_win_callback = None
		self._keyevent_callback = None
		menu_options = menu_options + (('Quit', None, False, self.QUIT),)
		self._next_action_id = self.FIRST_ID
		self.menu_actions_by_id = dict()
		self.menu_options = self._add_ids_to_menu_options(list(menu_options))
		del self._next_action_id
		
		self.default_menu_index = (default_menu_index or 0)
		self.window_class_name = window_class_name or "SysTrayIconPy"
		self.__extern_timer_callback = None
		self.__extern_timer_cnt = 0
		message_map = {win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
					   #win32con.WM_CREATE: self.onCreate,
					   win32con.WM_TIMER: self.onTimer,
					   win32con.WM_DESTROY: self.destroy,
					   win32con.WM_COMMAND: self.command,
					   #win32con.WM_KEYUP: self.keyup,
					   #win32con.WM_KEYDOWN: self.keydown,
					   win32con.WM_DEVICECHANGE: self.winDeviceEvent,
					   win32con.WM_USER + self.WM_USER_NOTIFY : self.notify,
					   win32con.WM_USER + self.WM_USER_IP_CHANGED : self.onWinIpChangedProc
					   }
		# Register the Window class.
		window_class = win32gui.WNDCLASS()
		hinst = window_class.hInstance = win32gui.GetModuleHandle(None)
		window_class.lpszClassName = self.window_class_name
		window_class.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
		window_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
		window_class.hbrBackground = win32con.COLOR_WINDOW
		window_class.lpfnWndProc = message_map # could also specify a wndproc.
		classAtom = win32gui.RegisterClass(window_class)
		# Create the Window.
		style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
		self.hwnd = win32gui.CreateWindow(classAtom,
										  self.window_class_name,
										  style,
										  0,
										  0,
										  win32con.CW_USEDEFAULT,
										  win32con.CW_USEDEFAULT,
										  0,
										  0,
										  hinst,
										  None)
		self.setupNotification()#sss
		win32gui.UpdateWindow(self.hwnd)
		user32.SetTimer(self.hwnd, self.ID_TIMER_FIRST_ONCE, 100, win32con.NULL);
		self.notify_id = None
		self.refresh_icon()
	def setKeyEventCallback(self,callback):
		self._keyevent_callback = callback
	def keyup(self, hwnd, msg, wparam, lparam):
		print ('keyup',msg,wparam,lparam&0xffff,(lparam>>16)&0xff,(lparam>>24)&0x01,(lparam>>25)&0x0f,(lparam>>29)&0x07)
		if self._keyevent_callback:
			self._keyevent_callback(msg, wparam, lparam)
	def keydown(self, hwnd, msg, wparam, lparam):
		print ('keydown',msg,wparam,lparam&0xffff,(lparam>>16)&0xff,(lparam>>24)&0x01,(lparam>>25)&0x0f,(lparam>>29)&0x07)
		if self._keyevent_callback:
			self._keyevent_callback(msg, wparam, lparam)
	def msgMainLoop(self):
		win32gui.PumpMessages()
	def setShowMainWinCallback(self,callback):
		self._show_main_win_callback = callback
	def setupNotification(self):
		dbh = DEV_BROADCAST_DEVICEINTERFACE()
		dbh.dbcc_size = ctypes.sizeof(DEV_BROADCAST_DEVICEINTERFACE)
		dbh.dbcc_devicetype = win32con.DBT_DEVTYP_DEVICEINTERFACE
		dbh.dbcc_classguid = GUID_DEVINTERFACE_USB_DEVICE #GUID_DEVCLASS_PORTS
		self.hNofity = RegisterDeviceNotification(int(self.hwnd), 
												ctypes.byref(dbh), 
												win32con.DEVICE_NOTIFY_WINDOW_HANDLE)
		if self.hNofity == win32con.NULL:
			print (ctypes.FormatError(), int(self.winId()))
			print ("RegisterDeviceNotification failed")

	def setupExternTimer(self,timeout_ms,callback):
		if timeout_ms > 0 and callback:
			self.__extern_timer_callback = callback
			user32.SetTimer(self.hwnd, self.ID_TIMER_EXTERN, timeout_ms, win32con.NULL);
		
	def winDeviceEvent(self, hwnd, msg, wParam, lParam):
		#print ('winDeviceEvent 0x%x, 0x%x, 0x%x\n'%(msg, wParam, lParam))
		if msg == win32con.WM_DEVICECHANGE:
			self.onDeviceChanged(wParam, lParam)
			
	def SetIpaddrChanged(self,change_type=None):
		win32gui.PostMessage(self.hwnd, win32con.WM_USER + self.WM_USER_IP_CHANGED, self.CHANGE_TYPE_IP_ADDR, 0)
	def onDeviceChanged(self, wParam, lParam):
		if win32con.DBT_DEVICEARRIVAL == wParam:
			self._ports_change_type = 'ARRIVAL'
			self._ports_change_count += 1
			user32.SetTimer(self.hwnd, self.ID_TIMER, self.__dev_change_delay_timer_len, win32con.NULL);
		elif win32con.DBT_DEVICEREMOVECOMPLETE == wParam:
			self._ports_change_type = 'REMOVECOMPLETE'
			self._ports_change_count += 1
			user32.SetTimer(self.hwnd, self.ID_TIMER, self.__dev_change_delay_timer_len, win32con.NULL);
		#if (DBT_DEVICEARRIVAL == wParam or DBT_DEVICEREMOVECOMPLETE == wParam):
			#dbh = DEV_BROADCAST_HDR.from_address(lParam)
			#if dbh.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
				#dbd = DEV_BROADCAST_DEVICEINTERFACE.from_address(lParam)
				#print('name',repr(dbd.dbcc_name))
	def _add_ids_to_menu_options(self, menu_options):
		result = []
		for menu_option in menu_options:
			option_text, option_icon, option_checked, option_action = menu_option
			if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
				item_list = list(menu_option + (self._next_action_id,))
				result.append(item_list)
				#self.menu_actions_by_id.add((self._next_action_id, option_action))
				self.menu_actions_by_id.setdefault(self._next_action_id, item_list)
			elif non_string_iterable(option_action):
				result.append((option_text,
							   option_icon,
							   option_checked,
							   self._add_ids_to_menu_options(option_action),
							   self._next_action_id))
			else:
				print ('Unknown item', option_text, option_icon, option_action)
			self._next_action_id += 1
		return result
		
	def refresh_icon(self):
		if self._instance_num > 0:
			return
		# Try and find a custom icon
		hinst = win32gui.GetModuleHandle(None)
		if os.path.isfile(self.icon):
			icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
			hicon = win32gui.LoadImage(hinst,
									   self.icon,
									   win32con.IMAGE_ICON,
									   0,
									   0,
									   icon_flags)
		else:
			print ("Can't find icon file - using default.")
			hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

		if self.notify_id: message = win32gui.NIM_MODIFY
		else: message = win32gui.NIM_ADD
		self.notify_id = (self.hwnd,
						  0,
						  win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
						  win32con.WM_USER+self.WM_USER_NOTIFY,
						  hicon,
						  self.hover_text)
		win32gui.Shell_NotifyIcon(message, self.notify_id)

	def restart(self, hwnd, msg, wparam, lparam):
		print (' tray tray restart event received')
		self.refresh_icon()
	def onCreate(self, hwnd, msg, wparam, lparam):
		print ('onCreate event received')
	def onWinIpChangedProc(self, hwnd, msg, wparam, lparam):
		self._ipaddr_change_count += 1
		user32.SetTimer(self.hwnd, self.ID_TIMER, self.__dev_change_delay_timer_len, win32con.NULL);
	def onTimer(self, hwnd, msg, wparam, lparam):
		#print (msg, wparam, lparam)
		if wparam == self.ID_TIMER or wparam == self.ID_TIMER_FIRST_ONCE:
			user32.KillTimer(hwnd, wparam);
		try:
			if not self.tray_ctrl_Q.empty():
				ctrl_msg = self.tray_ctrl_Q.get_nowait()
				if ctrl_msg[0] == 'QUIT':
					if self.on_quit: self.on_quit(self)
					win32gui.PostQuitMessage(0) # Terminate the app.
					return
			if wparam == self.ID_TIMER_EXTERN:
				if self.__extern_timer_callback:
					self.__extern_timer_cnt = self.__extern_timer_callback(lparam,self.__extern_timer_cnt)
			elif wparam == self.ID_TIMER_FIRST_ONCE:
				self._ports_change_count = 0
				self._ipaddr_change_count = 0
				self._on_ports_change('IPADDR')
				self._on_ports_change('ARRIVAL')
			elif wparam == self.ID_TIMER:
				if self._ports_change_count > 0:
					self._ports_change_count = 0
					self._on_ports_change(self._ports_change_type)
				if self._ipaddr_change_count > 0:
					self._ipaddr_change_count = 0
					self._on_ports_change('IPADDR')
		except Exception as e:
		   print ('get ctrl_msg exception %s'%e)
		   pass
		
	def destroy(self, hwnd=None, msg=None, wparam=None, lparam=None):
		nid = (self.hwnd, 0)
		user32.KillTimer(hwnd, self.ID_TIMER);
		try:
			win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
			if self.on_quit: self.on_quit(self)
		except:
			pass
		win32gui.PostQuitMessage(0) # Terminate the app.

	def notify(self, hwnd, msg, wparam, lparam):
		if lparam==win32con.WM_RBUTTONUP:
			self.show_menu()
		elif lparam==win32con.WM_LBUTTONUP:
			if self._show_main_win_callback is not None:
				self._show_main_win_callback()
		return True
		
	def show_menu(self):
		self.__menu_extra = {}
		menu = win32gui.CreatePopupMenu()
		self.create_menu(menu, self.menu_options)
		#win32gui.SetMenuDefaultItem(menu, 1000, 0)
		
		pos = win32gui.GetCursorPos()
		# See http://msdn.microsoft.com/library/default.asp?url=/library/en-us/winui/menus_0hdi.asp
		win32gui.SetForegroundWindow(self.hwnd)
		win32gui.TrackPopupMenu(menu,
								win32con.TPM_LEFTALIGN,
								pos[0],
								pos[1],
								0,
								self.hwnd,
								None)
		win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
	
	def create_menu(self, menu, menu_options):
		for option_text, option_icon, option_Checked, option_action, option_id in menu_options[::-1]:
			if option_icon:
				option_icon = self.prep_menu_icon(option_icon)
			item_state = None
			if option_Checked is True:
				item_state=win32con.MFS_CHECKED
			if option_id in self.menu_actions_by_id:				
				item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
																hbmpItem=option_icon,
																fState=item_state,
																wID=option_id)
				win32gui.InsertMenuItem(menu, 0, 1, item)
				if option_id not in self.__menu_extra:
					self.__menu_extra.setdefault(option_id, extras)
				else:
					self.__menu_extra[option_id] = extras
			else:
				submenu = win32gui.CreatePopupMenu()
				self.create_menu(submenu, option_action)
				item, extras = win32gui_struct.PackMENUITEMINFO(text=option_text,
																hbmpItem=option_icon,
																fState=item_state,
																hSubMenu=submenu)
				win32gui.InsertMenuItem(menu, 0, 1, item)
				if option_id not in self.__menu_extra:
					self.__menu_extra.setdefault(option_id, extras)
				else:
					self.__menu_extra[option_id] = extras

	def prep_menu_icon(self, icon):
		# First load the icon.
		ico_x = win32apiGetSystemMetrics(win32con.SM_CXSMICON)
		ico_y = win32apiGetSystemMetrics(win32con.SM_CYSMICON)
		hicon = win32gui.LoadImage(0, icon, win32con.IMAGE_ICON, ico_x, ico_y, win32con.LR_LOADFROMFILE)

		hdcBitmap = win32gui.CreateCompatibleDC(0)
		hdcScreen = win32gui.GetDC(0)
		hbm = win32gui.CreateCompatibleBitmap(hdcScreen, ico_x, ico_y)
		hbmOld = win32gui.SelectObject(hdcBitmap, hbm)
		# Fill the background.
		brush = win32gui.GetSysColorBrush(win32con.COLOR_MENU)
		win32gui.FillRect(hdcBitmap, (0, 0, 16, 16), brush)
		# unclear if brush needs to be feed.  Best clue I can find is:
		# "GetSysColorBrush returns a cached brush instead of allocating a new
		# one." - implies no DeleteObject
		# draw the icon
		win32gui.DrawIconEx(hdcBitmap, 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
		win32gui.SelectObject(hdcBitmap, hbmOld)
		win32gui.DeleteDC(hdcBitmap)
		#print ('icon_hbm',hbm)
		return hbm

	def command(self, hwnd, msg, wparam, lparam):
		id = win32gui.LOWORD(wparam)
		self.execute_menu_option(id)
		
	def walk_check_menu_options(self, id, menu_options):
		menu_count = len(menu_options)
		for i in range(0,menu_count):
			option_text, option_icon, option_checked, option_action, option_id = menu_options[i]
			if callable(option_action) or option_action in self.SPECIAL_ACTIONS:
				if option_id == id:
					menu_options[i][2] = not menu_options[i][2]
					break
			elif non_string_iterable(option_action):
				self.walk_check_menu_options(id, option_action)
		return
	def execute_menu_option(self, id):
		cur_item = self.menu_actions_by_id[id]
		menu_action = cur_item[-2]
		if menu_action == self.QUIT:
			win32gui.DestroyWindow(self.hwnd)
		else:
			ret = menu_action(self,cur_item)
			if ret is not None:
				self.walk_check_menu_options(id, self.menu_options)

def non_string_iterable(obj):
	try:
		iter(obj)
	except TypeError:
		return False
	else:
		return not isinstance(obj, str)

class win_sys_tray():
	def __init__(self):
		self.__root = None
		self.__sysTray = None
		self.__msgLoopProcess = None
		self.__expert_mode = False
		self.__debug_mode = False
		self.__instance_num = 0
		self.__serial_common_name = "COM"
		self.__net_common_name = 'NET'
		self.__adb_common_name = 'ADB'
		self.__net_key_word = '#'
		self.__dev_list_last = self.__dev_list = {self.__serial_common_name:[], self.__net_common_name:[],self.__adb_common_name:[]}
		self.__encoding = 'utf-8'
		self.__thread = None
		self.__quit = False
		self.__tray_icon_path = 'earth.ico'
		self.__app_title = 'iCOM for Windows'
		self.__realtime = 0
		self.__last_show_hide_time = 0
		self.__get_init_msg_success = True
	def set_expert_mode_callback(self,cur_mode):
		self.__expert_mode = cur_mode
	
	def _try_decoding(self,var_in,encoding=None):
		try:
			var_in = var_in.decode(encoding if encoding else "utf-8")
		except Exception as e:
			pass
		return var_in
	
	def get_serial_devs(self):
		serial__dev_list_last = self.__dev_list[self.__serial_common_name][:]
		adb__dev_list_last = self.__dev_list[self.__adb_common_name][:]
		try:
			self.__dev_list[self.__serial_common_name] = []
			self.__dev_list[self.__adb_common_name] = []
			cur__dev_list = devport.dev_list_class(('Ports','Modem','AndroidUsbDeviceClass'))
			for cur_dev in cur__dev_list:
				if cur_dev['ComPort'] and cur_dev['ComPort'] not in cur_dev['FriendlyName']:
					cur_dev['FriendlyName'] += "[%s]"%cur_dev['ComPort']
				if cur_dev['Class'] == 'AndroidUsbDeviceClass':
					self.__dev_list[self.__adb_common_name].append('#ADB:%s'%cur_dev['FriendlyName'])
				else:
					self.__dev_list[self.__serial_common_name].append(cur_dev['FriendlyName'])
			
		except Exception as e:
			print ("get serial,modem list exception %s"%e)
			pass
		return serial__dev_list_last != self.__dev_list[self.__serial_common_name],adb__dev_list_last != self.__dev_list[self.__adb_common_name]
	
	def get_net_devs(self):
		net__dev_list_last = self.__dev_list[self.__net_common_name][:]
		try:
			self.__dev_list[self.__net_common_name] = []
			ret,devs = osip.get_adapters_info()
			if ret == 0 and len(devs) > 0:
				for desc, addr, gwaddr, mac_a, dhcp_enabled, lease_obtained, lease_Expires, detail in devs:
					dhcp_enabled_i = lease_obtained_i = 0
					try:
						dhcp_enabled_i = int(dhcp_enabled)
						lease_obtained_i = int(lease_obtained,16)
					except Exception as e:
						print ('get dhcp lease/expires fail:%s'%e)
						pass
					#print (desc,type(desc),addr,isinstance(desc,bytes),isinstance(desc,str))
					
					desc = self._try_decoding(desc)
					
					#print (detail)
					dhcp_valid_flag = ''
					if dhcp_enabled_i > 0 and lease_obtained_i > 0:
						dhcp_valid_flag = '$'
					dev_info = "%s%s #IP: %s GW: %s MAC: %s"%(dhcp_valid_flag,desc,addr,gwaddr,mac_a)
					self.__dev_list[self.__net_common_name].append(dev_info)
		except Exception as e:
			print ('except in osip.get_adapters_info!! %s'%e)
			pass
		
		#return true is there is any change
		return net__dev_list_last != self.__dev_list[self.__net_common_name]
		
	def sys_tray_device_changed(self,change_type=None):
		if self.__sysTray:
			self.__sysTray.SetIpaddrChanged(change_type)
	def sys_tray_device_watching_thread(self,ipaddr_change_callback,var_reserved):
		if osip is None:
			return
		while self.__quit is False:
			osip.wait_ipaddr_change()
			ipaddr_change_callback('IPADDR')
		
	def sys_tray_init_tray_menu(self,icon_path,tray_ctrl_Q,menu_item_callback,ports_change_refresh,quit_callback=None):
		instance_num = self.__instance_num
		icons = icon_path
		tips_title = self.__app_title
		def keyEventCallback(msg,wparm,lparam):
			return
		def menu_click_callback(sysTrayIcon,cur_item):
			print ('cur_item',cur_item)
			return menu_item_callback(cur_item)
		
		menu_options = (('Show', None, False, menu_click_callback),
						('Hide', None, False, menu_click_callback),
						('Setting', None, False, (('Debug Mode', None, self.__debug_mode, menu_click_callback),
													  ('Expert Mode', None, self.__expert_mode, menu_click_callback),
													 )),
						('License', None, False, menu_click_callback)
					   )
		def on_quitbye(sysTrayIcon):
			if quit_callback is not None:quit_callback()
		__sysTray = SysTrayIcon(instance_num,icons,tray_ctrl_Q, tips_title, menu_options, ports_change_refresh, on_quitbye, 1, '%s-tray'%tips_title, self.__realtime)
		#__sysTray.setKeyEventCallback(keyEventCallback)
		__sysTray.setShowMainWinCallback(lambda :menu_click_callback(__sysTray,['SHOW-OR-HIDE',None,False,None,None]))
		self.__sysTray = __sysTray
	def sys_tray_init_device_change_watcher(self):
		self.__thread = Thread(target=self.sys_tray_device_watching_thread,args=(self.sys_tray_device_changed,0))
	def sys_tray_get_init_data(self,tray_out_Q,tray_ctrl_Q):
		self.tray_send_out_msg(tray_out_Q,('NOTIFY','TRAY-DATA',0))
		try:
			init_msg = tray_ctrl_Q.get(timeout=2)
			#print ('get init_msg',init_msg)
			if 'INIT-DATA' == init_msg[0] and len(init_msg) >= 2:
				expert_mode = init_msg[1]['expert_mode']
				self.__tray_icon_path = init_msg[1]['icon']
				self.__encoding = init_msg[1]['encoding']
				if 'realtime' in init_msg[1]:
					self.__realtime = init_msg[1]['realtime']
				self.set_expert_mode_callback(expert_mode)
		except Exception as e:
			self.__get_init_msg_success = False
			print ('get init_msg exception %s'%e)
			pass
	def tray_send_out_msg(self,msg_out_Q,send_args):
		ret = 0
		try:
			msg_out_Q.put(send_args,True)
			msg_out_Q.do_sync()
		except Exception as e:
			print ('tray send out msg exception %s'%e)
			ret = -1
			pass
		return ret
	def sys_tray_init(self,cur_instance_num,win_title,manager_Q,tray_ctrl_Q,gui_sync_ctrl_Q,tray_out_Q,pro_status):
		self.__root = None
		def ports_change_refresh(change):
			if change == 'IPADDR':
				is_change = self.get_net_devs()
				if is_change is True:
					self.tray_send_out_msg(tray_out_Q,('NOTIFY','NETS_CHANGE',self.__dev_list))
			else:
				is_serial_change,is_adb_change = self.get_serial_devs()
				if is_serial_change is True:
					self.tray_send_out_msg(tray_out_Q,('NOTIFY','PORTS_CHANGE',self.__dev_list))
				if is_adb_change is True:
					self.tray_send_out_msg(tray_out_Q,('NOTIFY','ADB_CHANGE',self.__dev_list))
				else:
					print ('ports no change')
		def quit_callback(e=None):
			self.tray_send_out_msg(tray_out_Q,('NOTIFY','QUIT',True))
			pro_status[1] = 1
			
		def menu_click_callback(cur_item):
			if tray_out_Q is not None and len(cur_item) > 2:
				item_str = cur_item[0].upper()
				if item_str == 'SHOW-OR-HIDE':
					cur_time = time.time()
					if cur_time < self.__last_show_hide_time + 0.9:
						return None
				self.tray_send_out_msg(tray_out_Q,('NOTIFY',item_str,cur_item[2]))
				#means no need to chang item check status
				if 'EXPERT MODE' == item_str or 'DEBUG MODE' == item_str:
					print ('menu_click_callback',True)
					return True
			return None
		
		self.__instance_num = cur_instance_num
		self.__app_title = win_title
		
		self.sys_tray_get_init_data(tray_out_Q, tray_ctrl_Q)
		self.sys_tray_init_tray_menu(self.__tray_icon_path,tray_ctrl_Q,menu_click_callback,ports_change_refresh,quit_callback)
		self.sys_tray_init_device_change_watcher()
	def sys_tray_setup_extimer(self,timeout_ms,callback):
		self.__sysTray.setupExternTimer(timeout_ms,callback)
	def sys_tray_start(self):
		self.__thread.setDaemon(True)
		self.__thread.start()
		self.__sysTray.msgMainLoop()
	def sys_tray_stay(self):
		if self.__root is not None:
			self.__root.withdraw()
	
	def sys_tray_quit(self):
		if self.__sysTray:
			self.__sysTray.destroy()
		self.__sysTray = None
	
	def sys_tray_leave(self):
		if self.__root is not None:
			self.__root.deiconify()

# Minimal self test. You'll need a bunch of ICO files in the current working
# directory in order for this to work...
if __name__ == '__main__':
	import itertools, glob
	pro_status = [0,0,0,0,0,0,0,0]
	#icons = itertools.cycle(glob.glob('*.ico'))
	icons = glob.glob('*.ico')
	hover_text = "SysTrayIcon.py Demo"
	def hello(sysTrayIcon): print ("Hello World.")
	def simon(sysTrayIcon): print ("Hello Simon.")
	def switch_icon(sysTrayIcon):
		sysTrayIcon.icon = icons.next()
		sysTrayIcon.refresh_icon()
	menu_options = (('Say Hello', False, False, hello),
					('Switch Icon', None, False,switch_icon),
					('A sub-menu', False, False,(('Say Hello', False, False, simon),
												  ('Switch Icon', False, False, switch_icon),
												 ))
				   )
	def bye(sysTrayIcon): print ('Bye, then.')
	sysTray = win_sys_tray()#manager_Q,tray_ctrl_Q,tray_out_Q
	import Queue
	tray_ctrl_Q = Queue.Queue()
	tray_out_Q = Queue.Queue()
	tray_ctrl_Q.put_nowait(('INIT-DATA',{'instance':0,'title':'title','expert_mode':0,'icon':'.','encoding':'utf-8'}))
	sysTray.sys_tray_init(None, tray_ctrl_Q,tray_out_Q, pro_status)
	print ('enter mainloop')
	empty = False
	while empty is False:
		try:
			out_msg = tray_out_Q.get(timeout=3)
			print ('GET-MSG:',out_msg)
		except:
			empty = True
			pass
	sysTray.sys_tray_quit()
	print ('enter quit')
	