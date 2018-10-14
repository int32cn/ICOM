#!/usr/bin/python
# -*- coding= utf-8 -*-

import sys
import os
import time
import string

from threading import current_thread
from collections import deque as ThreadQueue

import traceback

from autocomplete import *
from scrollFrame import VerticalScrolledFrame
import math

OS_name = os.name

icom_version    = 5
icom_subversion = 69
icom_version_description = 'ICOM Tools Version %d.%d\n'%(icom_version,icom_subversion)

N=Tkinter.N
S=Tkinter.S
E=Tkinter.E
W=Tkinter.W

def is_module_exists(module_name):
	_is_exists = False
	try:
		__import__(module_name)
		_is_exists = True
	except ImportError:
		pass
	return _is_exists	

def get_cur_base_dir():
	program_dir = os.path.abspath('.')
	basedir = program_dir
	try:
		if getattr(sys, 'frozen', None):
			basedir = sys._MEIPASS
	except Exception as e:
		print ('get_base_dir err:%s'%e)
		pass
		
	return program_dir,basedir

def load_config(conf_file_name,default_config_content=None):
	program_dir,basedir = get_cur_base_dir()
	user_config_file = False
	try:
		f = None
		if os.path.exists(conf_file_name):
			f = open(conf_file_name, 'rb')
			user_config_file = True
		else:
			xml_file = os.path.join(basedir, conf_file_name)
			f = open(xml_file, 'rb')
		str_xml = f.read()
	except Exception as e:
		user_config_file = False
		f = open(conf_file_name, 'w')
		f.write(default_config_xml_content)
		str_xml = default_config_xml_content
		print ('error open %s:%s,use default xml'%(conf_file_name,e))
		pass
	finally:
		if f:
			f.close()
	return str_xml,user_config_file
	
class com_ports_gui:
	NOTIFY_TAB = 'notify'
	DEFAULT_FILTERS = 3 #default value
	MAX_FILTERS = 12    #value for debug mode
	CF_TEXT = 1
	CF_UNICODETEXT = 13
	FILTER_MATCH = ('Disable','StartsWith','Include','EndsWith','RegExp','IdleTime(s)','ComeFrom')
	FILTER_MATCH_DISABLE = 0
	FILTER_MATCH_STARTS_WITH = 1
	FILTER_MATCH_INCLUDE = 2
	FILTER_MATCH_ENDS_WITH = 3
	FILTER_MATCH_REGEXP = 4
	FILTER_MATCH_IDLE_TIME = 5
	FILTER_MATCH_COME_FROM = 6
	
	FILTER_ACTION = ('Nothing','Send','AutoSend','Drop','Alarm','SendTo',"DoProcess")
	FILTER_ACTION_NONE = 0
	FILTER_ACTION_SEND = 1
	FILTER_ACTION_AUTO_SEND = 2
	FILTER_ACTION_DROP = 3
	FILTER_ACTION_ALARM = 4
	FILTER_ACTION_SENDTO = 5
	FILTER_ACTION_DOPROCESS = 6
	
	TEXT_TAG_LOCAL_ECHO = 'tag-local-echo'
	def __init__(self, tkroot, win_title):
		self.__quit_now = False
		self.__instance_num = 0
		self.__tid = current_thread().ident
		self.__expert_mode = False
		self.__debug_mode = 0
		self.__com_gui = {}
		self.__input_btn = {}
		self.__dev_dict = {}
		self.__cmd_dict = {}
		self.__root = tkroot
		self.__state = 'init'
		self.__is_focus_in = True
		self.__realtime = 0
		self.__win_title = win_title
		self.__need_refresh_gui_dev = False
		self.__root.title(win_title)
		self.__button_frame = ttk.Frame(self.__root, borderwidth=0,height=20)
		self.__top_frame = ttk.Frame(self.__root, borderwidth=0,height=2)
		self.__main_paned_frame = Tkinter.PanedWindow(self.__root, borderwidth=0)
		self.__left_frame = ttk.Frame(self.__main_paned_frame, borderwidth=0,width=800)
		self.__right_frame = ttk.LabelFrame(self.__main_paned_frame,text="command group",borderwidth=0,width=269)
		self.__left_top_frame = ttk.Frame(self.__left_frame, borderwidth=0)
		self.__left_top_frame_setting = ttk.Frame(self.__left_top_frame, borderwidth=0)
		self.__left_top_frame_com = ttk.LabelFrame(self.__left_top_frame, text="serial list", borderwidth=0)
		self.__left_top_frame_net = ttk.LabelFrame(self.__left_top_frame, text="netcard list", borderwidth=0)
		self.__left_middle_frame = ttk.Frame(self.__left_frame, borderwidth=0)
		self.__left_bottom_frame = ttk.LabelFrame(self.__left_frame, text="send box", borderwidth=1)
		self.__right_bottom_frame = VerticalScrolledFrame(self.__right_frame, borderwidth=1,width=267)
		self.__filter_frame = ttk.Frame(self.__root, borderwidth=0)
		self.__send_frame = ttk.LabelFrame(self.__root, text="send box",borderwidth=1)
		self.__send_frame_entry = None
		self.__send_file_name = ['demo.bin']
		self.__send_file_idx = 0
		self.__send_zmodem_file_path = ['zsend', 'demo.bin']
		self.__send_zmodem_idx = 0
		self.__first_dev = None
		self.__last_dev = None
		self.__about_button = None
		self.__frame_pack = False
		self.__gui_shown = False
		self.__filter_frame_pack = False
		self.__left_bottom_frame_pack = False
		self.__right_frame_pack = True
		self.__send_frame_pack = True
		self.__net_dev_cur_show = False
		self.__dev_mouse_on = {'com_dev':False,'net_dev':False,'text_title':False,'text_title_s':False,'setting':False}
		self.__dev_open_buttons = {}   #open and show tab
		self.__dev_hide_buttons = {}  #disconnect and hide tab
		self.__dev_text_queues = {}
		self.__dev_statics_info = {}
		self.__cmd_group_str_list = []
		self.__cmd_group_list = None
		self.__top_tips_var = Tkinter.StringVar(self.__root)
		self.__top_tips_label = None
		self.__tips__after_task_id = None
		self.__auto_send_ctrl = None
		self.__auto_parse_area = None
		self.__auto_send_loop_ctrl = None
		self.__auto_send_time_ctrl = None
		self.__alpha_scale_ctrl = None
		self.__auto_send_enable = False
		self.__auto_hide_dev_enable_var = Tkinter.IntVar(self.__root)
		self.__auto_send_time_interval = 1000
		self.__auto_send_cmd_list_info = {}
		self.__auto_send_loop_var = Tkinter.StringVar(self.__root)
		self.__auto_send_loop_count = 0
		self.__auto_send_total_loop_count = 0
		self.__auto_send_total_cmd_count = 0
		self.__auto_send_loop_str = Tkinter.StringVar(self.__root)
		self.__auto_start_tcp_server_var = Tkinter.IntVar(self.__root)
		self.__auto_start_udp_server_var = Tkinter.IntVar(self.__root)
		self.__auto_start_multicast_server_var = Tkinter.IntVar(self.__root)
		self.__auto_save_log_var = Tkinter.IntVar(self.__root)
		self.__sending_encoding_var = Tkinter.StringVar(self.__root)
		self.__display_encoding_var = Tkinter.StringVar(self.__root)
		self.__display_hex_var = Tkinter.IntVar(self.__root)
		self.__display_hex = 0
		self.__auto_line_wrap_show_var = Tkinter.IntVar(self.__root)
		self.__auto_line_wrap_show = 0
		self.__local_echo_var = Tkinter.IntVar(self.__root)
		self.__show_timestamp_var = Tkinter.IntVar(self.__root)
		self.__auto_send_reverse = Tkinter.IntVar(self.__root)
		self.__always_top_var = Tkinter.IntVar(self.__root)
		self.__send_format_hex_var = Tkinter.IntVar(self.__root)
		self.__save_log_file_name = {}
		self.__auto_send_time_interval_var = Tkinter.StringVar(self.__root)
		self.__auto_send_start_var = Tkinter.StringVar(self.__root)
		self.__send_interval_entry_list = [None,None,None]
		self.__send_interval_checkbox_list = [None,None,None]
		self.__send_interval_var_names = ('$X','$Y','$Z')
		self.__send_interval_var_names_bials = ('${X}','${Y}','${Z}')
		self.__send_interval_var_enable = (Tkinter.IntVar(self.__root),Tkinter.IntVar(self.__root),Tkinter.IntVar(self.__root))
		self.__send_interval_var_rule = (Tkinter.StringVar(self.__root),Tkinter.StringVar(self.__root),Tkinter.StringVar(self.__root))
		self.__send_interval_rule_compile = [None,None,None]
		self.__send_interval_var_index_to_name = ('X','Y','Z')
		self.__send_interval_scope = {'i':0,'X':0,'Y':0,'Z':0}
		self.__send_interval_template_dict = {}
		self.__send_interval_var_value = (Tkinter.StringVar(self.__root),Tkinter.StringVar(self.__root),Tkinter.StringVar(self.__root))
		self.__send_interval_enable    = [0,0,0]
		self.__send_interval_var_combo_list = []
		self.__cur_auto_send_index = 0
		self.__filter_real_count = self.DEFAULT_FILTERS
		self.__safe_scope = {'__builtins__':{}}
		self.__filter_interval_scope = {}
		self.__filter_external_module = {}
		self.__filter_external_module_buffer_in = None
		self.__filter_external_module_buffer_out = None
		self.__filter_text_var = [Tkinter.StringVar(self.__root) for i in range(0,self.MAX_FILTERS)]
		self.__filter_action_param_var = [Tkinter.StringVar(self.__root) for i in range(0,self.MAX_FILTERS)]
		self.__filter_match_pattan = com_ports_gui.FILTER_MATCH
		self.__filter_pattern_sel = [0 for i in range(0,self.MAX_FILTERS)]
		self.__text_filter_str = ['' for i in range(0,self.MAX_FILTERS)]
		self.__filter_actions = com_ports_gui.FILTER_ACTION
		self.__filter_actions_sel = [0 for i in range(0,self.MAX_FILTERS)]
		self.__filter_actions_param = ['' for i in range(0,self.MAX_FILTERS)]
		self.__filter_combo = [None for i in range(0,self.MAX_FILTERS)]
		self.__filter_action_combo = [None for i in range(0,self.MAX_FILTERS)]
		self.__filter_hit_timestamp = 0
		self.__filter_idle_task_count = 0
		self.__filter_execute_timestamp = [0 for i in range(0,self.MAX_FILTERS)]
		self.__filter_tasks_num = [0 for i in range(0,self.MAX_FILTERS)]
		self.__text_filter_valid_bits = [0 for i in range(0,self.MAX_FILTERS)]
		self.__include_text_filter = None
		self.__send_text_var = Tkinter.StringVar(self.__root)
		self.__text_extend_var = Tkinter.StringVar(self.__root)
		self.__send_normal_text_var = Tkinter.StringVar(self.__root)
		self.__send_text_tail_var = Tkinter.StringVar(self.__root)
		self.__serial_bitrate_var = Tkinter.StringVar(self.__root)
		self.__serial_databit_var = Tkinter.StringVar(self.__root)
		self.__serial_stopbit_var = Tkinter.StringVar(self.__root)
		self.__serial_checkbit_var = Tkinter.StringVar(self.__root)
		self.__serial_flowctrl_var = Tkinter.StringVar(self.__root)
		self.__cmd_tail_combo_list = []
		self.__history_cmd_list = []
		self.__history_hex_cmd_list = []
		self.__default_auto_complete_cmd_list = []
		self.__total_auto_complete_cmd_list = []
		self.__defaut_tail_str = os.linesep
		self.__send_cmd_callback = None
		self.__send_encoding_combo_list = ['utf-8','utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be','gb2312','gbk','gb18030']
		self.__recv_decoding_combo_list = ['utf-8','utf-16','utf-16-le','utf-16-be','utf-32','utf-32-le','utf-32-be','gb2312','gbk','gb18030']
		self.__send_encoding_var = Tkinter.StringVar(self.__root)
		self.__recv_decoding_var = Tkinter.StringVar(self.__root)
		self.__keep_ascii_single_byte = Tkinter.IntVar(self.__root)
		self.__callback_dict = {'start_tcp_srv':None,'start_udp_srv':None,'start_multicast_srv':None,'dev_remove':None,
					'start_TLV':None,'auto_save':None,'ports_all_close':None,'show_log_file_dir':None,
					'time_interval':None,'cmd_list':None,'auto_send_cmd_idx':None,'send_file':None,'send_zmodem_path':None,
					'focus_in':None,'focus_out':None,'msg_sync':None,
					'local_echo':None,'show_time':None,'msg_quit':None}
		self.__drop_down_callback = None
		self.__userlist_callback = None
		self.__port_callback = None
		self.__notebook = None
		self.__notebook_dev_tab_shown = False
		self.__notebook_dev_connect = False
		self.__notify_tab_show = False
		self.__notebook_cur_select_dev = None
		self.__toplevel_win_count = 0
		self.__buffer_text=[]
		self.__text_scroll_disable = False
		self.__text_scrollbar_press = False
		self.__max_buffer_lines = 3000
		self.__max_buffer_size = 16*1024
		self.__max_buffer_size_pingpong = 4*1024
		self.__max_buffer_lines_pingpong = 500
		self.__max_buffer_lines_threshold = self.__max_buffer_lines + self.__max_buffer_lines_pingpong
		self.__min_buffer_lines_threshold = self.__max_buffer_lines - self.__max_buffer_lines_pingpong
		self.__text_file_queue = ThreadQueue()
		self.__cmd_list = []
		self.__cmd_change_disable = False
		self.__tips_var = Tkinter.StringVar(self.__root)
		self.__tips_label = None
		self.__cmd_timeout = 0
		self.__min_cmd_per_group = 25
		self.__font_size = 10
		self.__entry_height = None
		self.__max_cmd_per_group = 32
		self.__config = {}
		self.__cmd_change_ver = 0
		self.__cmd_auto_save_ver = 0
		self.__custom_com_var = Tkinter.StringVar(self.__root)
		self.__in_trace = False
		self.__spec_char_set = set(['\r','\n','\t','\f','\t','\v','\b','\x00'])
		self.__spec_char_set_repr = {'\r':r'\r','\n':r'\n','\t':r'\t','\f':r'\f','\t':r'\t','\v':r'\v','\b':r'\b','\x00':r'\x00'}
		self.__auto_open_dev_entry = None
		self.__auto_open_dev_btn = None
		self.__custom_com_show = False
		self.__base_dir = None
		self.__program_dir = None
		self.__sync_msg_count = 0
		self.__sync_msg_rate = 0
		self.__net_common_name = 'NET'
		self.__adb_common_name = 'ADB'
		self.__net_key_word = '#'
		self.__mac_index_table = {}
		if OS_name == 'nt':
			self.__serial_common_name = "COM"
		else:
			self.__serial_common_name = "/dev/tty"
		self.__dev_list = {self.__serial_common_name:[], self.__net_common_name:[],self.__adb_common_name:[]}
		self.__dev_list_last = {self.__serial_common_name:[], self.__net_common_name:[],self.__adb_common_name:[]}
		self.__submit_processing_flag = False
		self.__no_add_text_schecule_count = 0
		self.__text_schedule_count_param = 0
		self.__schedule_manager = {}
		
		self.__img_gray = Tkinter.PhotoImage(master=self.__root)
		self.__img_gray.put("{#4C4C4C} ",to=(0,0,14,14))
		self.__img_red = Tkinter.PhotoImage(master=self.__root)
		self.__img_red.put("{#E1594A #E1594A} ",to=(0,0,14,14))
		self.__img_green = Tkinter.PhotoImage(master=self.__root)
		self.__img_green.put("{#51B973} ",to=(0,0,14,14))
		self.__img_red_yellow = Tkinter.PhotoImage(master=self.__root)
		self.__img_red_yellow.put("{#E1594A #E1594A #E1594A  #DFB831 #DFB831 #DFB831 } ",to=(2,2,14,14))
		
		s = ttk.Style(self.__root)
		s.configure('cmd.TEntry', borderwidth=0,font=('Helvetica', self.__font_size-1, 'normal'))
		s.configure('cmd.TButton', borderwidth=0,font=('Helvetica', self.__font_size-1, 'normal'))
		s.configure('send.TButton', borderwidth=0,font=('Helvetica', self.__font_size, 'normal'))
		s.configure('cmd.TCheckbutton', borderwidth=0,font=('Helvetica', self.__font_size-1, 'normal'))
		s.configure('running.TButton', foreground='#FF4500',background='#FFD700',font=('Helvetica', 10, 'normal'))# fg:maroon,bg: linttle-red
		s.configure('stoped.TButton', borderwidth=0,font=('Helvetica', 10, 'normal')) # forground pink-red, bg light-green
		
		s.map('TButton',
					foreground=[('disabled', 'gray'),
								('pressed', 'red'),
								('active', 'blue')],
					background=[#('disabled', 'magenta'),
								('pressed', '!focus', 'cyan'),
								('active', 'green')],
					highlightcolor=[('focus', 'green'),
									('!focus', 'red')],
					relief=[('pressed', 'sunken'), #groove
							('!pressed', 'ridge')],
					#borderwidth=[('active',0),('focus','0')]
					) #ridge
		s.configure('InactiveTab.TButton',
					#background='black',
					foreground='#8080FF',
					highlightthickness='20',
					font=('Helvetica', 10, 'normal'))
		s.configure('ActiveTab.TButton',
					#background='blue',
					foreground='#FF4500',
					highlightthickness='20',
					font=('Helvetica', 11, 'bold'))
		s.configure('fixsize.TButton', highlightthickness='20',font=('Helvetica', 10, 'normal'))
		s.configure('fixsize8.TButton', highlightthickness='20',font=('Helvetica', 8, 'normal'))
		s.configure('fixsize10.TButton', highlightthickness='20',font=('Helvetica', 10, 'normal'))
		s.configure('fixsize12.TButton', highlightthickness='20',font=('Helvetica', 12, 'normal'))
		s.configure('fixsize14.TButton', highlightthickness='20',font=('Helvetica', 14, 'normal'))
		#s.configure('extendArrow.TButton', border='0')
		self.__style_set = s
		
	def register_callback(self,callback_type,callback):
		if callback_type in self.__callback_dict:
			self.__callback_dict[callback_type] = callback
		else:
			self.__callback_dict.setdefault(callback_type,callback)
	def do_gui_callback(self,event,callback_type,**kargs):
		if callback_type in self.__callback_dict:
			if self.__callback_dict[callback_type] is not None:
				self.__callback_dict[callback_type](event,**kargs)
			
	def set_cmd_list(self,cmd_list):
		self.__cmd_list = cmd_list
		if type(self.__cmd_list) == type([]) and len(self.__cmd_list) > 0:
			groups = []
			for cmd in self.__cmd_list:
				if type(cmd) == type({}) and '@name' in cmd:
					groups.append(cmd['@name'])
			self.__cmd_group_str_list = tuple(groups)
			
		self.__init_cmd_dict_var('CMD')
		self.__init_total_cmd_list('CMD')
		
	def set_debug_mode(self,debug_mode):
		self.__debug_mode = debug_mode
	def set_config(self,config_list):
		self.__config = config_list
		
		try:
			self.__min_cmd_per_group = 25
			if 'cmdpergroup' in self.__config and self.__config['cmdpergroup'].isdigit():
				self.__min_cmd_per_group = int(config_list['cmdpergroup'])
				if self.__min_cmd_per_group <= 3:
					self.__min_cmd_per_group = 15
		except:
			pass
		
		try:
			if 'expert_mode' in self.__config and self.__config['expert_mode'].isdigit():
				if int(self.__config['expert_mode']) > 0:
					self.__expert_mode = True
		except:
			pass
		
		try:
			self.__entry_height = None
			if 'entryheight' in self.__config and self.__config['entryheight'].isdigit():
				self.__entry_height = int(self.__config['entryheight'])
				if self.__entry_height <= 0:
					self.__entry_height = None
		except:
			pass
		
		try:
			self.__auto_start_tcp_server_var.set(0)
			if 'auto_start_tcp_server' in self.__config and self.__config['auto_start_tcp_server'].isdigit():
				if int(self.__config['auto_start_tcp_server']) > 0:
					self.__auto_start_tcp_server_var.set(1)
		except:
			pass
		
		try:
			self.__auto_start_udp_server_var.set(0)
			if 'auto_start_udp_server' in self.__config and self.__config['auto_start_udp_server'].isdigit():
				if int(self.__config['auto_start_udp_server']) > 0:
					self.__auto_start_udp_server_var.set(1)
		except:
			pass
		
		try:
			self.__auto_start_multicast_server_var.set(0)
			if 'auto_start_multicast_server' in self.__config and self.__config['auto_start_multicast_server'].isdigit():
				if int(self.__config['auto_start_multicast_server']) > 0:
					self.__auto_start_multicast_server_var.set(1)
		except:
			pass
		
		try:
			self.__right_frame_pack = True
			if 'show_command_list' in self.__config and self.__config['show_command_list'].isdigit():
				if int(self.__config['show_command_list']) == 0:
					self.__right_frame_pack = False
		except:
			pass
		try:
			self.__font_size = 10
			if 'font_size' in self.__config and self.__config['font_size'].isdigit():
				self.__font_size = int(self.__config['font_size'])
				self.__style_set.configure('send.TButton', font=('Helvetica', self.__font_size, 'normal'))
		except:
			pass
		try:
			self.__realtime = 0
			if 'realtime' in self.__config and self.__config['realtime'].isdigit():
				self.__realtime = int(self.__config['realtime'])
		except:
			pass
		
		try:
			'test.recv.encoding'.decode(self.__config['send_encoding'])
		except:
			self.__config['send_encoding'] = 'utf-8'
			pass
		try:
			'test.send.encoding'.decode(self.__config['display_encoding'])
		except:
			self.__config['display_encoding'] = 'utf-8'
			pass
	def check_set_config(self, config_list):
		check_set = False
		cur_window_size = str(self.__root.geometry())
		cur_exe_base_diff = True
		if self.__program_dir == self.__base_dir:
			cur_exe_base_diff = False
			
		if not 'baudrate' in config_list:
			config_list['baudrate'] = 115200
			check_set = True
		if not 'send_encoding' in config_list:
			config_list['send_encoding'] = 'utf-8'
			check_set = True
		if not 'display_encoding' in config_list:
			config_list['display_encoding'] = 'utf-8'
			check_set = True
		if not 'textwidth' in config_list:
			config_list['textwidth'] = 60
			check_set = True
		if not 'poll_timer' in config_list:
			config_list['poll_timer'] = 3000
			check_set = True
		if not 'shell' in config_list:
			config_list['shell'] = 'cmd.exe'
			check_set = True
		if not 'textbackground' in config_list:
			config_list['textbackground'] = 'auto'
			check_set = True
		if not 'textforeground' in config_list:
			config_list['textforeground'] = 'auto'
			check_set = True
		if not 'entryheight' in config_list:
			config_list['entryheight'] = 25
			check_set = True
		if not 'listheight' in config_list:
			config_list['listheight'] = 6
			check_set = True
		if not 'cmdpergroup' in config_list:
			config_list['cmdpergroup'] = 25
			check_set = True
		if not 'autocom' in config_list:
			config_list['autocom'] = ''
			check_set = True
		if not 'net_config_data' in config_list:
			config_list['net_config_data'] = r'AT\r'
			check_set = True
		if not 'tcp_srv_port' in config_list:
			config_list['tcp_srv_port'] = 3000
			check_set = True
		if not 'udp_srv_port' in config_list:
			config_list['udp_srv_port'] = 3000
			check_set = True
		if not 'auto_start_multicast_server' in config_list:
			config_list['auto_start_multicast_server'] = 1
			check_set = True
		if not 'auto_start_tcp_server' in config_list:
			config_list['auto_start_tcp_server'] = 0
			check_set = True
		if not 'multicast_ip' in config_list:
			config_list['multicast_ip'] = '224.0.0.119'
			check_set = True
		if not 'multicast_port' in config_list:
			config_list['multicast_port'] = 30000
			check_set = True
		if not 'auto_start_udp_server' in config_list:
			config_list['auto_start_udp_server'] = '0'
			check_set = True
		if not 'parse_key_word' in config_list:
			config_list['parse_key_word'] = '61 74 '
			check_set = True
		if not 'show_command_list' in config_list:
			config_list['show_command_list'] = 1
			check_set = True
		if not 'expert_mode' in config_list:
			config_list['expert_mode'] = 0
			check_set = True
		if not 'realtime' in config_list:
			config_list['realtime'] = 0
			check_set = True
		
		if cur_exe_base_diff is False:
			#print (self.__program_dir,self.__base_dir,__file__,check_set)
			return check_set;
			
		if not 'window_size' in config_list or config_list['window_size'] != cur_window_size:
			config_list['window_size'] = cur_window_size
			check_set = True
		
		if 'font_size' not in config_list or  config_list['font_size'] != str(self.__font_size):
			config_list['font_size'] = str(self.__font_size)
			check_set = True
		
		if self.__right_frame_pack is False and config_list['show_command_list'] != '0':
			config_list['show_command_list'] = '0'
			check_set = True
		if self.__right_frame_pack is True and config_list['show_command_list'] == '0':
			config_list['show_command_list'] = '1'
			check_set = True
			
		if str(self.__auto_start_tcp_server_var.get()) != str(config_list['auto_start_tcp_server']):
			config_list['auto_start_tcp_server'] = self.__auto_start_tcp_server_var.get()
			check_set = True
		if str(self.__auto_start_udp_server_var.get()) != str(config_list['auto_start_udp_server']):
			config_list['auto_start_udp_server'] = self.__auto_start_udp_server_var.get()
			check_set = True
		if str(self.__auto_start_multicast_server_var.get()) != str(config_list['auto_start_multicast_server']):
			config_list['auto_start_multicast_server'] = self.__auto_start_multicast_server_var.get()
			check_set = True
		
		return check_set
	def get_base_dir(self):
		if self.__base_dir is None:
			self.__program_dir, self.__base_dir = get_cur_base_dir()
		return self.__base_dir
		
	def set_instance_num(self,instance_num):
		self.__instance_num = instance_num
	
	def get_realtime_mode(self):
		return self.__realtime
	def get_current_state(self):
		#normal, icon, iconic (see wm_iconwindow), withdrawn, or zoomed (Windows only).
		if self.__is_focus_in is True:
			return ".focus"
		if not self.__state:
			self.__state = self.__root.wm_state()
		return "%s"%self.__state
	def show_gui(self):
		cur_state = self.__root.wm_state()
		if 'normal' != cur_state and 'zoomed' != cur_state:
			self.__root.deiconify()
			self.__state = 'normal'
	def hide_gui(self):
		cur_state = self.__root.wm_state()
		if 'withdrawn' != cur_state:
			self.__root.withdraw()
			self.__state = 'withdrawn'
	def show_or_hide_gui(self):
		cur_state = self.__root.wm_state()
		if 'withdrawn' != cur_state:
			self.__root.withdraw()
			self.__state = 'withdrawn'
		else:
			self.__root.deiconify()
			self.__state = 'normal'
	def mini_gui(self):
		cur_state = self.__root.wm_state()
		if 'iconic' != cur_state and 'icon' != cur_state:
			self.__root.iconify()
			self.__state = 'icon'
	def load_icon(self):
		basedir = self.get_base_dir()
		d = {'1':'question','2':'question','3':'question','4':'question','5':'question','6':'warning','7':'error'}
		try:
			icon_file = os.path.join('.', 'icon.icon')
			icon_file_snd = os.path.join(basedir, 'icon.ico')
			icon_file_third = os.path.join(basedir, 'earth.ico')
			if os.path.exists(icon_file):
				x = self.__root.iconbitmap(bitmap=icon_file)
			elif os.path.exists(icon_file_snd):
				x = self.__root.iconbitmap(bitmap=icon_file_snd)
			elif os.path.exists(icon_file_third):
				x = self.__root.iconbitmap(bitmap=icon_file_third)
			else:
				x = self.__root.iconbitmap(bitmap=d['7'])
		except:
			pass
	
	def get_dev_common_name(self):
		return (self.__serial_common_name,self.__net_common_name)
	
	def add_buttons(self,btn_str,btn_callback=None):
		'''set the top buttons below MENU'''
		if not btn_str in self.__input_btn:
			b2=Button(self.__button_frame, text=btn_str,width=8)
			b2.pack(side=LEFT, padx=1)
			if btn_callback is not None:
				b2.bind("<Button-1>",btn_callback)
				b2.bind("<Return>",btn_callback)
			self.__input_btn.setdefault(btn_str,{})
			self.__input_btn[btn_str]['widget'] = b2
		
	def get_log_file_name(self,dev_name):
		if not os.path.exists('log'):
			os.mkdir('log')
		if self.__auto_save_log_var.get() > 0:
			log_dev_name = dev_name.replace(':','v').replace('?','').replace('/','').replace('\\','').replace('@','v')
			log_dev_name = log_dev_name.replace('*','').replace('|','').replace('>','').replace('<','').replace('"','')
			log_name = os.path.join('log', '_%s_%s.txt' %(log_dev_name, time.strftime("%m%d_%H%M%S")))
			self.__save_log_file_name[dev_name] = log_name
			return log_name
		return None
	
	def _auto_save_log_file_close(self,dev_name):
		if dev_name in self.__save_log_file_name:
			del self.__save_log_file_name[dev_name]
			
	def __get_vscroll_text(self,top_frame):
		text_area = None
		try:
			scroll_text_frame = top_frame
			text_bg = text_fg = 'auto'
			if 'textbackground' in self.__config:
				text_bg = self.__config['textbackground']
			if 'textforeground' in self.__config:
				text_fg = self.__config['textforeground']
			
			if text_bg != 'auto' and text_fg != 'auto' and text_bg != b'auto' and text_fg != b'auto':
				text_area = scrolledtext.ScrolledText(scroll_text_frame, background=text_bg,foreground=text_fg, wrap=Tkinter.WORD)
			elif text_bg != 'auto' and text_bg != b'auto':
				text_area = scrolledtext.ScrolledText(scroll_text_frame, background=text_bg, wrap=Tkinter.WORD)
			elif text_fg != 'auto' and text_fg != b'auto':
				text_area = scrolledtext.ScrolledText(scroll_text_frame, foreground=text_fg, wrap=Tkinter.WORD)
			else:
				text_area = scrolledtext.ScrolledText(scroll_text_frame, wrap=Tkinter.WORD)
		except Exception as e:
			print ('Exception in creat Text:%s'%e)
			text_area = scrolledtext.ScrolledText(scroll_text_frame)
			pass
		return text_area,text_area
	def _get_vscroll_text(self,top_frame):
		scroll_text_frame = ttk.Frame(top_frame)
		scroll_text_frame.rowconfigure(0,weight=1)
		scroll_text_frame.columnconfigure(0,weight=1)
		
		try:
			text_bg = text_fg = 'auto'
			if 'textbackground' in self.__config:
				text_bg = self.__config['textbackground']
			if 'textforeground' in self.__config:
				text_fg = self.__config['textforeground']
			
			if text_bg != 'auto' and text_fg != 'auto' and text_bg != b'auto' and text_fg != b'auto':
				text_area = Tkinter.Text(scroll_text_frame,background=text_bg,foreground=text_fg)
			elif text_bg != 'auto' and text_bg != b'auto':
				text_area = Tkinter.Text(scroll_text_frame,background=text_bg)
			elif text_fg != 'auto' and text_fg != b'auto':
				text_area = Tkinter.Text(scroll_text_frame,foreground=text_fg)
			else:
				text_area = Tkinter.Text(scroll_text_frame)
		except Exception as e:
			print ('Exception in creat Text:%s'%e)
			text_area = Tkinter.Text(scroll_text_frame)
			pass
		
		if text_bg == 'blue':
			text_area.tag_config(com_ports_gui.TEXT_TAG_LOCAL_ECHO, foreground='white')
		else:
			text_area.tag_config(com_ports_gui.TEXT_TAG_LOCAL_ECHO, foreground='blue')
		scroll_bar = ttk.Scrollbar(scroll_text_frame)
		
		self.__text_key_var = Tkinter.StringVar(self.__root)
		def text_key_in(event):
			#print ('<'+event.keysym+'>',event.keycode,'<'+event.char+'>',len(event.char) )
			#ord('a') chr(65) unichr(65)
			need_send_key = False
			cmd_ctx = {'text':self.__text_key_var, 'tail':''}
			
			if event.keysym == 'Return':
				self.__text_key_var.set(os.linesep)
				need_send_key = True
			elif event.keycode >= 65 and event.keycode <=90:
				if chr(event.keycode).upper() == event.char.upper():
					self.__text_key_var.set(event.char)
					need_send_key = True
			elif event.keysym == 'Escape':
				self.__text_key_var.set(chr(27))
				need_send_key = True
				#print (self.__text_key_var.get(),'c',event.char)
			elif len(event.char) > 0:
				self.__text_key_var.set(event.char)
				need_send_key = True
			
			if need_send_key == True:
				self.text_scroll_disable_set(event,False,'keyin',True)
				self.__do_send_command(event,cmd_ctx)
				return 'break'
		
		def text_scroll_press(event):
			self.__text_scrollbar_press = True
			self.text_scroll_disable_set(event,True,'scrollPress',True)
		def text_scroll_release(event):
			self.__text_scrollbar_press = False
			cur_up,cur_down = scroll_bar.get()
			if cur_down >= 0.99999: #to the bottom
				self.text_scroll_disable_set(event,False,'scrollEnd',True)
		text_area.bind('<FocusIn>', lambda event:self.text_scroll_disable_set(event,True,'foucusIn',True))
		text_area.bind('<FocusOut>',lambda event:self.text_scroll_disable_set(event,False,'foucusOut',True))
		text_area.bind('<Down>',lambda event: self.__send_frame_entry.focus())
		text_area.bind('<Right>',lambda event: self.__cmd_group_list.focus())
		#text_area.bind('<Escape>',lambda event: self.list_box_focus())
		text_area.bind('<Shift-Tab>',lambda event: self.first_dev_focus())
		text_area.bind('<Key>',lambda event: text_key_in(event))
		def scro_bar_set_func(cur_top,cur_down,*args):
			cur_top_f = float(cur_top)
			cur_down_f = float(cur_down)
			#print ('scro_bar_set_func',cur_top,cur_down,args,1/(cur_down_f-cur_top_f),self.__text_scrollbar_press,self.__text_scroll_disable)
			if self.__text_scrollbar_press is True:
				scroll_bar.set(cur_top,cur_down,*args)
			elif cur_down_f >= 0.99999:
				scroll_bar.set(cur_top,cur_down,*args)
			elif self.__text_scroll_disable is True:
				scroll_bar.set(cur_top,cur_down,*args)
			
		text_area['yscrollcommand'] = scro_bar_set_func#scroll_bar.set
		scroll_bar['command'] = text_area.yview#text_area.yview
		scroll_bar.bind('<ButtonPress-1>',lambda event: self.text_scroll_disable_set(event,True,'scrollPress',True))
		scroll_bar.bind('<ButtonRelease-1>',text_scroll_release)
		
		text_area.grid(row=0,column=0,sticky=N+S+W+E)
		scroll_bar.grid(row=0,column=1,sticky=N+S)
		return scroll_text_frame,text_area
	def _set_auto_comm_state(self,dev_name,event_now=None):
		if event_now is not None and event_now.widget == self.__auto_open_dev_btn:
			self.change_readonly_state(self.__auto_open_dev_entry,'disabled')
			if 'autocom' in self.__config:
				new_com_name = self.__auto_open_dev_entry.get()
				if self.__config['autocom'] != new_com_name:
					self.__config['autocom'] = new_com_name
					self.set_cmd_changed(True)
			else:
				self.set_cmd_changed(True)
	def __get_port_button_widget_from_name(self,dev_name,event_now=None):
		port_button = None
		ports_dev_dict = self.__dev_dict[self.__serial_common_name]
		for dev_key,dev_info in ports_dev_dict.items():
			if dev_name == "%s%d"%(self.__serial_common_name,dev_key):
				port_button = dev_info['button']
				break
		if event_now and event_now.widget == self.__auto_open_dev_btn and dev_name == self.__auto_open_dev_btn['text']:
			port_button = self.__auto_open_dev_btn
		
		return port_button
	def add_open_dev(self,dev_name,event_now=None):
		if self.__notebook is None:
			self.show_tips('NoteBook None Error,%s'%dev_name,0)
			return
		tab_add = text_area = None
		tab_normal_show = True
		if not dev_name in self.__dev_open_buttons:
			if dev_name in self.__dev_hide_buttons:
				tab_add,text_area,tab_state = self.__dev_hide_buttons.pop(dev_name)
			else:
				tab_add,text_area = self._get_vscroll_text(self.__notebook)
			self.__dev_open_buttons.setdefault(dev_name,(tab_add,text_area,{'status':'ok'}))
			
			#create the text process queue
			if not dev_name in self.__dev_text_queues:
				self.__dev_text_queues.setdefault(dev_name,ThreadQueue())
			
			#add the tab to the notebook
			self.__notebook.add(tab_add, text=dev_name)
			self.__notebook.tab(tab_add, sticky='nsew')#N+S+E+W
			
			#do not show notify tab on start
			if self.NOTIFY_TAB == dev_name and self.__notify_tab_show is False:
				self.__notebook.tab(tab_add, state='hidden')
				tab_normal_show = False
		else:
			tab_add,text_area,tab_info = self.__dev_open_buttons[dev_name]
			tab_info['status'] = 'ok'
			
		if tab_normal_show is True:
			self.__notebook.tab(tab_add, image=self.__img_gray, compound=Tkinter.LEFT)
			self.__notebook.tab(tab_add, state='normal')
			self.__notebook.select(tab_add)
		
		#set autocomm state to readonly,and save config
		self._set_auto_comm_state(dev_name,event_now)
		
		#reset dev statics info
		if not dev_name in self.__dev_statics_info: 
			self.__dev_statics_info.setdefault(dev_name,{'send':0,'recv':0,'recvTimes':0,'displayLines':0,'displayChars':0,'filebuf':0})
		
		port_button = self.__get_port_button_widget_from_name(dev_name,event_now)
		if port_button:
			port_button['relief'] = Tkinter.SUNKEN
		else:
			self.show_tips("error: can not found (%s)"%dev_name,0)
		
		#do check receive data task schedule
		if self.NOTIFY_TAB != dev_name:
			self.__notebook_dev_connect = True
			self.__notebook_dev_tab_shown = True
			self._cancel_schecule('port-all-close')
			
	def check_need_auto_open_dev(self):
		need_auto_open_dev = None
		if isinstance(self.__auto_open_dev_btn,Tkinter.Button):
			if self.__auto_open_dev_btn['relief'] != Tkinter.RAISED:
				dev_name = self.__auto_open_dev_btn['text']
				if not dev_name in self.__dev_open_buttons or self.__dev_open_buttons[dev_name][2]['status'] == 'disconnect':
					need_auto_open_dev = dev_name
		return need_auto_open_dev
	def check_no_open_dev(self):
		no_open_dev = True
		for dev_name in self.__dev_open_buttons:
			tab_add,text_area,tab_info = self.__dev_open_buttons[dev_name]
			if self.NOTIFY_TAB != dev_name and tab_info['status'] == 'ok':
				no_open_dev = False
				break
		return no_open_dev
		
	def all_dev_tabs_close(self):
		if self.__notebook_dev_tab_shown is False:
			self.do_gui_callback(None,'ports_all_close',cause='no_dev_tabs')
	def all_open_dev_close(self):
		if self.check_no_open_dev() is True:
			self.do_gui_callback(None,'ports_all_close',cause='no_dev_open')
			self._after_schecule('port-all-close',6000,self.all_dev_tabs_close)
	
	def del_open_dev(self,dev_name,event_now=None):
		if self.__notebook is None:
			self.show_tips('NoteBook None Error,%s'%dev_name,0)
			return
		if self.NOTIFY_TAB == dev_name and dev_name in self.__dev_open_buttons:
			self.__notebook.tab(self.__dev_open_buttons[self.NOTIFY_TAB][0], state='hidden')
			self.__notify_tab_show = False
			return
		if dev_name in self.__dev_open_buttons:
			self.__notebook.forget(self.__dev_open_buttons[dev_name][0])
			tab_add,text_area,tab_state = self.__dev_open_buttons.pop(dev_name)
			if dev_name not in self.__dev_hide_buttons:
				text_area.delete(0.0, Tkinter.END)
				self.__dev_hide_buttons.setdefault(dev_name,(tab_add,text_area,tab_state))
				if len(self.__dev_hide_buttons) > 16:
					self.__dev_hide_buttons.popitem()
		
		#remove text Queue
		if dev_name in self.__dev_text_queues:
			del self.__dev_text_queues[dev_name]
		
		#close log file
		self._auto_save_log_file_close(dev_name)
		
		#remove static info
		if dev_name in self.__dev_statics_info: 
			del self.__dev_statics_info[dev_name]
		
		if event_now is not None and event_now.widget == self.__auto_open_dev_btn:
			self.change_readonly_state(self.__auto_open_dev_entry,'normal')
		
		cur_dev = self.get_select_tab_direct()
		if cur_dev is None and self.check_no_open_dev() is True:
			self.__notebook_dev_connect = False
			self.__notebook_dev_tab_shown = False
			self.__text_schedule_count_param = 0
			self._after_schecule('port-all-close',5000,self.all_open_dev_close)
		if cur_dev == self.NOTIFY_TAB and len(self.__notebook.tabs()) == 1:
			self.__notebook_dev_tab_shown = False
		
		print ('dev_connect:%d,dev_show:%d,notify_show:%d'%(self.__notebook_dev_connect,self.__notebook_dev_tab_shown,self.__notify_tab_show))
	def connect_open_dev(self,dev_name,event_now=None):
		if self.__notebook is None:
			self.show_tips('NoteBook None Error,%s'%dev_name,0)
			return
		if dev_name in self.__dev_open_buttons:
			tab_add,text_area,tab_info = self.__dev_open_buttons[dev_name]
			self.__notebook.tab(tab_add, image=self.__img_green, compound=Tkinter.LEFT)
		else:
			print ('unknown start ok dev',dev_name)
	def open_dev_status(self,dev_name,dev_status):
		if dev_name in self.__dev_open_buttons:
			self.submit_control_text(dev_name,"%s========%s DEVICE %s========%s"%(os.linesep,time.strftime("%y-%m-%d %H:%M:%S"),dev_status,os.linesep))
	def disconnect_open_dev(self,dev_name,event_now=None):
		if self.__notebook is None:
			self.show_tips('NoteBook None Error,%s'%dev_name,0)
			return
		if dev_name in self.__dev_open_buttons:
			tab_add,text_area,tab_info = self.__dev_open_buttons[dev_name]
			self.__notebook.tab(tab_add, image=self.__img_red, compound=Tkinter.LEFT)
			tab_info['status'] = 'disconnect'
			self.submit_control_text(dev_name,"%s========%s DEVICE DISCONNECT========%s"%(os.linesep,time.strftime("%y-%m-%d %H:%M:%S"),os.linesep))
		
		port_button = self.__get_port_button_widget_from_name(dev_name,event_now)
		if port_button:
			port_button['relief'] = Tkinter.RAISED
		
		if event_now is not None and event_now.widget == self.__auto_open_dev_btn:
			self.change_readonly_state(self.__auto_open_dev_entry,'normal')
		
		if self.check_no_open_dev() is True:
			self.__notebook_dev_connect = False
			self.__text_schedule_count_param = 0
			if not self.__realtime:
				self._after_schecule('port-all-close',5000,self.all_open_dev_close)
		
	def open_dev_error(self,dev_name):
		if self.__notebook is None:
			self.show_tips('NoteBook None Error,%s'%dev_name,0)
			return
		if dev_name in self.__dev_open_buttons:
			tab_add,text_area,tab_info = self.__dev_open_buttons[dev_name]
			self.__notebook.tab(tab_add, image=self.__img_red_yellow, compound=Tkinter.LEFT)
			tab_info['status'] = 'disconnect'
		
	def get_select_tab(self):
		return self.__notebook_cur_select_dev
	def get_select_tab_direct(self):
		cur_dev = None
		try:
			if self.__dev_open_buttons:
				cur_dev = self.__notebook.tab('current',option='text')
		except Exception as e:
			#print('get_select_tab Exception:%s'%e)
			pass
		return cur_dev
	def get_next_cmd_select(self,cur):
		next_select = 0
		if cur > self.__min_cmd_per_group:
			cur = 1
		elif cur <= 1:
			cur = 1
		
		for i in range(cur,self.__min_cmd_per_group+1):
			cmd_ctx = self.get_cmd_context('CMD', i)
			if cmd_ctx is not None:
				if cmd_ctx['select'].get():
					next_select = i
					break
		if next_select == 0:
			for i in range(1,cur+1):
				cmd_ctx = self.get_cmd_context('CMD', i)
				if cmd_ctx is not None:
					if cmd_ctx['select'].get():
						next_select = i
						break
		return next_select
		
	def reverse_selection(self):
		for i in range(1,self.__min_cmd_per_group+1):
			cmd_ctx = self.get_cmd_context('CMD', i)
			if cmd_ctx is not None:
				if cmd_ctx['select'].get():
					cmd_ctx['select'].set(False)
				elif cmd_ctx['preset'] is True:
					cmd_ctx['select'].set(True)
	def set_selection(self,sel_list):
		for i in range(1,self.__min_cmd_per_group+1):
			cmd_ctx = self.get_cmd_context('CMD', i)
			if cmd_ctx is not None:
				if i in sel_list:
					cmd_ctx['select'].set(True)
				elif cmd_ctx['preset'] is True:
					cmd_ctx['select'].set(False)
	def _calc_auto_send_valiable(self,count_i):
		self.__send_interval_scope['i'] = count_i
		for var_index in range(0,3):
			compiled_rule = self.__send_interval_rule_compile[var_index]
			str_value   = ''
			if compiled_rule is not None:
				try:
					x_value = eval(compiled_rule, self.__safe_scope, self.__send_interval_scope)
					if isinstance(x_value,(str,bytes)) and len(x_value) > 8192:
						x_value = x_value[0:8192]
					str_value = str(x_value) if not isinstance(x_value,str) else x_value
				except Exception as e:
					print ('calc send var exception:%s' %e)
					pass
			cur_var_name = self.__send_interval_var_index_to_name[var_index]
			if self.__send_interval_enable[var_index]:
				self.__send_interval_template_dict[cur_var_name] = str_value
				self.__send_interval_var_value[var_index].set(str_value)
			elif cur_var_name in self.__send_interval_template_dict:
				del self.__send_interval_template_dict[cur_var_name]
				self.__send_interval_var_value[var_index].set('')
			
			self.__send_interval_scope[cur_var_name] = str_value
	def __build_string_template(self,text_str):
		return string.Template(text_str)
	def _get_template_value(self,cur_string_template):
		if not cur_string_template:
			return ''
		return cur_string_template.safe_substitute(self.__send_interval_template_dict)
	
	def _calc_auto_send_init_valiable(self,count_i,check_var_index=None,cur_idx=None):
		for i in range(3):
			self.__send_interval_enable[i] = self.__send_interval_var_enable[i].get()
			self.__send_interval_scope[self.__send_interval_var_index_to_name[i]]=str(i)
		
		if check_var_index is not None:
			self.__send_interval_enable[check_var_index] = bool(self.__send_interval_enable[check_var_index]) != bool(True)
			
		for i in range(3):
			str_rule = self.__send_interval_var_rule[i].get()
			if len(str_rule) > 0:
				try:
					self.__send_interval_rule_compile[i] = compile(str_rule,'','eval')
				except Exception as e:
					print ('Exception(%s) in compile'%e)
					self.__send_interval_rule_compile[i] = None
					pass
			else:
				self.__send_interval_rule_compile[i] = None
		self._calc_auto_send_valiable(count_i)
		if cur_idx is not None:
			_val_name = self.__send_interval_var_index_to_name[cur_idx]
			self.show_tips('$%s: %s'%(_val_name,self.__send_interval_scope[_val_name]),0)
		
	def auto_send_idx_execute(self):
		if self.__auto_send_enable is not True or self.__quit_now is True:
			return
		send_cmd_idx           = self.__cur_auto_send_index
		auto_send_info         = self.__auto_send_cmd_list_info
		next_send_cmd_idx      = send_cmd_idx
		all_task_done          = False
		cmd_ctx = self.get_cmd_context('CMD', send_cmd_idx)
		show_tips_str = ''
		
		if cmd_ctx is not None:
			loop_cnt = self.__auto_send_loop_count
			total_loop_cnt = self.__auto_send_total_loop_count
			self._calc_auto_send_valiable(loop_cnt)
			
			time_out = self.__auto_send_time_interval
			cmd_timeout_limit = cmd_ctx['timeout']
			if cmd_timeout_limit > time_out:
				time_out = cmd_timeout_limit
			
			dev_name = self.get_select_tab()
			if dev_name is not None and dev_name is not self.NOTIFY_TAB and dev_name in self.__dev_open_buttons and self.__dev_open_buttons[dev_name][2]['status'] == 'ok':
				has_var = cmd_info_changed = False
				new_cmd_ver = cmd_ctx['ver']
				if send_cmd_idx not in auto_send_info:
					cmd_info_changed = True
				elif auto_send_info[send_cmd_idx]['has_var']:
					has_var = cmd_info_changed = True
				elif new_cmd_ver > auto_send_info[send_cmd_idx]['ver'] or not auto_send_info[send_cmd_idx]['select']:
					cmd_info_changed = True
				
				if cmd_info_changed is True:
					if has_var:
						new_text = self.get_real_string(self._get_template_value(cmd_ctx['template']) + cmd_ctx['tail'])
					else:
						new_text = self.get_real_string(cmd_ctx['text'].get() + cmd_ctx['tail'])
					real_send_bytes = self.get_bytes_from_string(new_text)
					self.do_gui_callback(None,'auto_send_cmd_idx',port_name=dev_name, cmd_idx=send_cmd_idx-1, text=real_send_bytes)
					auto_send_info[send_cmd_idx]['select'] = True
					auto_send_info[send_cmd_idx]['ver'] = new_cmd_ver
				else:
					self.do_gui_callback(None,'auto_send_cmd_idx',port_name=dev_name, cmd_idx=send_cmd_idx-1)
				self.__auto_send_total_cmd_count += 1
				next_send_cmd_idx = self.get_next_cmd_select(send_cmd_idx+1)
				self.__cur_auto_send_index = next_send_cmd_idx
				if next_send_cmd_idx <= send_cmd_idx:
					self.__auto_send_loop_str.set("%d"%loop_cnt)
					loop_cnt += 1
					self.__auto_send_loop_count = loop_cnt
					if total_loop_cnt > 0 and loop_cnt >= total_loop_cnt:
						all_task_done = True
				show_tips_str = 'Loop: %03d Auto Send Command: %02d '%(loop_cnt,send_cmd_idx)
			else:
				show_tips_str = 'Wait Loop: %03d Auto Send Command: %02d '%(loop_cnt,send_cmd_idx)
				if self.__realtime and time_out < 50:
					time_out = 50
				elif time_out < 500: #atleast wait 0.5 second
					time_out = 500
			
			if all_task_done is True:
				self.show_tips('%s All Task(%d) Done'%(show_tips_str,total_loop_cnt), 0)
			elif self.__auto_send_enable is True:
				next_scheduled = True
				if self._after_schecule('A',time_out, self.auto_send_idx_execute):
					pass
				elif self._after_schecule('A',time_out, self.auto_send_idx_execute):
					pass
				else:
					next_scheduled = False
					print ('add auto send task error')
				
				total_send_cmd_cnt = self.__auto_send_total_cmd_count
				nees_display_tips = False
				if next_scheduled is False:
					self.show_tips('%s Next Schedule: %4d ms cmd: %02d Failed'%(show_tips_str,time_out,next_send_cmd_idx), 0)
				elif time_out >= 500:
					nees_display_tips = True
				elif time_out <= 5:
					if 1 == (total_send_cmd_cnt % 90):
						nees_display_tips = True
				elif time_out <= 10:
					if 1 == (total_send_cmd_cnt % 50):
						nees_display_tips = True
				elif time_out <= 15:
					if 1 == (total_send_cmd_cnt % 30):
						nees_display_tips = True
				elif time_out <= 20:
					if 1 == (total_send_cmd_cnt % 25):
						nees_display_tips = True
				elif time_out <= 30:
					if 1 == (total_send_cmd_cnt % 20):
						nees_display_tips = True
				elif time_out <= 60:
					if 1 == (total_send_cmd_cnt % 10):
						nees_display_tips = True
				elif time_out <= 100:
					if 1 == (total_send_cmd_cnt % 5):
						nees_display_tips = True
				elif time_out <= 200:
					if 1 == (total_send_cmd_cnt % 3):
						nees_display_tips = True
				elif time_out <= 300:
					if 1 == (total_send_cmd_cnt % 2):
						nees_display_tips = True
				if nees_display_tips is True:
					self.show_tips('%s Next Schedule: %4d ms cmd: %02d'%(show_tips_str,time_out,next_send_cmd_idx), 0)
		else: # cmd_ctx is None
			all_task_done = True
		
		if all_task_done is True:
			self.__auto_send_enable = False
			self.__cur_auto_send_index = 0
			self.__auto_send_start_var.set('Auto Send')
			self.__auto_send_ctrl.config(style='stoped.TButton')#lightgreen
			self.__interval_entry_state_set('normal')
	
	def all_task_destroy(self):
		try:
			self.__quit_now = True
			
			#need cancel all sheculed tasks,TODO
			self._cancel_all_schecule()
		except Exception as e:
			print ('all task edstroy err',e)
			pass
		
	def auto_send_loop_ctrl_check(self,event=None):
		if event is not None and self.__auto_send_loop_ctrl is not None:
			self.__auto_send_loop_ctrl.toggle()
		
	def auto_send_ctrl_input_check(self,event):
		l = list(event.widget.get())
		for i in range(len(l) - 1, -1, -1):
			#limit input to number or dot
			if not(48 <= ord(l[i]) <= 57 or ord(l[i]) == 46):
				event.widget.delete(i, i+1)
	def auto_send_ctrl_time_check(self,a=None,b=None,c=None):
		try:
			self.__auto_send_time_interval = int(self.__auto_send_time_interval_var.get())
			self.__auto_send_total_loop_count = int(self.__auto_send_loop_var.get())
		except:
			pass
		if self.__auto_send_time_interval <= 0:
			self.__auto_send_time_interval = 1000
		if self.__auto_send_enable is False:
			if self.__auto_send_time_interval <= 1000:
				self.do_gui_callback(None,'time_interval',time_interval=self.__auto_send_time_interval,auto_send=0,port_name=self.get_select_tab())
			else:#use 0 to set to default value
				self.do_gui_callback(None,'time_interval',time_interval=0,auto_send=0,port_name=self.get_select_tab())
		else:
			self.do_gui_callback(None,'time_interval',time_interval=self.__auto_send_time_interval,auto_send=1,port_name=self.get_select_tab())
		if self.__auto_send_total_loop_count <= 0:
			self.__auto_send_total_loop_count = 0
		
	def __interval_entry_state_set(self,new_state=None):
		for etry in self.__send_interval_entry_list:
			if etry is not None:
				self.change_readonly_state(etry,new_state)
		for cbx in self.__send_interval_checkbox_list:
			if cbx is not None:
				self.change_readonly_state(cbx,new_state)
		self.change_readonly_state(self.__cmd_group_list,new_state)
		
	def __set_default_auto_send_list(self):
		cur_cmd_list_info = []
		local_cmd_list_info = self.__auto_send_cmd_list_info
		for i in range(1,self.__min_cmd_per_group+1):
			cmd_ctx = self.get_cmd_context('CMD', i)
			if cmd_ctx:
				cmd_real_str = self.get_real_string(cmd_ctx['text'].get() + cmd_ctx['tail'])
				_selected = cmd_ctx['select'].get()
				_has_var = False
				for idx,var_name in enumerate(self.__send_interval_var_names):
					var_name_2 = self.__send_interval_var_names_bials[idx]
					if self.__send_interval_enable[idx] and (var_name in cmd_real_str or var_name_2 in cmd_real_str):
						_has_var = True
						break
				real_send_bytes = self.get_bytes_from_string(cmd_real_str)
				local_cmd_list_info[i] =  {'select':_selected,'ver':cmd_ctx['ver'],'has_var':_has_var}
				cur_cmd_list_info.append( {'text':real_send_bytes,'select':_selected,'timeout':cmd_ctx['timeout']} )
			else:
				print('error get cmd_ctx when auto-send %d'%i)
				local_cmd_list_info[i] =  {'select':False,'ver':0,'has_var':False}
				cur_cmd_list_info.append( {'text':b'','select':False,'timeout':1000} )
		
		self.do_gui_callback(None,'cmd_list',cmd_list=cur_cmd_list_info,time_interval=self.__auto_send_time_interval,auto_send=1)
	def auto_send_start_end(self,event=None):
		if self.__toplevel_win_count > 0:
			self.show_tips('please close command editer %d first'%self.__toplevel_win_count,0)
			return
		
		if self.__auto_send_enable is True:
			self.__auto_send_enable = False
			self._cancel_schecule('A') #try cancel previous schedule
			self.do_gui_callback(None,'time_interval',time_interval=self.__auto_send_time_interval,auto_send=0,port_name=self.get_select_tab())
			self.__auto_send_start_var.set('Auto Send')
			self.__auto_send_ctrl.config(style='stoped.TButton')
			self.__interval_entry_state_set('normal')
			self.__auto_send_loop_str.set('LoopTime')
		else:
			self.__auto_send_enable = True
			self.__cur_auto_send_index = self.get_next_cmd_select(0)
			if self.__cur_auto_send_index > 0:
				self.do_gui_callback(None,'time_interval',time_interval=self.__auto_send_time_interval,auto_send=1,port_name=self.get_select_tab())
				self.__set_default_auto_send_list()
				self.__auto_send_loop_count = 0
				self.__auto_send_total_cmd_count = 0
				self.__interval_entry_state_set('disabled')
				self.auto_send_idx_execute()
				self.__auto_send_start_var.set('Stop Send')
				self.__auto_send_ctrl.config(style='running.TButton')
			else:
				self.show_tips('No command selected', 3000)
		
	def comand_list_focus_set(self,keyword=1,type_wiget='entry'):
		ctx = self.get_cmd_context('CMD', keyword)
		if ctx is not None and type_wiget in ctx:
			ctx[type_wiget].focus()
			
	def set_dropdown_callback(self,dropdown_callback):
		self.__drop_down_callback = dropdown_callback
	#def set_task_done_callback(self,taskdone_callback):
	#	self.__taskdone_callback = taskdone_callback
	def set_userlist_callback(self,userlist_callback):
		self.__userlist_callback = userlist_callback
		
	def get_drop_area_wiget(self):
		return self.__auto_parse_area
		
	def drop_enter(self,event):
		#print 'enter'
		self.__auto_parse_area.config(bg='#00FF7F')
		
	def drop_position(self,event):
		print ('position')
	def drop_leave(self,event):
		#print 'leave'
		self.__auto_parse_area.config(bg='#FFFFF0')
		
	def drop_down(self,event):
		if self.__drop_down_callback is not None:
			self.__drop_down_callback(self.__root.tk.splitlist(event.data))
		#print 'drop', self.__root.tk.splitlist(event.data)
			
	def show_tips_area(self):
		b2=ttk.Button(self.__button_frame,text = 'about',width=8,style="fixsize.TButton")
		b2.pack(side=Tkinter.RIGHT, padx=1)
		b2.bind("<Button-1>",self.aboutCallBack)
		b2.bind("<Return>",self.aboutCallBackAuthor)
		b2.bind("<Double-Button-1>",self.aboutCallBackAuthor)
		b2.bind("<Button-2>",self.aboutCallBackAuthor)
		b2.bind("<Button-3>",self.aboutCallBackAuthor)
		self.__about_button = b2
		
		if self.__expert_mode is True:
			b_l=ttk.Button(self.__button_frame,text = '1',width=1,style="fixsize8.TButton")
			b_l.pack(side=Tkinter.RIGHT, padx=1)
			b_l.bind("<Button-1>",lambda e:self.change_font_size(e,8))
			b_l.bind("<Double-Button-1>",lambda e:self.change_font_size(e,8))
			
			b_l=ttk.Button(self.__button_frame,text = '2',width=1,style="fixsize10.TButton")
			b_l.pack(side=Tkinter.RIGHT, padx=1)
			b_l.bind("<Button-1>",lambda e:self.change_font_size(e,10))
			b_l.bind("<Double-Button-1>",lambda e:self.change_font_size(e,10))
			
			b_m=ttk.Button(self.__button_frame,text = '3',width=1,style="fixsize12.TButton")
			b_m.pack(side=Tkinter.RIGHT, padx=1)
			b_m.bind("<Button-1>",lambda e:self.change_font_size(e,12))
			b_m.bind("<Double-Button-1>",lambda e:self.change_font_size(e,12))
			
			b_b=ttk.Button(self.__button_frame,text = '4',width=1,style="fixsize14.TButton")
			b_b.pack(side=Tkinter.RIGHT, padx=1)
			b_b.bind("<Button-1>",lambda e:self.do_gui_callback(e,'start_TLV',var=None))
			b_b.bind("<Button-1>",lambda e:self.change_font_size(e,14))
			b_b.bind("<Double-Button-1>",lambda e:self.change_font_size(e,14))
			
			b_t=ttk.Button(self.__button_frame,text = 'TLV',width=3,style="fixsize10.TButton")
			b_t.pack(side=Tkinter.RIGHT, padx=1)
			b_t.bind("<Button-1>",lambda e:self.do_gui_callback(e,'start_TLV',root=self.__root))
			
		self.__top_tips_var.set('')
		tips_label=Tkinter.Entry(self.__button_frame,justify=Tkinter.CENTER,bd=0,highlightthickness=0,relief='flat',textvariable=self.__top_tips_var, takefocus=0, width=80)#
		tips_label.config(state='readonly')
		tips_label.pack(side=Tkinter.LEFT, padx=2, fill=Tkinter.X,expand=1)
		self.__top_tips_label = tips_label
		
		self.__tips_label = None
		#if self.__tips_label is None:
		#	lb=Entry(self.__top_frame, relief='flat', state='readonly', bd=0, textvariable=self.__tips_var, takefocus=0, highlightthickness=0,justify=CENTER)
		#	lb.pack(side=TOP,fill=BOTH,expand=1)
		#	self.__tips_label = lb
			
	def show_command_group(self,top_frame,**grid_kwargs):
		def down_focus_set(event,list):
			try:
				index = 0
				total = list.size()
				if total > 0:
					index = getint(list.curselection()[0])
				
				if index + 1 >= total:
					self.comand_list_focus_set(1,'entry')
			except:
				print ('down focus error',list)
				pass
		list_height = 8
		if 'listheight' in self.__config:
			try:
				list_height = int(self.__config['listheight'])
			except:
				pass
		
		if self.__cmd_group_list is None:
			#list_box = Listbox(top_frame, listvariable=self.__cmd_group_var, width=18, height=list_height)
			group_list = self.__cmd_group_str_list
			list_box   = ttk.Combobox(top_frame, values=group_list, width=18, state='readonly',postcommand=self.__commbo_display)
			#scroll_bar = ttk.Scrollbar(top_frame)
			#list_box.bind("<Double-Button-1>",self.change_cmd_group)
			#list_box.bind("<Return>",self.change_cmd_group)
			if len(group_list) > 0:
				list_box.current(0)
			list_box.bind("<<ComboboxSelected>>",self.change_cmd_group)
			#list_box.bind("<Left>",lambda event: self.first_dev_focus())
			#list_box.bind("<Down>",lambda event,l=list_box: down_focus_set(event,l))
			#list_box.bind("", self.change_cmd_group)
			#list_box['yscrollcommand'] = scroll_bar.set
			#scroll_bar['command'] = list_box.yview#text_area.yview
			list_box.grid(**grid_kwargs)
			#scroll_bar.pack(side=LEFT,padx=0,fill=Y,expand=0)
			self.__cmd_group_list = list_box
		
	def __commbo_display(self):
		#if sys.version_info.major >= 3:
		return
		if self.__always_top_var.get() > 0:
			self.__root.wm_attributes('-topmost',0)
			
	def __commbo_display_hide(self,event):
		#if sys.version_info.major >= 3:
		return
		if self.__always_top_var.get() > 0:
			self.__root.wm_attributes('-topmost',1)
			
	def show_auto_send_ctrl_box(self,top_frame):
		if self.__auto_send_ctrl is None:
			top_frame.columnconfigure(3, weight=1)
			top_frame.columnconfigure(4, weight=1)
			#top_frame.columnconfigure(2, pad=4)
			#top_frame.rowconfigure(4, pad=4)
			top_frame.rowconfigure(self.__min_cmd_per_group, pad=0)
			
			var_count = 0
			var_names = self.__send_interval_var_names_bials
			if self.__expert_mode is True:
				var_count = len(var_names)
			#variable set control
			frmVar = top_frame
			
			for var_index in range(0,var_count):
				grid_row = var_index + 0
				self.__send_interval_var_enable[var_index].set(0)
				self.__send_interval_var_value[var_index].set('0')
				ckb = ttk.Checkbutton(frmVar, text='%s %s '%(var_names[var_index],'='), width=5, variable=self.__send_interval_var_enable[var_index])
				ckb.bind('<Button-1>', lambda event,cur_idx=var_index: self._calc_auto_send_init_valiable(0,cur_idx))
				#ckb.bind('<ButtonRelease-1>', lambda event,var_i=var_index: self._calc_auto_send_init_valiable(0,var_i))
				ckb.grid(row=grid_row,column=0,sticky=W)
				self.__send_interval_checkbox_list[var_index] = ckb
				
				self.__send_interval_var_combo_list = ('i','2*i+1','3*i*i+2*i+1','4*pow(i,3)+3*pow(i,2)+1','X*2+Y*3','int(X)+int(Y)+int(Z)','hex(i)','bin(i)','int(Y,16)',"ord('A')",'chr(65)','getcmd(i,1)')
				combo_list = self.__send_interval_var_combo_list
				etry = ttk.Combobox(frmVar, textvariable=self.__send_interval_var_rule[var_index],width=10,values=combo_list,postcommand=self.__commbo_display)
				etry.bind('<KeyRelease>', lambda event: self._calc_auto_send_init_valiable(0))
				etry.bind('<Return>', lambda event,cur_idx=var_index: self._calc_auto_send_init_valiable(0,None,cur_idx))
				etry.bind('<<ComboboxSelected>>', lambda event: self._calc_auto_send_init_valiable(0))
				
				etry.grid(row=grid_row,column=1,columnspan=4,sticky=E+W)
				self.__send_interval_entry_list[var_index] = etry
				lb = ttk.Label(frmVar, textvariable=self.__send_interval_var_value[var_index],width=10,font=('Helvetica', 10, 'normal'))
				lb.grid(row=grid_row,column=5,columnspan=2,sticky=E+W)
			
			row_control = var_count
			frm = top_frame #ttk.Frame(top_frame,border=0)
			frmLoop = frm #Frame(frm, bd=0)
			self.__auto_send_loop_str.set('LoopTime')
			lb = ttk.Label(frmLoop, textvariable=self.__auto_send_loop_str,width=8,font=('Helvetica', 10, 'normal'))
			lb.grid(row=row_control,column=0,sticky=W+E)
			
			self.__auto_send_loop_var.set('0')
			loop_etry = ttk.Entry(frmLoop, textvariable=self.__auto_send_loop_var,width=5,font=('Helvetica',10,'normal'))
			loop_etry.bind('<KeyRelease>', self.auto_send_ctrl_input_check)
			#loop_etry.bind('<FocusOut>', self.auto_send_ctrl_time_check)
			self.__auto_send_loop_var.trace_variable('w',self.auto_send_ctrl_time_check)
			#ckb = ttk.Checkbutton(frmLoop, textvariable=self.__auto_send_loop_str, width=9, variable=self.__auto_send_loop_var)
			#loop_etry.bind("<Return>",self.auto_send_loop_ctrl_check)
			loop_etry.grid(row=row_control,column=1,sticky=W+E)
			self.__auto_send_loop_ctrl = loop_etry
			
			frmTime = frm #Frame(frm, bd=0)
			self.__auto_send_time_interval_var.set(self.__auto_send_time_interval)
			etry = ttk.Entry(frmTime, textvariable=self.__auto_send_time_interval_var,width=5,font=('Helvetica',10,'normal'),)
			#etry.bind("<Left>",lambda event: self.self.__cmd_group_list.focus())
			etry.bind('<KeyRelease>', self.auto_send_ctrl_input_check)
			#etry.bind('<Return>', lambda event: self.auto_send_ctrl_time_check(event))
			#etry.bind('<FocusOut>', lambda event: self.auto_send_ctrl_time_check(event))
			self.__auto_send_time_interval_var.trace_variable('w',self.auto_send_ctrl_time_check)
			etry.grid(row=row_control,column=2,sticky=W+E)
			self.__auto_send_time_ctrl = etry
			lb = ttk.Label(frmTime, text='ms',width=3,font=('Helvetica', 10, 'normal'))
			lb.grid(row=row_control,column=3,sticky=W+E)
			
			frmSend = frm #Frame(frm, bd=0)
			self.__auto_send_start_var.set('Auto Send')
			btn = ttk.Button(frmSend, textvariable=self.__auto_send_start_var, width=9, style='stoped.TButton' )
			btn.bind("<Return>",self.auto_send_start_end)
			btn.bind("<Button-1>",self.auto_send_start_end)
			btn.bind("<Left>",lambda event: self.first_dev_focus())
			btn.bind("<Down>",lambda event: self.comand_list_focus_set(1,'entry'))
			btn.grid(row=row_control,column=4,columnspan=2,sticky=E+W)
			self.__auto_send_ctrl = btn
			#reserse select
			ckb = ttk.Checkbutton(frmSend, text="", variable=self.__auto_send_reverse,command=self.reverse_selection)
			ckb.bind("<Return>",self.reverse_selection)
			ckb.grid(row=row_control,column=6)
			
	def show_auto_parse_area(self,top_frame,**grid_kwargs):
		if self.__auto_parse_area is None:
			frm = Tkinter.Frame(top_frame, width=50) #bg='#FFFFF0',
			frm.grid(**grid_kwargs)
			try:
				if hasattr(frm,'drop_target_register') and hasattr(frm,'dnd_bind') and hasattr(frm,'drag_source_register'):
					frm.drop_target_register('*')
					frm.dnd_bind('<<DropEnter>>', self.drop_enter)
					#frm.dnd_bind('<<DropPosition>>', self.drop_position)
					frm.dnd_bind('<<DropLeave>>', self.drop_leave)
					frm.dnd_bind('<<Drop>>', self.drop_down)
					# make the listbox a drag source
					frm.drag_source_register(1, self.CF_UNICODETEXT)
				else:
					print ('no drag attribute found')
			except Exception as e:
				print ('no drag and drop support. exception %s'%e)
				pass
			#add get user list callback
			frm.bind("<Button-3>",lambda event:self.__userlist_callback())
			self.__auto_parse_area = frm
			
	def __check_filter_param(self,i):
		text_filter_param = self.__text_filter_str[i]
		if not isinstance(text_filter_param,str):
			text_filter_param = self.__filter_text_var[i].get()
		if not text_filter_param:
			return 0x00
		if self.__filter_pattern_sel[i] <= 0:
			return 0x00
		filter_value_valid = True
		if self.__filter_pattern_sel[i] == self.FILTER_MATCH_IDLE_TIME:
			if not text_filter_param.isdigit():  #idleTime 
				return 0x00
			self.__filter_execute_timestamp[i] = time.time()#add time stamp, to prevent first add from actions_idle_task_check 
			self.do_filter_start_idle_task(i,int(text_filter_param))
			self.__text_filter_str[i] = text_filter_param
		elif self.__filter_pattern_sel[i] == self.FILTER_MATCH_REGEXP: #regExp
			try:
				import re
				self.__text_filter_str[i] = re.compile(text_filter_param)
				print ('compile filter re ok')
				self.show_tips('filter regexp %d ok'%i,0)
			except Exception as e:
				filter_value_valid = False
				print ('compile re %d fail:%s'%(i,e))
				self.show_tips('filter exp %d fail:%s'%(i,e),0)
				pass
		else:
			self.__text_filter_str[i] = self.get_real_string(text_filter_param)
		return 0x10 if filter_value_valid else 0x00
	def __val_filter_trace_callback(self,i):
		self.__text_filter_str[i] = self.__filter_text_var[i].get()
		self.__text_filter_valid_bits[i] = (self.__text_filter_valid_bits[i]&0x0f) | self.__check_filter_param(i)
	def __filter_combo_selected(self,i,e):
		self.__filter_pattern_sel[i] = self.__filter_combo[i].current()
		self.__text_filter_valid_bits[i] = (self.__text_filter_valid_bits[i]&0x0f) | self.__check_filter_param(i)
	def __filter_combo_action_selected(self,i,e):
		self.__filter_actions_sel[i] = self.__filter_action_combo[i].current()
		self.__text_filter_valid_bits[i] = (self.__text_filter_valid_bits[i]&0xf0) | self.__check_filter_action_param(i)
	def __val_filter_action_trace_callback(self,i):
		self.__filter_actions_param[i] = self.__filter_action_param_var[i].get()
		self.__text_filter_valid_bits[i] = (self.__text_filter_valid_bits[i]&0xf0) | self.__check_filter_action_param(i)
	def __check_filter_action_param(self,i):
		if self.__filter_actions_sel[i] <= 0:
			return 0x00
		if self.__filter_actions_sel[i] != self.FILTER_ACTION_DOPROCESS:
			return 0x01
		
		module_sep_index =  self.__filter_actions_param[i].find('::')
		if module_sep_index <= 0:#can use only small inside functions
			self.show_tips('use simple expressions to process R%d, or use (extmodule.py::func) to process the data'%i,0)
			return 0x01
		ext_module = self.__filter_actions_param[i][0:module_sep_index]
		ext_module_upper = ext_module.upper()
		if ext_module_upper.endswith('.DLL') or ext_module_upper.endswith('.SO'):
			if self._do_load_external_module(ext_module):
				return 0x01
		elif ext_module_upper.endswith('.PY') or ext_module_upper.endswith('.PYC'):
			if self._do_load_external_py_module(ext_module):
				return 0x01
		elif os.path.exists('%s.dll'%ext_module):
			if self._do_load_external_module('%s.dll'%ext_module):
				return 0x01
		elif os.path.exists('%s.so'%ext_module):
			if self._do_load_external_module('%s.so'%ext_module):
				return 0x01
		#not valid exter module
		self.show_tips('can also use ([extmodule.py|extmodule.dll|extmodule.so]::func) to process the data',0)
		return 0x00
	def show_filter_box(self,top_frame):
		top_frame.columnconfigure(2, weight=1)
		top_frame.columnconfigure(5, weight=1)
		text_var_count = self.DEFAULT_FILTERS
		if self.__expert_mode is True:
			text_var_count = self.MAX_FILTERS
			self.__filter_real_count = text_var_count
		for i in range(0,text_var_count):
			match_pattan = self.__filter_match_pattan
			pattanCombo = ttk.Combobox(top_frame,state='readonly', width=12,values=match_pattan, postcommand=self.__commbo_display)
			self.__filter_combo[i] = pattanCombo
			pattanCombo.grid(row=i,column=0)
			pattanCombo.bind('<<ComboboxSelected>>',lambda e,idx=i:self.__filter_combo_selected(idx,e))
			pattanCombo.current(0)
			
			self.__filter_text_var[i].set('')
			lb = ttk.Entry(top_frame, textvariable = self.__filter_text_var[i])
			self.__filter_text_var[i].trace_variable('w',lambda a,b,c,idx=i: self.__val_filter_trace_callback(idx))
			lb.grid(row=i,column=1,columnspan=2,sticky=W+E)
			
			filter_actions = self.__filter_actions
			actionsCombo = ttk.Combobox(top_frame,state='readonly', width=12,values=filter_actions, postcommand=self.__commbo_display)
			self.__filter_action_combo[i] = actionsCombo
			actionsCombo.grid(row=i,column=3)
			actionsCombo.bind('<<ComboboxSelected>>',lambda e,idx=i,:self.__filter_combo_action_selected(idx,e))
			actionsCombo.current(0)
			
			self.__filter_action_param_var[i].set('')
			lb = ttk.Entry(top_frame, textvariable = self.__filter_action_param_var[i])
			self.__filter_action_param_var[i].trace_variable('w',lambda a,b,c,idx=i: self.__val_filter_action_trace_callback(idx))
			lb.grid(row=i,column=4,columnspan=2,sticky=W+E)
			
		
	def show_text_ctrl_box(self,top_frame,**grid_kw):
		text_clear_btn = ttk.Button(top_frame, text="Clear", width=6,style="fixsize.TButton")
		text_clear_btn.bind('<Button-1>',self.clear_text)
		text_clear_btn.grid(padx=10,column=1,**grid_kw)
		
		send_file_btn = ttk.Button(top_frame, text="SendFile", width=8,style="fixsize.TButton")
		send_file_btn.bind('<Button-1>', self.select_send_file)
		send_file_btn.bind('<Button-3>', self.select_send_zmodem)
		send_file_btn.grid(padx=10,column=2,**grid_kw)
		
		text_filter_btn = ttk.Button(top_frame, text="Actions", width=7,style="fixsize.TButton")
		text_filter_btn.bind('<Button-1>',self.show_exclude_filter_frame_toggle)
		text_filter_btn.grid(padx=4,column=3,**grid_kw)
		
		self.__text_extend_var.set('ExCmd>>')
		extend_cmd_btn = ttk.Button(top_frame, textvariable=self.__text_extend_var, width=7,style="fixsize.TButton")
		extend_cmd_btn.bind('<Button-1>',self.show_right_frame_toggle)
		extend_cmd_btn.grid(padx=4,column=4,**grid_kw)
		
	def show_send_box(self,top_frame):
		def do_send_envent(event,v):
			cmd_ctx = {'text':v, 'tail':self.__send_text_tail_var.get()}
			if self.__send_format_hex_var.get() > 0:
				#Hex mode, convert Hex to normal text first
				hex_str = v.get()
				normal_str = self.change_hex_to_ascii(hex_str,r' ')
				self.__send_normal_text_var.set(normal_str)
				cmd_ctx['text'] = self.__send_normal_text_var
			
			self.text_scroll_disable_set(event,False,'box-send',True)
			self.__do_send_command(event,cmd_ctx)
			history_list = self.__history_cmd_list
			
			real_val = cmd_ctx['text'].get()
			real_val = self.change_ascii_to_repr_display(real_val)
			if real_val not in history_list:
				history_list.insert(0, real_val)
			elif real_val != history_list[0]:
				history_list.remove(real_val)
				history_list.insert(0, real_val)
			
			if len(history_list) > 16:
				history_list.pop()
			
			if self.__send_frame_entry is not None:
				#print len(total_cmd_list), len(set(total_cmd_list))
				if self.__send_format_hex_var.get() == 0:
					self.__send_frame_entry.set_completion_list(history_list)
					self.__send_frame_entry.set_snd_completion_list(self.__default_auto_complete_cmd_list)
				self.__send_frame_entry['values'] = history_list
			#print (self.__history_cmd_list)
		def sendbox_do_calc_or_send(event,v,force_calc=None):
			#no dev connect and auto_send not active,try eval
			cur_dev = self.get_select_tab()
			if force_calc is True or ((cur_dev is None or cur_dev == self.NOTIFY_TAB) and (self.__auto_send_enable is False)):
				try:
					str_rule = v.get()
					if str_rule:
						compiled_rule = compile(str_rule,'','eval')
						self._calc_auto_send_valiable(0)
						x_value = eval(compiled_rule, self.__safe_scope, self.__send_interval_scope)
						if x_value is not None:
							self.submit_control_text('calc',"\n%s=\n%s\n"%(str_rule,x_value))
							if cur_dev != self.NOTIFY_TAB:
								self.__notebook.select(self.__dev_open_buttons[self.NOTIFY_TAB][0])
						else:
							self.show_tips('do %s'%str_rule,0)
				except Exception as e:
					print ('Exception(%s) in compile'%e)
					self.submit_control_text('calc',"\n%s error:%s\n"%(str_rule,e))#
					pass
			else:
				do_send_envent(event,v)
				self.__send_frame_entry.select_range(0,Tkinter.END)
		def focus_up_last_cmd():
			if self.check_visible(self.__right_frame) is True:
				self.comand_list_focus_set(self.__min_cmd_per_group,'button')
		def combox_selected(event):
			#print 'combox selected',event
			self.__send_format_hex_var.set(0)
			self.__send_frame_entry.set_input_hex_mode(False)
		frm_send = ttk.Frame(top_frame)
		frm_send_ctrl = ttk.Frame(top_frame)
		self.__send_text_var.set('')
		self.__send_text_var.trace_variable('w',lambda a,b,c: self._val_sendbox_trace_callback(self.__send_text_var))
		#send input entry
		send_ery = AutocompleteCombobox(frm_send, textvariable = self.__send_text_var, font=('Helvetica',self.__font_size*2,'normal'),postcommand=self.__commbo_display)
		send_ery.bind_auto_key_event()
		send_ery.set_input_hex_mode(False)
		send_ery.set_completion_list(self.__default_auto_complete_cmd_list)
		send_ery.set_third_completion_list(self.__total_auto_complete_cmd_list)
		send_ery.bind('<Return>', lambda event,v=self.__send_text_var: sendbox_do_calc_or_send(event,v))
		send_ery.bind('<Control-Key-Return>', lambda event,v=self.__send_text_var: sendbox_do_calc_or_send(event,v,True))
		send_ery.bind('<<ComboboxSelected>>', lambda event: combox_selected(event))
		send_ery.pack(side=Tkinter.LEFT,fill=Tkinter.BOTH,expand=1)
		#send_ery.grid(rows=2,row=1,rowspan=2,column=1)
		self.__send_frame_entry = send_ery
		#send control options
		if sys.version_info.major < 3 and sys.version_info.minor ==7 and sys.version_info.micro < 10:
			self.__cmd_tail_combo_list = (r'\\r\\n',r'\\r',r'\\n',r'')
		else:
			self.__cmd_tail_combo_list = (r'\r\n',r'\r',r'\n',r'')
		cmbEditCombo = ttk.Combobox(frm_send_ctrl, textvariable=self.__send_text_tail_var,width=4,values=self.__cmd_tail_combo_list,postcommand=self.__commbo_display)
		cmbEditCombo.current(0)
		cmbEditCombo.grid(row=1,column=1)
		hex_send_check_btn = ttk.Checkbutton(frm_send_ctrl, text="HEX", variable=self.__send_format_hex_var, width=4, command=self.change_send_box_mode)
		hex_send_check_btn.grid(row=2,column=1)
		
		#send button
		lb = ttk.Button(frm_send, text='Send',width=5,style="send.TButton")
		lb.bind('<Button-1>', lambda event,v=self.__send_text_var: do_send_envent(event,v))
		lb.bind('<Button-3>', lambda event,v=self.__send_text_var: sendbox_do_calc_or_send(event,v,True))
		lb.bind('<Return>', lambda event,v=self.__send_text_var: sendbox_do_calc_or_send(event,v))
		lb.bind('<Up>', lambda event: focus_up_last_cmd())
		lb.bind('<Left>', lambda event,e=send_ery: e.focus())
		lb.pack(side=Tkinter.LEFT,padx=2,fill=Tkinter.Y,expand=0)
		#lb.grid(rows=2,row=1,rowspan=2,column=2)
		frm_send.pack(side=Tkinter.LEFT,fill=Tkinter.BOTH,expand=1)
		frm_send_ctrl.pack(side=Tkinter.RIGHT,fill=Tkinter.Y,expand=0)
	def check_visible(self,wi):
		be_visible = False
		try:
			if wi.winfo_viewable() > 0:
				be_visible = True
		except:
			be_visible = False
			pass
		#print (be_visible,wi.winfo_viewable())
		return be_visible
			
	def show_exclude_filter_frame_toggle(self,event):
		if self.__filter_frame_pack is True:
			self.__filter_frame.grid_remove()
			#event.widget['relief'] = SUNKEN
			self.__filter_frame_pack = False
		else:
			self.__filter_frame.grid(row=6,column=0,columnspan=5,sticky=E+W)
			#event.widget['relief'] = RAISED
			self.__filter_frame_pack = True
		#return 'break'
		
	def show_send_frame_toggle(self,event):
		if self.__send_frame_pack is True:
			self.__send_frame.grid_remove()
			#event.widget['relief'] = SUNKEN
			self.__send_frame_pack = False
		else:
			self.__send_frame.grid(row=5,column=0,columnspan=5,sticky=E+W)
			#event.widget['relief'] = RAISED
			self.__send_frame_pack = True
		#return 'break'
		
	def dev_frame_auto_hide_check(self):
		if self.__auto_hide_dev_enable_var.get() == 0:
			return
		dev_com_visible = self.check_visible(self.__left_top_frame)
		
		if self.get_select_tab() is None:
			#no open dev now, should show the dev frame
			if dev_com_visible is False:
				self.show_dev_frame_toggle(None)
			return
		
		#already has dev open
		if self.__dev_mouse_on['com_dev'] is False and \
			self.__dev_mouse_on['net_dev'] is False and self.__dev_mouse_on['setting'] is False and self.__dev_mouse_on['text_title'] is False:
			#no mouse on, try auto hide the frame
			if dev_com_visible is True:
				self.show_dev_frame_toggle(None)
		elif dev_com_visible is False and self.__dev_mouse_on['text_title_s'] is True:
				self.show_dev_frame_toggle(None)
		
	def show_dev_frame_toggle(self,event):
		if self.check_visible(self.__left_top_frame) is True:
			self.__left_top_frame.grid_remove()
		else:
			com_dev_list = self.get_dev_names(self.__serial_common_name)
			if self.__expert_mode is False and len(com_dev_list) <= 8:
					self.build_dev_dict(self.get_dev_names(self.__net_common_name), self.__net_key_word)
					self.show_dev_dict(self.__net_key_word, self.open_or_close_port, self.__left_top_frame_net)
					self.__net_dev_cur_show = True
			self.__left_top_frame.grid(row=0,rowspan=8,column=0,columnspan=3,sticky=E+W)
		#return 'break'
		
	def show_dev_frame(self,event=None):
		if self.check_visible(self.__left_top_frame) is not True:
			self.__left_top_frame.grid(row=0,rowspan=8,column=0,columnspan=3,sticky=E+W)
			
	def show_right_frame_toggle(self,event):
		self.__root.update()
		if self.__right_frame_pack is True:
			#r_width = self.__right_frame.winfo_width()
			
			#t_width = self.__root.winfo_width()
			#t_height = self.__root.winfo_height()
			#t_x = self.__root.winfo_x()
			#t_y = self.__root.winfo_y()
			#print ('H m, mh, r, r_req',m_width,m_height,r_width,t_reqheight)
			
			self.__main_paned_frame.remove(self.__right_frame)
			
			#self.__root.geometry(str(t_width-r_width)+'x'+str(t_height)+'+'+str(t_x)+'+'+str(t_y))
			self.__text_extend_var.set('ExCmd<<')
			self.__right_frame_pack = False
		else:
			#r_reqwidth = self.__right_frame.winfo_reqwidth()
			#delta_width = r_reqwidth
			
			#print ('H r_req, r, l_req, l, delta',r_reqwidth,r_width,l_reqwidth,l_width,delta_width)
			#if delta_width > 0:
			#	t_width = self.__root.winfo_width()
			#	t_height = self.__root.winfo_height()
			#	t_reqheight = self.__root.winfo_reqheight()
			#	t_x = self.__root.winfo_x()
			#	t_y = self.__root.winfo_y()
			#	#self.__root.geometry(str(t_width+delta_width)+'x'+str(t_height)+'+'+str(t_x)+'+'+str(t_y))
			
			self.__main_paned_frame.add(self.__right_frame,stretch="always",minsize="200")
			#self.__root.update()
			self.__right_frame_pack = True
			
			self.__text_extend_var.set('ExCmd>>')
			#event.widget['relief'] = RAISED
		#return 'break'
			
	def text_scroll_disable_set(self,event,scroll_disable,_cause,tips_disable=None):
		self.__text_scroll_disable = scroll_disable
		
		if tips_disable is True:
			return
		elif scroll_disable is True:
			self.show_tips('text scroll disable', 3000)
		else:
			self.show_tips('text scroll enable', 3000)
	def first_dev_focus(self):
		if self.__last_dev is not None and self.check_visible(self.__left_top_frame_com) is True:
			try:
				self.__last_dev['button'].focus()
			except:
				self.__about_button.focus()
				print ('first dev focus error')
				pass
		else:
			self.__about_button.focus()
	def list_box_focus(self):
		if self.check_visible(self.__right_frame) is True:
			self.__cmd_group_list.focus()
		else:
			self.__send_frame_entry.focus()
		return 'break'
		
	def change_ascii_to_repr_display(self,ascii_str):
		return ascii_str.replace('\\',r'\\')
	def change_hex_to_ascii_v2(self,hex_str,seprator_char):
		HexCharArry = hex_str.split(seprator_char)
		asciiCharArray = ''
		for cmdChar in HexCharArry:
			if len(cmdChar) >= 1:
				numCode = int(cmdChar,16)
				if numCode > 256:
					if sys.version_info.major >= 3:
						chrCode = chr(numCode)
					else:
						chrCode = unichr(numCode)
				elif numCode >= 0x20 and numCode < 127:
					chrCode = chr(numCode)
				else:
					chrCode = r'\x%02X'%numCode
				#print (cmdChar,numCode,chrCode)
				asciiCharArray += chrCode
		return asciiCharArray
	def change_str_to_hex_v2(self,ascii_str,seprator_char):
		#ord('a') chr(65) unichr(65)
		hexCharArray = ''
		real_str = self.get_real_string(ascii_str)
		for ascii_chr in real_str:
			hexInt = ord(ascii_chr)
			if hexInt <= 0xff:
				hexChar = '%02X'%hexInt#int(hexInt,16)
			else:
				hexChar = '%04X'%hexInt#int(hexInt,16)
			#print (type(ascii_chr),ascii_chr,hexInt,hexChar)
			hexCharArray = hexCharArray + hexChar + seprator_char
		return hexCharArray
		
	def change_hex_to_str(self,hex_str,seprator_char):
		HexCharArry = hex_str.split(seprator_char)
		str_list = []
		for cmdChar in HexCharArry:
			chr_code = int(cmdChar,16)
			one_chr = chr(chr_code)
			str_list.append(one_chr)
			
		return "".join(str_list)
	def change_str_to_hex(self,str_in,seprator_char):
		bytes_list = []
		real_str = self.get_real_string(str_in)
		for one_chr in real_str:
			#chr_bytes = one_chr.encode()
			#chr_hex = int.from_bytes(chr_bytes,byteorder='big')
			chr_code = ord(one_chr)
			bytes_list.append('%x'%chr_code)
			
		return seprator_char.join(bytes_list)
	
	def change_ascii_to_hex(self,ascii_str,seprator_char):
		return self.change_str_to_hex_v2(ascii_str,seprator_char)
		
	def change_hex_to_ascii(self,hex_str,seprator_char):
		return self.change_hex_to_ascii_v2(hex_str,seprator_char)
		
	def change_send_box_mode(self):
		if self.__send_format_hex_var.get() > 0:
			#HEX mode
			send_str = self.__send_text_var.get()
			hex_str = self.change_ascii_to_hex(send_str,r' ')
			self.__send_text_var.set(hex_str)
			self.__send_frame_entry.set_input_hex_mode(True)
			#self.__send_frame_entry['values'] = self.__history_hex_cmd_list
		else:
			#normal ASCII mode
			send_str = self.__send_text_var.get()
			ascii_str = self.change_hex_to_ascii(send_str,r' ')
			self.__send_text_var.set(ascii_str)
			self.__send_frame_entry.set_input_hex_mode(False)
			#self.__send_frame_entry['values'] = self.__history_cmd_list
	def _notebook_selected(self,event):
		self.__notebook_cur_select_dev = self.get_select_tab_direct()
	def _notebook_tab_clicked(self,event,hide_tips=None):
		try:
			tab_name = self.__notebook.tab('@%d,%d'%(event.x, event.y), option='text')
			key = self.get_dev_dictkey(self.__serial_common_name,tab_name,0)
			if key is not None and hide_tips is not True:
				self.show_tips(self.__dev_dict[self.__serial_common_name][key]['description'].get(), 6000)
		except Exception as e:
			#print ('notebook_click Exception %s\n'%e)
			pass
	def _notebook_tab_right_clicked(self,event):
		try:
			tab_name = self.__notebook.tab('@%d,%d'%(event.x, event.y), option='text')
			cur_widget = event.widget
			cur_widget.clipboard_clear()
			cur_widget.clipboard_append(tab_name)
			self.show_tips( "%s copyed to clipboard"%tab_name, 6000)
		except Exception as e:
			print ('notebook_click Exception %s\n'%e)
			pass
	def _notebook_double_clicked(self,event):
		tab_identify = self.__notebook.identify(event.x, event.y)
		if len(tab_identify) > 0:
			try:
				tab_name = self.__notebook.tab('@%d,%d'%(event.x, event.y), option='text')
				port_button = self.__get_port_button_widget_from_name(tab_name,event)
				if self.NOTIFY_TAB == tab_name and tab_name in self.__dev_open_buttons:
					self.__notebook.tab(self.__dev_open_buttons[self.NOTIFY_TAB][0], state='hidden')
					self.__notify_tab_show = False
				elif port_button is not None:
					self.closePort(tab_name)
					self.del_open_dev(tab_name,event)
				elif tab_name in self.__dev_open_buttons:
					self.del_open_dev(tab_name,event)
				else:
					print (tab_name,'click else')
				#btn.bind("<Double-Button-1>",lambda event,w=event_now.widget: w.event_generate('<Button-1>', x=0, y=0))
			except Exception as e:
				#print ('notebook_double_click Exception %s\n'%e)
				pass
		else:
			self.show_dev_frame_toggle(event)
		
	def show_text_nodebook(self,top_frame):
		if self.__notebook is None:
			text_width = 800
			if 'textwidth' in self.__config and self.__config['textwidth'].isdigit():
				text_width = int(self.__config['textwidth']) % 4096
				if text_width < 500:
					text_width = 500
			self.__notebook = ttk.Notebook(top_frame,width=text_width)
			self.add_open_dev(self.NOTIFY_TAB)
			
			self.__notebook.bind('<<NotebookTabChanged>>',self._notebook_selected)
			self.__notebook.bind('<Button-1>',self._notebook_tab_clicked)
			self.__notebook.bind('<Button-3>',self._notebook_tab_right_clicked)
			self.__notebook.bind('<Double-Button-1>',self._notebook_double_clicked)
			self.__notebook.grid(row=0,column=0,columnspan=5,sticky=N+S+E+W)
			self.__notebook.enable_traversal()
			self.show_text_ctrl_box(top_frame,row=1,sticky=E)
	
	def clear_text(self,port_name):
		if self.__notebook is not None:
			dev_name = self.get_select_tab_direct()
			if dev_name is not None and dev_name in self.__dev_open_buttons:
				self.__dev_open_buttons[dev_name][1].delete(0.0, Tkinter.END)
				if dev_name in self.__dev_statics_info:
					self.__dev_statics_info[dev_name]['displayChars'] = 0
					self.__dev_statics_info[dev_name]['displayLines'] = 0
		
	def select_send_file(self,event):
		self.__send_format_hex_var.set(0)
		self.__send_frame_entry.set_input_hex_mode(False)
		self.__send_file_idx += 1
		self.__send_file_idx %= len(self.__send_file_name)
		self.__send_text_var.set('sendFile("%s")'%self.__send_file_name[self.__send_file_idx])
		self.show_tips('right click the SEND button(or CTRL+ENTER) to do sendFile("fileName") command',0)
	def select_send_zmodem(self,event):
		self.__send_format_hex_var.set(0)
		self.__send_frame_entry.set_input_hex_mode(False)
		self.__send_zmodem_idx += 1
		self.__send_zmodem_idx %= len(self.__send_zmodem_file_path)
		self.__send_text_var.set('sendZmodem("%s")'%self.__send_zmodem_file_path[self.__send_zmodem_idx])
		self.show_tips('right click the SEND button(or CTRL+ENTER) to do sendZmodem("folderOrFilePath") command',0)
	def get_send_encoding(self):
		return self.__config['send_encoding'] if 'send_encoding' in self.__config else 'utf-8'
	def get_display_encoding(self):
		return self.__config['display_encoding'] if 'display_encoding' in self.__config else 'utf-8'
	def __convert_single_byte_char_code_list_to_bytes(self,single_byte_char_code_list):
		return bytes(single_byte_char_code_list)
	def __convert_multi_byte_char_list_to_bytes(self,multi_byte_char_list,encoding):
		multi_byte_str = ''.join(multi_byte_char_list)
		bytes_of_multi_bytes_char_list = self.__try_the_encoding(multi_byte_str,encoding)
		if bytes_of_multi_bytes_char_list is None:
			raise Exception('can not encode(%s) in encoding(%s)'%(multi_byte_str,encoding))
		return bytes_of_multi_bytes_char_list
	def get_bytes_from_string(self,send_str):
		bytes_list = []
		single_byte_code_list = []
		multi_byte_char_list = []
		send_encoding = self.get_send_encoding()
		keep_ascii_utf8 = self.__keep_ascii_single_byte.get()
		char_code_list = []
		for char in send_str:
			code_val = ord(char)
			if keep_ascii_utf8 > 0 and code_val <= 255:
				if multi_byte_char_list:
					bytes_list.append(self.__convert_multi_byte_char_list_to_bytes(multi_byte_char_list,send_encoding))
					multi_byte_char_list = []
				single_byte_code_list.append(code_val)
			else:
				if single_byte_code_list:
					bytes_list.append(self.__convert_single_byte_char_code_list_to_bytes(single_byte_code_list))
					single_byte_code_list = []
				multi_byte_char_list.append(char)
		if single_byte_code_list:
			bytes_list.append(self.__convert_single_byte_char_code_list_to_bytes(single_byte_code_list))
		if multi_byte_char_list:
			bytes_list.append(self.__convert_multi_byte_char_list_to_bytes(multi_byte_char_list,send_encoding))
		return b''.join(bytes_list)
	def get_real_string(self,send_str):
		real_send_str_list = []
		send_str = send_str.replace(r'\r','\r')
		send_str = send_str.replace(r'\n','\n')
		send_str = send_str.replace(r'\f','\f')
		send_str = send_str.replace(r'\t','\t')
		send_str = send_str.replace(r'\v','\v')
		send_str = send_str.replace(r"\'","\'")
		send_str = send_str.replace(r'\"','\"')
		send_str = send_str.replace(r'\b','\b')
		send_str = send_str.replace(r'\000','\000')
		send_str = send_str.replace(r'\\','\\')
		
		def isHex(ch):
			if ch >= 'A' and ch <= 'F':
				return True
			elif ch >= 'a' and ch <= 'f':
				return True
			elif ch.isdigit() is True:
				return True
			return False
		
		i = 0
		str_len = len(send_str)
		#print ('M:',send_str,str_len)
		while i <= str_len-4:
			if send_str[i] == '\\' and send_str[i+1] == 'x' and isHex(send_str[i+2]) and isHex(send_str[i+3]):
				o_str = send_str[i+2]+send_str[i+3]
				r_str = chr(int(o_str,16)) #bytes.fromhex(o_str).decode('utf-8')#o_str.decode('Hex')
				i += 4
				real_send_str_list.append(r_str)
			else:
				real_send_str_list.append(send_str[i])
				i += 1
		else:
			if i < str_len:
				real_send_str_list.append(send_str[i:str_len])
		return "".join(real_send_str_list)
		
	def do_filter_start_idle_task(self,i,idle_time_s):
		self._after_schecule('IDLE-FILTER',1000,self.actions_idle_task_check)
	def actions_idle_task_check(self):
		if self.__filter_frame_pack is False or not 0x11 in self.__text_filter_valid_bits:
			return
		self.__filter_idle_task_count += 1
		cur_timestamp = time.time()
		for i in range(0,self.__filter_real_count):
			cur_pattern = self.__filter_pattern_sel[i]
			if cur_pattern == self.FILTER_MATCH_IDLE_TIME and self.__text_filter_str[i].isdigit(): #idleTime
				idle_time_s = int(self.__text_filter_str[i])
				#check if idle task time passed twice
				if self.__filter_idle_task_count > 0 and idle_time_s > 0 and (self.__filter_idle_task_count % idle_time_s) == 0:
					cur_action = self.__filter_actions_sel[i]
					#do not trigle idle task while aready in autosend mode
					if self.__auto_send_enable is False and self.__filter_frame_pack is True:
						if cur_action == self.FILTER_ACTION_SEND: #send
							print ('filter idle %d %ds send'%(i,idle_time_s))
							self.do_filter_send_event(None,i,None)
						elif cur_action == self.FILTER_ACTION_AUTO_SEND: #auto send
							print ('filter idle %d %ds auto send'%(i,idle_time_s))
							self.do_filter_auto_send_event(None,i)
						elif cur_action == self.FILTER_ACTION_SENDTO: #SendTo
							print ('filter idle %d %ds sendTo'%(i,idle_time_s))
							self.do_filter_send_to_event(None,i,None)
						elif cur_action == self.FILTER_ACTION_DOPROCESS:
							self.do_filter_process_send_event(None,i,None)
		self._after_schecule('IDLE-FILTER',1000,self.actions_idle_task_check)
		
	def _do_load_external_py_module(self,ext_module):
		load_result = True
		pure_module_name = ext_module[0:ext_module.rfind('.')]
		try:
			if ext_module not in self.__filter_external_module:
				cur_path = os.path.abspath('.')
				plugins_path = os.path.join(cur_path,'plugins')
				if plugins_path not in sys.path:
					sys.path.append(plugins_path)
				module_handle = __import__(pure_module_name,self.__send_interval_scope)
				modify_fime = os.stat(module_handle.__file__).st_mtime if hasattr(module_handle,'__file__') else 0
				self.__filter_external_module.setdefault(ext_module,(module_handle,None,None,None,None,modify_fime))
				self.show_tips('load module %s success'%ext_module, 0)
			else:
				module_handle = self.__filter_external_module[ext_module][0]
				modify_fime = os.stat(module_handle.__file__).st_mtime if hasattr(module_handle,'__file__') else 0
				if modify_fime != self.__filter_external_module[ext_module][5]:
					if pure_module_name in sys.modules:
						del sys.modules[pure_module_name]
					del self.__filter_external_module[ext_module]
					del module_handle
					module_handle = __import__(pure_module_name,self.__send_interval_scope)
					self.__filter_external_module.setdefault(ext_module,(module_handle,None,None,None,None,modify_fime))
					self.show_tips('load module %s success'%ext_module, 0)
				else:
					self.show_tips('external py module:%s aready loaded'%ext_module, 0)
		except Exception as e:
			self.show_tips('load external py module:%s err:%s'%(ext_module,e), 0)
			load_result = False
			pass
		return load_result
		
	def _do_load_external_module(self,ext_module):
		'''load external .dll or .so module in cdel type.
		or load external .py or .pyc module
		support 'init' function with no argument on load.
		'''
		if ext_module.endswith('.py') or ext_module.endswith('.pyc'):
			return self._do_load_external_py_module(ext_module)
		if not os.path.exists(ext_module):
			self.show_tips('external module:%s not found'%ext_module, 0)
			return False
		load_result = True
		try:
			from ctypes import cdll,create_string_buffer,byref
			if self.__filter_external_module_buffer_in is None:
				self.__filter_external_module_buffer_in = create_string_buffer('\0'*2048)
			if self.__filter_external_module_buffer_out is None:
				self.__filter_external_module_buffer_out = create_string_buffer('\0'*2048)
			if ext_module not in self.__filter_external_module:
				module_handle = cdll.LoadLibrary(ext_module)
				in_buffer = self.__filter_external_module_buffer_in
				out_buffer = self.__filter_external_module_buffer_out
				if module_handle and in_buffer and out_buffer:
					self.__filter_external_module.setdefault(ext_module,(module_handle,in_buffer,out_buffer,byref(in_buffer),byref(out_buffer)))
					if hasattr(module_handle,'init'):
						init_func = getattr(module_handle,'init')
						init_func()
					self.show_tips('load module %s success'%ext_module, 0)
				else:
					self.show_tips('load external module(%s) error null'%ext_module, 0)
					load_result = False
		except Exception as e:
			load_result = False
			self.show_tips('load external module exception:%s'%e, 0)
			pass
		return load_result
	def _setup_safe_func_scope(self):
		buildin_funcs = ('abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr',
						'complex', 'delattr', 'dict', 'divmod', 'enumerate', 'filter', 'float', 'format',
						'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'int',
						'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
						'min', 'next', 'oct', 'ord', 'pow', 'print', 'range', 'repr', 'round', 'set',
						'setattr', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'vars', 'zip')
		for func in buildin_funcs:
			try:
				pfunc = eval(func)
				self.__safe_scope.setdefault(func,pfunc)
			except Exception as e:
				pass
		for func in dir(math):
			if not func.startswith('_') and func not in self.__safe_scope:
				self.__safe_scope.setdefault(func, getattr(math,func))
				
	def getPorts(self,port_desc=None):
		__dev_dict = self.__dev_dict[self.__serial_common_name]
		ports_list = []
		for comnum,desc in __dev_dict.items():
			if desc['preset'] is not True:
				continue
			detail_name = desc['description'].get()
			if port_desc:
				if port_desc in detail_name:
					ports_list.append((comnum,detail_name))
			else:
				ports_list.append((comnum,detail_name))
				
		ports_list.sort()
		return list(("%s%d"%(self.__serial_common_name,n),d) for n,d in ports_list)
	def getOpenPorts(self,port_desc=None):
		open_devs = self.__dev_open_buttons
		ports_list = []
		for dev_name,dev_info in open_devs.items():
			if port_desc:
				if port_desc in dev_name:
					ports_list.append((dev_name,dev_info[2]['status']))
			else:
				ports_list.append((dev_name,dev_info[2]['status']))
		return ports_list
	def openPort(self,port_name,event=None):
		ret = False
		if self.__port_callback:
			ret = self.__port_callback(port_name,'open',event)
		return None if ret is True else ret
	def closeOnePort(self,port_name,event=None):
		ret = False
		if self.NOTIFY_TAB == port_name:
			ret = True
		elif self.__port_callback:
			ret = self.__port_callback(port_name,'close',event)
		return None if ret is True else ret
	def closeOneTab(self,tab_name,event=None):
		self.closePort(tab_name)
		self.del_open_dev(tab_name,event)
		return None
	def closePort(self,port_name=None):
		ret = False
		if port_name == 'all':
			open_devs = self.__dev_open_buttons.copy()
			for dev_name,dev_info in open_devs.items():
				ret = self.closeOnePort(dev_name)
		else:
			if port_name is None:
				port_name = self.get_select_tab()
			ret = self.closeOnePort(port_name)
		
		return None if ret is True else ret
	def closeTab(self,tab_name):
		if tab_name == 'all':
			open_devs = self.__dev_open_buttons.copy()
			for dev_name,dev_info in open_devs.items():
				self.closeOneTab(dev_name)
		else:
			if tab_name is None:
				tab_name = self.get_select_tab()
			self.closeOneTab(tab_name)
	def selectPort(self,port_name):
		for dev_name,dev_info in self.__dev_open_buttons.items():
			if dev_name == port_name:
				tab_add = dev_info[0]
				self.__notebook.select(tab_add)
				break
	def open_or_close_port(self,port_name,event):
		ret = None
		if event.widget['relief'] != Tkinter.SUNKEN:
			ret = self.openPort(port_name,event)
		else:
			ret = self.closeOnePort(port_name,event)
		return 'break' if ret is None else None
	def sendData(self,data,dev_name=None):
		cmd_ctx = {'text':data, 'senddev':dev_name, 'tail':self.__send_text_tail_var.get()}
		self.__send_cmd_callback(cmd_ctx)
	def sendFile(self,_file_name,dev_name=None):
		if not os.path.exists(_file_name):
			return 'file(%s) not exists'%_file_name
		if dev_name is None:
			dev_name = self.get_select_tab()
		if dev_name is None:
			return 'send port not exists'
		
		if _file_name not in self.__send_file_name:
			if len(self.__send_file_name) > 8:
				del self.__send_file_name[0]
			self.__send_file_name.append(_file_name)
		self.do_gui_callback(None,'send_file',port_name=dev_name, file_name=_file_name)
	def sendFilePathZmodem(self,_file_path,dev_name=None):
		if not os.path.exists(_file_path):
			return 'path(%s) not exists'%_file_path
		if dev_name is None:
			dev_name = self.get_select_tab()
		if dev_name is None:
			return 'send port not exists'
		if _file_path not in self.__send_zmodem_file_path:
			if len(self.__send_zmodem_file_path) > 8:
				del self.__send_zmodem_file_path[0]
			self.__send_zmodem_file_path.append(_file_path)
		print("do_gui_callback(None,'send_zmodem_path",_file_path)
		self.do_gui_callback(None,'send_zmodem_path',port_name=dev_name, file_path=_file_path)
	def _do_setup_external_execute_env(self):
		self._setup_safe_func_scope()
		if 'getCmd' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('getcmd',self.cmd_text)
		if 'loadModule' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('loadmodule',self._do_load_external_module)
		if 'doModule' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('domodule',self._do_external_function)
		
		#spec_funcs = ('getPorts', 'getOpenPorts', 'openPort', 'closePort', 'selectPort', 'sendData', 'sendFile' )
		if 'getPorts' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('getPorts',self.getPorts)
		if 'getOpenPorts' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('getOpenPorts',self.getOpenPorts)
		if 'openPort' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('openPort',self.openPort)
		if 'closePort' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('closePort',self.closePort)
		if 'closeTab' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('closeTab',self.closeTab)
		if 'selectPort' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('selectPort',self.selectPort)
		if 'sendData' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('sendData',self.sendData)
		if 'sendFile' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('sendFile',self.sendFile)
		if 'sendZmodem' not in self.__send_interval_scope:
			self.__send_interval_scope.setdefault('sendZmodem',self.sendFilePathZmodem)
			
		self.__total_auto_complete_cmd_list.extend(self.__send_interval_scope.keys())
	def _do_external_function(self,_module,_func,args):
		'''excute external functions in  .dll or .so module of cdll type
		and externel export function with argument (<input_buffer-2k>,<output_buffer-2k>)
		'''
		if _module not in self.__filter_external_module:
			self.show_tips('external module(%s) not found'%_module, 0)
			return None
		ret_val = None
		try:
			module_handle,in_buffer,out_buffer,byref_inbuffer,byref_outbuffer,m_time = self.__filter_external_module[_module]
			if module_handle and in_buffer and out_buffer and hasattr(module_handle,_func):
				pfunc = getattr(module_handle,_func)
				in_buffer.value = args
				pfunc(byref_inbuffer,byref_outbuffer)
				ret_val = out_buffer.value
			elif module_handle:
				pfunc = getattr(module_handle,_func)
				ret_val = pfunc(args)
			else:
				self.show_tips('do not found func(%s) in module(%s)'%(_func,_module), 0)
		except Exception as e:
			self.show_tips('do external funtion error:%s'%e, 0)
			pass
		
		return ret_val
	def _do_filter_send_to_event(self,_sendDev,send_content):
		cmd_ctx = {'senddev':_sendDev, 'text':send_content, 'tail':self.__send_text_tail_var.get()}
		self.__do_send_command(None,cmd_ctx)
		
	def do_filter_process_send_event(self,event,i,_match_Rx=None):
		send_content = None
		if self.__filter_actions_sel[i] == self.FILTER_ACTION_DOPROCESS:
			self.__filter_interval_scope["R%d"%i] = _match_Rx
			try:
				send_processer = self.__filter_actions_param[i]
				module_sep_index = 0
				if isinstance(send_processer,bytes):
					module_sep_index =  send_processer.find(b'::')
				else:
					module_sep_index =  send_processer.find('::')
				if module_sep_index > 0:
					ext_module = send_processer[0:module_sep_index]
					ext_func = send_processer[module_sep_index+2:]
					send_content = self._do_external_function(ext_module,ext_func,_match_Rx)
				else:
					compile_rule = compile(send_processer, '', 'eval')
					send_content = eval(compile_rule, self.__safe_scope, self.__filter_interval_scope)
			except Exception as e:
				self.show_tips('eval send err:%s, var scope:%s'%(e,self.__filter_interval_scope), 0)
				self.__text_filter_valid_bits[i] &= 0xf0
				pass
		if send_content:
			self._do_filter_send_to_event(None,send_content)
	def do_filter_send_to_event(self,event,i,_match_Rx=None):
		#first try stop auto send
		if self.__auto_send_enable is True:
			self.auto_send_start_end(None)
		
		param_content = self.__filter_actions_param[i]
		
		#no valid content,show tips and return error
		if not param_content.strip():
			self.__text_filter_valid_bits[i] &= 0xf0
			self.show_tips( "set sendTo 'devName[,sendcmdVal]',ex:COM1,R%d"%i, 0)
			return
		
		self.__filter_interval_scope["R%d"%i] = _match_Rx if _match_Rx else ''
		
		sep_idx = param_content.find(',')
		_sendDev = None
		#no , found but _match_Rx exists, default to send _match_Rx instead
		if sep_idx < 0 and _match_Rx != None:
			_sendDev = param_content
			send_content = _match_Rx
		elif sep_idx > 0 and len(param_content) > sep_idx+1: #send dev,send_string both found
			_sendDev = param_content[0:sep_idx]
			send_content = param_content[sep_idx+1:]
			if '$R' in send_content or '${R' in send_content:
				send_content = string.Template(send_content).safe_substitute(self.__filter_interval_scope)
		else:
			self.__text_filter_valid_bits[i] &= 0xf0
			self.show_tips( "set sendTo 'devName[,sendcmdVal]',ex:COM1,R%d"%i, 0)
			return
		
		if _sendDev in self.__dev_open_buttons:
			self._do_filter_send_to_event(_sendDev,send_content)
		else:
			self.show_tips( "%s err, set sendTo 'devName[,sendcmdVal]',ex:COM2,R%d"%(_sendDev,i), 0)
	def do_filter_send_event(self,event,i,_match_Rx=None,_sendDev=None):
		if self.__auto_send_enable is True:
			self.auto_send_start_end(None) #first try stop auto send
		
		self.__filter_interval_scope["R%d"%i] = _match_Rx if _match_Rx else ''
		
		send_content = self.__filter_actions_param[i]
		if '$R' in send_content or '${R' in send_content:
			send_content = string.Template(send_content).safe_substitute(self.__filter_interval_scope)
		self._do_filter_send_to_event(_sendDev,send_content)
		
	def do_filter_auto_send_event(self,event,i):
		def set_invalid_flag(i):
			self.__text_filter_valid_bits[i] &= 0xf0
			return
		if self.__auto_send_enable is True:
			self.auto_send_start_end(None) #first try stop auto send
		param_list = self.__filter_actions_param[i].split(',')
		if len(param_list) < 3:
			set_invalid_flag(i)
			self.show_tips( "set auto send 'LoopTime IntervalTime cmdList',ex:0,1000,1,2,3,4,6", 0)
			return
		for param in param_list:
			if not param.isdigit():
				set_invalid_flag(i)
				return
		param_list_int = [int(i_str) for i_str in param_list]
		param_over_list = [ i for i in param_list_int[2:] if i > self.__min_cmd_per_group+1 or i < 1]
		
		if param_over_list:
			set_invalid_flag(i)
			print ('filter_auto_send cmd index error:%s'%param_over_list)
			return
		self.__auto_send_loop_var.set(param_list[0])
		self.__auto_send_time_interval_var.set(param_list[1])
		#select send command list checkbox
		self.set_selection(param_list_int[2:])
		self.auto_send_start_end(None)
	
	def __do_filter_action(self,dev_name,match_result,cur_action,filter_index):
		i = filter_index
		if cur_action == self.FILTER_ACTION_SEND: #send
			#print ('filter send',match_result)
			self.do_filter_send_event(None,i,match_result)
			self.__filter_tasks_num[i] += 1
		elif cur_action == self.FILTER_ACTION_AUTO_SEND: #auto send
			#print ('filter auto send')
			self.do_filter_auto_send_event(None,i)
			self.__filter_tasks_num[i] += 1
		elif cur_action == self.FILTER_ACTION_DROP: #Drop
			print ('drop')
			self.__filter_tasks_num[i] += 1
		elif cur_action == self.FILTER_ACTION_ALARM: #Alarm
			print ('alarm')
		elif cur_action == self.FILTER_ACTION_SENDTO: #SendTo
			#print ('sendTo')
			self.do_filter_send_to_event(None,i,match_result)
			self.__filter_tasks_num[i] += 1
		elif cur_action == self.FILTER_ACTION_DOPROCESS:
			self.do_filter_process_send_event(None,i,match_result)
		else:
			self.__text_filter_valid_bits[i] &= 0xf0
		
	def __do_match_filter(self,dev_name,cur_line_str,filter_pattern,filter_action):
		match_result = []
		cur_line_filter_hit = False
		cur_line_drop = False
		for i in range(0,self.__filter_real_count):
			filterd = False
			cur_pattern = filter_pattern[i]
			exc_filter = self.__text_filter_str[i]
			
			if cur_pattern > 0 and self.__text_filter_valid_bits[i] >= 0x11:
				if cur_pattern == self.FILTER_MATCH_STARTS_WITH:#1.StartsWith
					if cur_line_str.startswith(exc_filter) is True:
						filterd = True
						match_result = cur_line_str
				elif cur_pattern == self.FILTER_MATCH_ENDS_WITH:#3.EndsWith
					linestr_pure = cur_line_str.rstrip()
					exc_filter_pure = exc_filter.rstrip()
					if linestr_pure.endswith(exc_filter_pure) is True:
						filterd = True
						match_result = cur_line_str
				elif cur_pattern == self.FILTER_MATCH_INCLUDE: #Middle, any position
					if cur_line_str.find(exc_filter) >= 0:
						filterd = True
						match_result = cur_line_str
				elif cur_pattern == self.FILTER_MATCH_REGEXP: #RegExp
					if hasattr(exc_filter,'findall') and hasattr(exc_filter,'match'):
						if exc_filter.match(cur_line_str) is not None:
							filterd = True
							match_result = exc_filter.findall(cur_line_str)
					else:
						print ('error not compiled reg',exc_filter)
						self.__text_filter_valid_bits[i] &= 0x0f
				
				#do filter action
				if filterd is True:
					cur_action = filter_action[i]
					if cur_line_filter_hit is False:
						cur_line_filter_hit = True
					if cur_action == self.FILTER_ACTION_DROP: #drop
						cur_line_drop = True
					self.__do_filter_action(dev_name,match_result,cur_action,i)
				
		return cur_line_filter_hit,cur_line_drop
	def __filter_words_process(self,dev_name,total_add_lines_str):
		add_lines_str = total_add_lines_str
		
		if self.__filter_frame_pack is True and 0x11 in self.__text_filter_valid_bits:
			drop_line_idx = []
			filter_pattern = self.__filter_pattern_sel
			filter_action = self.__filter_actions_sel
			
			cur_dev = self.get_select_tab()
			if cur_dev == dev_name:
				lines_str = total_add_lines_str.splitlines(True)
				is_filterd = False
				is_filterd_trop = False
				_line_count = len(lines_str)
				for i in range(_line_count):
					cur_line_str = lines_str[i]
					if os.linesep != cur_line_str:
						filterd,filterd_trop = self.__do_match_filter(dev_name,cur_line_str,filter_pattern,filter_action)
						is_filterd = True if filterd is True else is_filterd
						if filterd_trop:
							drop_line_idx.insert(0,i) #bigger idx must insert to the beginning
					
				if is_filterd is True:
					#set filterd timestamp
					self.__filter_hit_timestamp = time.time()
					self.__filter_idle_task_count = 0
					
					if drop_line_idx:
						for _drop in drop_line_idx:
							if _drop+1 < _line_count and os.linesep == lines_str[_drop+1]:
								del lines_str[_drop+1]
								_line_count -= 1
							del lines_str[_drop]
							_line_count -=1
						add_lines_str = "".join(lines_str)
			
			#ComeFrom/SendTo Filter/Action, sepcial process
			if self.FILTER_MATCH_COME_FROM in filter_pattern:
				for i in range(0,self.__filter_real_count):
					if filter_pattern[i] == self.FILTER_MATCH_COME_FROM:
						if dev_name == self.__text_filter_str[i]:
							if filter_action[i] == self.FILTER_ACTION_SENDTO:
								self.do_filter_send_to_event(None,i,total_add_lines_str)
								self.__filter_tasks_num[i] += 1
							elif filter_action[i] == self.FILTER_ACTION_DOPROCESS:
								self.do_filter_process_send_event(None,i,total_add_lines_str)
								self.__filter_tasks_num[i] += 1
		return add_lines_str
		
	def __ctrl_words_process(self,sci_string,sci_offset):
		#ctrl_color_words = '\[[0-9]+[;0-9]*m'
		#\33[nA cursor up n lines
		#\33[nB cursor down n lines 
		#\33[nC cursor right n lines 
		#\33[nD cursor left n lines 
		#\33[y;xH set cursor position 
		#\33[2J clear screen
		#\33[K clear cursor to line end 
		#\33[s save cursor positon
		#\33[u pop cursor position
		#\33[?25l hide cursor
		#\33[?25h show cursor
		strip_sck_string_list = []
		strip_sck_string_list.append(sci_string[0:sci_offset])
		#strip_sck_string = sci_string[0:sci_offset]
		skip_char_count = 1  #skip \x1B (33)
		ending_char_set = ['m','n','A','B','C','D','H','J','K','s','u','l','h']
		new_sci_offset = sci_offset
		while new_sci_offset >= 0:
			#strip_sck_string += sci_string[sci_offset:new_sci_offset]
			strip_sck_string_list.append(sci_string[sci_offset:new_sci_offset])
			sci_offset = new_sci_offset
			skip_char_count = 1
			try:
				for i in range(sci_offset+1,sci_offset+20):
					if sci_string[i] == '[' or sci_string[i] == ';' or sci_string[i] == '?' or sci_string[i].isdigit():
						skip_char_count += 1
					else:
						break
				#print 'e',skip_char_count,sci_string[sci_offset+skip_char_count]
				if sci_string[sci_offset+skip_char_count] in ending_char_set:
					skip_char_count += 1
					#print 'o',skip_char_count,sci_offset
			finally:
				sci_offset += skip_char_count
				new_sci_offset = sci_string.find('\x1B', sci_offset)
		else:
			#strip_sck_string += sci_string[sci_offset:]
			strip_sck_string_list.append(sci_string[sci_offset:])
		
		return "".join(strip_sck_string_list)
			
	def __do_send_command(self,event,cmd_ctx=None,cmd_index=None):
		if self.__send_cmd_callback is not None:
			if cmd_index is not None:
				cmd_ctx = self.get_cmd_context('CMD',cmd_index)
			elif cmd_ctx is None:
				text_str = event.widget['text']
				cmd_ctx = self.get_cmd_context('CMD',text_str)
			
			if cmd_ctx is not None and 'calctext' in cmd_ctx and 'template' in cmd_ctx:
				if self.__send_interval_template_dict:
					cmd_ctx['calctext'] = self._get_template_value(cmd_ctx['template'])
				else:
					cmd_ctx['calctext'] = None
				self.__send_cmd_callback(cmd_ctx)
				cmd_ctx['calctext'] = None
			else:
				self.__send_cmd_callback(cmd_ctx)
			
	def __process_text_schedule(self,next_time_out):
		if next_time_out < 1 or self.__notebook is None:
			return None
		if self.__quit_now is True:
			print ('quiting,nto add schedule task')
			return None
		
		after_task_id = None
		try:
			after_task_id = self._after_schecule('T',next_time_out, self.__process_add_text_notebook)
			if after_task_id is not None and self.__submit_processing_flag is False:
				self.__submit_processing_flag = True
		except Exception as e:
			print ('__process_text_schedule err',e)
			pass
		
		return after_task_id
	
	def _do_schecule_process(self,event_cause,process_func,timestamp,*args):
		if self.__tid != current_thread().ident:
			print ('error do schedule from other thread, return')
			return None
		if event_cause not in self.__schedule_manager:
			return None
		
		if self.__schedule_manager[event_cause]['count'] >= 1:
			self.__schedule_manager[event_cause]['count'] -= 1
		if timestamp in self.__schedule_manager[event_cause]['tasks']:
			del self.__schedule_manager[event_cause]['tasks'][timestamp]
		
		if event_cause is not 'T' and event_cause is not 'S' and event_cause is not 'Q' and event_cause is not 'A':
			print ('_do_schecule_process',event_cause)
		try:
			process_func(*args)
		except Exception as e:
			traceback.print_exc()
			print ('process %s Exception:%s'%(event_cause,e))
			pass
		
	def __do_after_schecule(self,schecule_widget,event_cause,timeafter,process_func,*args):
		if self.__tid != current_thread().ident:
			print ('error after schedule from other thread, return', event_cause, process_func)
			return None
		
		#note: the same event_cause statics
		if event_cause in self.__schedule_manager and self.__schedule_manager[event_cause]['count'] >= 1:
			#print ("drop schedule event: %d,%s"%(timeafter,event_cause))
			return None
		
		task_id = None
		retry_times = 0
		timestamp = time.time()
		
		while retry_times < 3 and task_id is None:
			try:
				if timeafter > 0:
					task_id = schecule_widget.after(timeafter,self._do_schecule_process,event_cause,process_func,timestamp,*args)
				else:
					task_id = schecule_widget.after_idle(self._do_schecule_process,event_cause,process_func,timestamp,*args)
			except Exception as e:
				retry_times += 1
				print ('_after_schecule:%s exception:%s'%(event_cause,e))
				pass
		
		if task_id is not None:
			if event_cause not in self.__schedule_manager:
				self.__schedule_manager[event_cause] = {'count':1,'tasks':{timestamp:task_id}}
			else:
				self.__schedule_manager[event_cause]['count'] += 1
				self.__schedule_manager[event_cause]['tasks'][timestamp] = task_id
		
		return task_id
	def _after_schecule(self,event_cause,timeafter,process_func,*args):
		if self.__quit_now is True:
			return None
		
		if event_cause is 'T' or event_cause is 'S':
			task_id = self.__do_after_schecule(self.__notebook,event_cause,timeafter,process_func,*args)
		elif event_cause is 'A':
			task_id = self.__do_after_schecule(self.__auto_send_ctrl,event_cause,timeafter,process_func,*args)
		else:
			task_id = self.__do_after_schecule(self.__root,event_cause,timeafter,process_func,*args)
		
		if self.__expert_mode is False:
			return task_id
		elif self.__debug_mode is True:
			print ('_after_schecule %d,%s'%(timeafter,event_cause))
		elif event_cause is 'T' or event_cause is 'S' or event_cause is 'Q' or event_cause is 'A':
			return task_id
		else:
			print ('_after_sche %d,%s'%(timeafter,event_cause))
		return task_id
		
	def _cancel_schecule(self,event_cause):
		if self.__tid != current_thread().ident:
			print ('error do cancel schedule from other thread, return')
			return None
		cencel_success = False
		if event_cause in self.__schedule_manager:
			for timestamp,task_id in self.__schedule_manager[event_cause]['tasks'].items():
				try:
					if event_cause is 'T' or event_cause is 'S':
						self.__notebook.after_cancel(task_id)
					elif event_cause is 'A':
						self.__auto_send_ctrl.after_cancel(task_id)
					else:
						self.__root.after_cancel(task_id)
					cencel_success = True
				except Exception as e:
					print ('_cancel_schecule %s Exception %s'%(event_cause,e))
					pass
			self.__schedule_manager[event_cause] = {'count':0,'tasks':{}}
		
		return cencel_success
	def _cancel_all_schecule(self):
		if self.__tid != current_thread().ident:
			print ('error do cancel all schedule from other thread, return')
			return None
		for event_cause in self.__schedule_manager:
			for timestamp,task_id in self.__schedule_manager[event_cause]['tasks'].items():
				try:
					if event_cause is 'T' or event_cause is 'S':
						self.__notebook.after_cancel(task_id)
					elif event_cause is 'A':
						self.__auto_send_ctrl.after_cancel(task_id)
					else:
						self.__root.after_cancel(task_id)
				except Exception as e:
					print ('_cancel_schecule %s Exception %s'%(event_cause,e))
					pass
			self.__schedule_manager[event_cause] = {'count':0,'tasks':{}}
		
	def __check_skip_too_many_msg(self,dev_name,_msg_queue):
		msg_count = len(_msg_queue)
		if msg_count < 6:
			return msg_count, 0
		displayChars = self.__dev_statics_info[dev_name]['displayChars']
		displayLines = self.__dev_statics_info[dev_name]['displayLines']
		last_msg_idx = 1
		skip_msg_count = 0
		skip_msg_count_lines = 0
		
		avarage_msg_len = (_msg_queue[0][2] + _msg_queue[-1][2] + _msg_queue[msg_count//2][2]) / 3
		
		min_buffer_size_threhold = self.__max_buffer_size - self.__max_buffer_size_pingpong
		
		if displayChars + msg_count*avarage_msg_len >= min_buffer_size_threhold:
			top_msg_chars = 0
			for idx in range(1,msg_count):
				top_msg_chars += _msg_queue[-idx][2]
				if top_msg_chars >= min_buffer_size_threhold:
					skip_msg_count = msg_count - idx
					break

		for i in range(skip_msg_count):
			_msg_queue.popleft()
		
		msg_count_left = msg_count - skip_msg_count
		if displayLines + msg_count_left >= self.__min_buffer_lines_threshold:
			top_msg_lines = 0
			for idx in range(1,msg_count_left):
				top_msg = _msg_queue[-idx]
				top_msg_lines += top_msg.count('\n') or top_msg.count('\r')
				if top_msg_lines >= self.__min_buffer_lines_threshold:
					skip_msg_count_lines = msg_count_left - idx
					break
		
		for i in range(skip_msg_count_lines):
			_msg_queue.popleft()
		
		return msg_count, skip_msg_count + skip_msg_count_lines
	def __get_msg_from_queue(self,dev_name,_msg_queue):
		total_add_lines_array = []
		total_local_flag_array = []
		msg_array = []
		msg_count = total_joined_msg_count = 0
		msg_len = 0
		last_local_msg_flag = cur_local_msg_flag = None
		last_port_name = cur_port_name = None
		auto_swrap = self.__auto_line_wrap_show
		
		while True:
			try:
				__msg = _msg_queue.popleft()
				cur_local_msg_flag = __msg[0]
				if dev_name is self.NOTIFY_TAB:
					cur_port_name = __msg[3]
					if msg_array and last_local_msg_flag is not None and last_port_name and (cur_port_name != last_port_name or cur_local_msg_flag != last_local_msg_flag):
						if auto_swrap and not msg_array[-1][-1] in os.linesep:
							msg_array.append(os.linesep)
						total_add_lines_array.append( (last_port_name,"".join(msg_array),last_local_msg_flag) )
						total_joined_msg_count += 1
						msg_array = []
					last_port_name = cur_port_name
				elif msg_array and last_local_msg_flag is not None and cur_local_msg_flag != last_local_msg_flag:
					if auto_swrap and not msg_array[-1][-1] in os.linesep:
						msg_array.append(os.linesep)
					total_add_lines_array.append( ("".join(msg_array),last_local_msg_flag) )
					total_joined_msg_count += 1
					msg_array = []
					
				msg_array.append(__msg[1])
				msg_len += __msg[2]
				last_local_msg_flag = cur_local_msg_flag
				msg_count += 1
				
				#do not process too much message one time
				if msg_count >= 100 or msg_len >= 4096:
					break
			except Exception as e:
				break
			
		if msg_array:
			if auto_swrap and not msg_array[-1][-1] in os.linesep:
				msg_array.append(os.linesep)
			if dev_name is self.NOTIFY_TAB:
				total_add_lines_array.append( (last_port_name,"".join(msg_array),last_local_msg_flag) )
			else:
				total_add_lines_array.append( ("".join(msg_array),last_local_msg_flag) )
			total_joined_msg_count += 1
		if msg_count > 0:
			if dev_name in self.__dev_statics_info:
				self.__dev_statics_info[dev_name]['recv'] += msg_len
				self.__dev_statics_info[dev_name]['recvTimes'] += msg_count
				self.__dev_statics_info[dev_name]['displayChars'] += msg_len
				self.__dev_statics_info[dev_name]['displayLines'] += 1
			return total_joined_msg_count,total_add_lines_array
		return 0,None
		
	def __text_filter_ctrl_word_preparse(self,dev_name,total_add_lines_str,need_display_ctrl=True):
		if need_display_ctrl is False or dev_name != self.get_select_tab():
			return total_add_lines_str

		if isinstance(total_add_lines_str,bytes) and not isinstance(b'',str):
			return total_add_lines_str
		if need_display_ctrl is False:
			return total_add_lines_str
		add_lines_str = total_add_lines_str
		sci = add_lines_str.find('\x1B')
		if sci >= 0:
			add_lines_str = self.__ctrl_words_process(add_lines_str,sci)
		return add_lines_str
	
	def __control_text_max_line_and_auto_scroll(self,text_window,dev_name):
		if dev_name in self.__dev_statics_info:
			displayChars = self.__dev_statics_info[dev_name]['displayChars']
			displayLines = self.__dev_statics_info[dev_name]['displayLines']
			recv_times = self.__dev_statics_info[dev_name]['recvTimes']
			
			if displayLines > self.__max_buffer_lines or displayChars > self.__max_buffer_size or (recv_times % 256)  == 128:
				total_lines,total_chars = text_window.count('1.0',  Tkinter.END, 'lines','chars')
				#total_lines = int(text_window.index('end-1c').split('.')[0])
				del_lines = 0
				del_chars = 0
				if  total_lines >= self.__max_buffer_lines_threshold:
					del_lines = total_lines - self.__min_buffer_lines_threshold
					text_window.delete('1.0', '%d.0'%del_lines)
				elif total_chars > self.__max_buffer_size:
					del_chars = total_chars - self.__max_buffer_size
					if del_chars < self.__max_buffer_size_pingpong:
						del_chars = self.__max_buffer_size_pingpong
					del_lines = 2
					line_chars = 0
					last_line_chars = 0
					while del_lines <= total_lines+1:
						line_chars +=  text_window.count('%d.0'%(del_lines - 1),'%d.0'%del_lines,'chars')[0]
						if line_chars >= del_chars:
							break
						last_line_chars = line_chars
						del_lines += 1
					
					del_last_line_chars = del_chars - last_line_chars
					if del_last_line_chars > 256:
						text_window.delete('1.0', '%d.%d'%(del_lines - 1, del_last_line_chars))
					else:
						text_window.delete('1.0', '%d.%d'%(del_lines - 1, 0))
				
				#adjust use real value
				self.__dev_statics_info[dev_name]['displayLines'] = total_lines - del_lines
				self.__dev_statics_info[dev_name]['displayChars'] = total_chars - del_chars
		
		if self.__text_scroll_disable is False:
			#text_window.see(Tkinter.END)
			#text_window.after(200,text_window.see,Tkinter.END)
			if self.__sync_msg_rate > 10:
				self._after_schecule('S',160,text_window.see,Tkinter.END)
			else:
				text_window.see(Tkinter.END)
			#text_window.yview(Tkinter.MOVETO, 1.0)#
		
	def __do_recv_text_decoding(self,add_line_str,rcv_encoding=None):
		add_line_str_d = add_line_str
		if type(add_line_str) != type(u'') and isinstance(add_line_str,bytes):
			try:
				if rcv_encoding is None:
					rcv_encoding = self.get_display_encoding()
				add_line_str_d = add_line_str.decode(rcv_encoding)
			except Exception as e:
				try:
					add_line_str_d = add_line_str.decode('utf-8')
				except Exception as e:
					add_line_str_d = add_line_str.decode(rcv_encoding, errors='replace')
					pass
				pass
		return add_line_str_d
		
	def check_is_display_text_queue_empty(self):
		for msg_queue in self.__dev_text_queues.values():
			if msg_queue:
				return False
		if self.__text_file_queue:
				return False
		return True
	def __process_add_text_notebook(self):
		if self.__notebook is None:
			return
		self.__submit_processing_flag = False
		
		for dev_name,msg_queue in self.__dev_text_queues.items():
			total_msg_count,can_skip_msg_count = self.__check_skip_too_many_msg(dev_name,msg_queue)
			if can_skip_msg_count:
				print ('skip %d of %d'%(can_skip_msg_count,total_msg_count))
				#text_window.delete('1.0',Tkinter.END)
			msg_count,my_msg_list = self.__get_msg_from_queue(dev_name,msg_queue)
			if my_msg_list is None:
				continue
			
			if dev_name not in self.__dev_open_buttons:
				print('display dev:%s drop\n'%dev_name)
				continue
			
			text_window = self.__dev_open_buttons[dev_name][1]
			for my_msg_text,is_local_msg in my_msg_list:
				#do text display
				try:
					if is_local_msg:
						text_window.insert(Tkinter.END, my_msg_text,com_ports_gui.TEXT_TAG_LOCAL_ECHO)
					else:
						my_msg_text = self.__text_filter_ctrl_word_preparse(dev_name,my_msg_text,True)
						text_window.insert(Tkinter.END, my_msg_text)
				except Exception as e:
					print ('insert %s text error %s\n'%(dev_name,e))
					pass
			# auto buffer linecount and scroll control
			self.__control_text_max_line_and_auto_scroll(text_window,dev_name)
			
		msg_count,my_msg_list = self.__get_msg_from_queue(self.NOTIFY_TAB,self.__text_file_queue)
		if my_msg_list is not None and self.NOTIFY_TAB in self.__dev_open_buttons:
			display_text = text_window = None
			need_show_notify_tab = False
			for port_name,my_msg_text,is_local_msg in my_msg_list:
				#print (i_msg[1],type(i_msg[1]))
				tab_name = self.NOTIFY_TAB
				if port_name.startswith('tcp') or port_name.startswith('udp'):
					if port_name not in self.__dev_open_buttons:
						self.add_open_dev(port_name)
					tab_name = port_name
					display_text = '%s%s'%(os.linesep,my_msg_text)
				else:
					display_text = '%s%s: %s'%(os.linesep,port_name,my_msg_text)
					need_show_notify_tab = True
				text_window = self.__dev_open_buttons[tab_name][1]
				#only do filter match do not change display
				self.__text_filter_ctrl_word_preparse(tab_name,display_text,False)
				if is_local_msg:
					text_window.insert(Tkinter.END, display_text, com_ports_gui.TEXT_TAG_LOCAL_ECHO)
				else:
					text_window.insert(Tkinter.END, display_text)
			self.__control_text_max_line_and_auto_scroll(text_window,self.NOTIFY_TAB)
			if self.__notify_tab_show is False and need_show_notify_tab is True:
				self.__notify_tab_show = True
				self.__notebook.tab(self.__dev_open_buttons[self.NOTIFY_TAB][0], state='normal')
				if len(self.__notebook.tabs()) == 1:
					self.__notebook.select(self.__dev_open_buttons[self.NOTIFY_TAB][0])
		
		if self.__submit_processing_flag is False and not self.check_is_display_text_queue_empty():
			self.__process_text_schedule(200)
	def triger_show_text(self):
		try:
			if self.__submit_processing_flag is True:
				pass
			elif self.__sync_msg_rate >= 20:
				cur_state = self.get_current_state()
				if cur_state.endswith('focus'):
					self.__process_text_schedule(85)
				elif cur_state == 'withdrawn':
					self.__process_text_schedule(203)
				else:
					self.__process_text_schedule(115)
			elif self.__sync_msg_rate > 10 or self.__sync_msg_count >= 30:
				self.__process_text_schedule(57)
			else:
				self.__process_add_text_notebook()
		except Exception as e:
			print ('submit next schedule error %s'%e)
			#traceback.print_exc()
			pass
		
	def submit_add_text(self,port_name,ser_handle,bytes_or_string_add):
		is_Q_full = False
		try:
			local_add = 0
			if isinstance(bytes_or_string_add,tuple):
				if self.__display_hex and isinstance(bytes_or_string_add[0],bytes):
					string_add = bytes_or_string_add[0].hex()
				else:
					string_add = self.__do_recv_text_decoding(bytes_or_string_add[0])
				cur_timestamp = bytes_or_string_add[1]
				local_add = bytes_or_string_add[2]
				if not local_add:
					string_add = self.__filter_words_process(port_name,string_add)
				if cur_timestamp:
					string_add = '%s %s'%(cur_timestamp,string_add)
			else:
				if self.__display_hex and isinstance(bytes_or_string_add,bytes):
					string_add = bytes_or_string_add.hex()
				else:
					add_string = self.__do_recv_text_decoding(bytes_or_string_add)
				string_add = self.__filter_words_process(port_name,add_string)
				
			string_len = len(string_add)
			if port_name in self.__dev_text_queues:
				self.__dev_text_queues[port_name].append((local_add,string_add,string_len))
			else:
				self.__text_file_queue.append( (local_add,string_add,string_len,port_name) )
		except Exception as e:
			print ('submit text err:%s'%e)
			is_Q_full = True
			pass
		
		if is_Q_full:
			self.triger_show_text()
	def submit_control_text(self,port_name,string_add):
		self.submit_add_text(port_name,None,(string_add,None,1))
		self.triger_show_text()
	def get_select_cmd_group_index(self):
		if self.__cmd_group_list is not None:
			#cur_index =  self.__cmd_group_list.curselection()
			cur_index =  self.__cmd_group_list.current()
			#if len(cur_index) > 0:
			#	return getint(cur_index[0])
			if cur_index >= 0:
				return cur_index
		return None
	def __try_the_encoding(self,str_in,encoding):
		bytes_out = None
		try:
			bytes_out = str_in.encode(encoding)
		except Exception as e:
			pass
		return bytes_out
	def __try_the_decoding(self,bytes_in,encoding):
		str_out = None
		try:
			str_out = bytes_in.decode(encoding)
		except Exception as e:
			pass
		return str_out
	def _try_decoding(self,bytes_in,encoding=None):
		encoding_list = []
		if encoding is not None:
			encoding_list.append(encoding)
		encoding_list.append(self.get_display_encoding())
		encoding_list.append(self.get_send_encoding())
		encoding_list.append('utf-8')
		encoding_list.append('gb2312')
		encoding_list.append('gbk')
		
		decode_out = None
		for enc in encoding_list:
			var_out = self.__try_the_decoding(bytes_in,enc)
			if var_out is not None:
				decode_out = var_out
				break
		if decode_out is None:
			decode_out = str(bytes_in)
		
		return decode_out
	
	def get_all_dev(self):
		return False
		if OS_name == 'nt':
			import devport
			import winip as osip
		else:
			import comdev_linux as devport
			osip = None
		self.__dev_list_last = self.__dev_list.copy()
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
			
		if osip is not None:
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
					self.__dev_list[self.__net_common_name] += self.__dev_list[self.__adb_common_name]
			except Exception as e:
				print ('except in osip.get_adapters_info!! %s'%e)
				self.show_tips('except in osip.get_adapters_info!!',3000)
				pass
		
		#return true is there is any change
		return self.__dev_list_last != self.__dev_list
		
	def get_dev_names(self, dev_class):
		if dev_class.upper() == self.__net_common_name:
			return self.__dev_list[self.__net_common_name]
		else:
			return self.__dev_list[self.__serial_common_name]
		
	def get_cmd_list(self, key_word, group_index):
		group_num = len(self.__cmd_list)
		if group_num > 0 and group_index < group_num:
			cmd_list = self.__cmd_list[group_index]
		else:
			cmd_list = []
		
		group_timeout = 10
		group_tail ='\r\n'
		
		if type(cmd_list) == type({}):
			if '@timeout' in cmd_list:
				group_timeout = int(cmd_list['@timeout'])
			if '@tail' in cmd_list:
				group_tail = cmd_list['@tail']
			if 'string' in cmd_list:
				cmd_list = cmd_list['string']
				if type(cmd_list) == type({}): #only one command string
					cmd_list = [cmd_list]
					self.__cmd_list[group_index]['string'] = cmd_list  #update the original structure
				elif isinstance(cmd_list,(str,bytes)):
					cmd_list = [cmd_list]
					self.__cmd_list[group_index]['string'] = cmd_list  #update the original structure
				
		return (group_timeout,group_tail,cmd_list)
	def build_cmd_dict(self,min_num,group_index,key_word):
		self.__cmd_change_disable = True
		
		if not key_word in self.__cmd_dict:
			self.__cmd_dict.setdefault(key_word, {})
		
		__cmd_dict = self.__cmd_dict[key_word]
		
		self.__cmd_timeout, tail, cmd_list = self.get_cmd_list(key_word,group_index)
		dev_num = len(cmd_list)
		self.__defaut_tail_str = tail
		self.__default_auto_complete_cmd_list = []
		
		if dev_num > self.__max_cmd_per_group:
			dev_num = self.__max_cmd_per_group
		
		for i in range(0,dev_num):
			#print (i,cmd_list[i])
			text_str = ''
			tips_text = ''
			timeout = self.__cmd_timeout
			
			if isinstance(cmd_list[i],str):
				text_str = cmd_list[i]
			elif type(cmd_list[i]) == type({}):
				if 'string' in cmd_list[i]:
					text_str = cmd_list[i]['string']
				if '@desc' in cmd_list[i]:
					tips_text = cmd_list[i]['@desc']
				if '@tail' in cmd_list[i]:
					tail = cmd_list[i]['@tail']
				if '@timeout' in cmd_list[i]:
					timeout = int(cmd_list[i]['@timeout'])
			
			comnum = i+1
			if comnum in __cmd_dict:
				__cmd_dict[comnum]['group_index'] = group_index  #pleas keep this first
				__cmd_dict[comnum]['text'].set(text_str)
				__cmd_dict[comnum]['template'] = self.__build_string_template(text_str)
				__cmd_dict[comnum]['description'].set(tips_text)
				__cmd_dict[comnum]['tail'] = tail
				__cmd_dict[comnum]['timeout'] = timeout
				__cmd_dict[comnum]['select'].set(True)
				__cmd_dict[comnum]['preset'] = True
				if len(text_str) > 0 and text_str not in self.__default_auto_complete_cmd_list:
					self.__default_auto_complete_cmd_list.append(text_str)
					
		for i in range(dev_num,self.__min_cmd_per_group+1):
			comnum = i+1
			if comnum in __cmd_dict:
				__cmd_dict[comnum]['group_index'] = group_index  #pleas keep this first
				__cmd_dict[comnum]['text'].set('')
				__cmd_dict[comnum]['template'] = None
				__cmd_dict[comnum]['description'].set('')
				__cmd_dict[comnum]['tail'] = tail
				__cmd_dict[comnum]['timeout'] = self.__cmd_timeout
				__cmd_dict[comnum]['select'].set(False)
				__cmd_dict[comnum]['preset'] = False
		
		self.__cmd_change_disable = False
		
	def get_cmd_context(self,key_word,dict_key):
		if key_word in self.__cmd_dict:
			__cmd_dict = self.__cmd_dict[key_word]
			if type(dict_key) == type('') and dict_key.isdigit():
				dict_key = int(dict_key)
				
			if dict_key in __cmd_dict:
				return __cmd_dict[dict_key]
			else:
				print ('get_cmd_ctx error',type(dict_key), dict_key)
		return None
	
	def gettimeout(self,key_word,dict_key):
		return self.__cmd_timeout
		
	def cmd_change_complte_check(self,change_ver):
		if change_ver == self.__cmd_change_ver:
			#ok, no more change
			self.do_gui_callback(None,'auto_save',ver=change_ver)
		else:
			#there is another change, check later, after_schedule only allow one, so just add it
			self._after_schecule('change-complte-check',600,self.cmd_change_complte_check,self.__cmd_change_ver)
	def get_cmd_changed(self):
		if self.__cmd_auto_save_ver != self.__cmd_change_ver:
			return (True,self.__cmd_change_ver)
		return (False,self.__cmd_change_ver)
	def set_cmd_changed(self,changed):
		if changed is True:
			self.__cmd_change_ver += 1
			self.__cmd_change_ver %= 36000
		if self.__cmd_auto_save_ver != self.__cmd_change_ver: #after_schedule only allow one, so just add it
			self._after_schecule('change-complte-check',600,self.cmd_change_complte_check,self.__cmd_change_ver)
	def set_cmd_auto_save_ver(self,ver):
		self.__cmd_auto_save_ver = ver
		print ('change:%d,save:%d'%(self.__cmd_change_ver,self.__cmd_auto_save_ver))
	def show_cmd_tips(self,key_word,event):
		#print (key_word,type(key_word),event)
		#key_word = event.widget['text']
		ctx = self.get_cmd_context('CMD', key_word)
		if ctx is not None:
			if 'description' in ctx:
				self.show_tips(str(key_word)+'. '+ctx['description'].get(), 0)
	
	def cmd_text(self,group_index,cmd_index,new_text=None,new_description=None):
		'''get command list. param: <group_index>,<cmd_index>
		set command list,param: <group_index>,<cmd_index>,<new_text>,<new_description>
		'''
		old_text = ''
		old_description = ''
		change = 0
		#if not isinstance(new_text, bytes):
		#	new_text = new_text.encode('utf-8')
		#if not isinstance(new_text, bytes):
		#	new_description = new_description.encode('utf-8')
		if group_index < len(self.__cmd_list) and cmd_index > 0:
			cmd_list = self.__cmd_list[group_index]
			i = cmd_index-1
			if type(cmd_list) == type({}):
				if 'string' in cmd_list:
					cmd_list_length = len(cmd_list['string'])
					if i < cmd_list_length:
						if isinstance(cmd_list['string'][i],str) or type(cmd_list['string'][i]) == type(u''):
							old_text = cmd_list['string'][i]
							change = 1000
							if new_text is not None and new_text != old_text:
								self.__cmd_list[group_index]['string'][i] = {'string':new_text, '@desc':new_description}
								change += 1
							elif new_description is not None:
								self.__cmd_list[group_index]['string'][i] = {'string':old_text, '@desc':new_description}
								change += 10
						elif type(cmd_list['string'][i]) == type({}):
							change = 2000
							if 'string' in cmd_list['string'][i]:
								old_text = cmd_list['string'][i]['string']
							if '@desc' in cmd_list['string'][i]:
								old_description = cmd_list['string'][i]['@desc']
							
							if new_text is not None and new_text != old_text:
								self.__cmd_list[group_index]['string'][i]['string'] = new_text
								change += 1
							if new_description is not None and old_description != new_description:
								self.__cmd_list[group_index]['string'][i]['@desc'] = new_description
								change += 10
						else:
							change = -1000
					elif i < self.__max_cmd_per_group:	#total allow self.__max_cmd_per_group commands per group
						old_text = ''
						change = 6000
						if new_text is not None and len(new_text) > 0:
							for j in range(cmd_list_length,i):
								self.__cmd_list[group_index]['string'].append({'string':'', '@desc':''})
							self.__cmd_list[group_index]['string'].append({'string':new_text, '@desc':new_description})
							change += 11
					else:
						change = -2000
						print ('else',i,cmd_list_length,self.__max_cmd_per_group,len(new_text) )
				else:
					change = -1001
					print ("cmd_list not has key'string' ")
			elif type(cmd_list) == type([]):
				cmd_list_length = len(cmd_list)
				if i < cmd_list_length:
					if isinstance(cmd_list[i],str) or type(cmd_list['string'][i]) == type(u''):
						old_text = cmd_list[i]
						change = 100
						if new_text is not None and old_text != new_text:
							self.__cmd_list[group_index][i] = {'string':new_text, '@desc':new_description}
							change += 1
						elif new_description is not None:
							self.__cmd_list[group_index][i] = {'string':old_text, '@desc':new_description}
							change += 10
					elif type(cmd_list[i]) == type({}):
						change = 200
						if 'string' in cmd_list[i]:
							old_text = cmd_list[i]['string']
						if '@desc' in cmd_list[i]:
							old_description = cmd_list[i]['@desc']
						if new_text is not None and new_text != old_text:
							self.__cmd_list[group_index][i]['string'] = new_text
							change += 1
						if new_description is not None and new_description != old_description:
							self.__cmd_list[group_index][i]['@desc'] = new_description
							change += 10
					else:
						change = -200
						print ('err type',type(cmd_list[i]) )
				elif i < self.__max_cmd_per_group:	#total allow self.__max_cmd_per_group commands per group
						old_text = ''
						change = 6000
						if new_text is not None and len(new_text) > 0:
							for j in range(cmd_list_length,i):
								self.__cmd_list[group_index]['string'].append({'string':'', '@desc':''})
							self.__cmd_list[group_index]['string'].append({'string':new_text, '@desc':new_description})
							change += 11
						else:
							change = -1
				else:
					change = -2
			else:
				change = -3
				print ('err',type(cmd_list))
		else:
			change = -10
		#print ('group_index:%d,cmd_index:%d,change:%d\n'%(group_index,cmd_index,change))
		return old_text,old_description
	def __init_total_cmd_list(self,key_word):
		auto_complete_list = self.__total_auto_complete_cmd_list
		group_num = len(self.__cmd_list)
		for group_index in range(0,group_num):
			cmd_timeout, tail, cmd_list = self.get_cmd_list(key_word,group_index)
			
			for each_cmd in cmd_list:
				text_str = ''
				if type(each_cmd) == type(''):
					text_str = each_cmd
				elif type(each_cmd) == type({}):
					if 'string' in each_cmd:
						text_str = each_cmd['string']
					#if '@desc' in each_cmd:
					#	tips_text = each_cmd['@desc']
					#if '@timeout' in each_cmd:
					#	timeout = int(each_cmd['@timeout'])
				if text_str != '' and text_str not in auto_complete_list:
					auto_complete_list.append(text_str)
			
	def __var_spec_char_check(self,str_in):
		ch_set   = set(str_in)
		com_set  =  ch_set & self.__spec_char_set
		change = False
		for ch in com_set:
			str_in = str_in.replace(ch,self.__spec_char_set_repr[ch])
			change = True
		return str_in,change
	def _val_sendbox_trace_callback(self,v):
		if self.__cmd_change_disable is True or self.__frame_pack is False or self.__gui_shown is False or self.__quit_now is True:
			return
		if self.__in_trace is True:
			return
		new_text        = v.get()
		new_text_repr, change = self.__var_spec_char_check(new_text)
		if change is True:
			self.__in_trace = True
			v.set(new_text_repr)
			self.__in_trace = False
	def __val_text_trace_callback(self,i,v):
		if self.__cmd_change_disable is True or self.__frame_pack is False or self.__gui_shown is False or self.__quit_now is True:
			return
		if self.__in_trace is True or 'CMD' not in self.__cmd_dict or i not in self.__cmd_dict['CMD']:
			return
		
		cur_group_index = self.__cmd_dict['CMD'][i]['group_index']
		cur_cmd_index   = i
		new_text        = v.get()
		#print (new_text,type(new_text))
		old_text,old_d = self.cmd_text(cur_group_index, cur_cmd_index, new_text)
		new_text_repr, change = self.__var_spec_char_check(new_text)
		if change is True:
			self.__in_trace = True
			v.set(new_text_repr)
			self.__in_trace = False
		self.__cmd_dict['CMD'][i]['template'] = self.__build_string_template(new_text_repr)
		self.__cmd_dict['CMD'][i]['ver'] += 1
		self.set_cmd_changed(True)
		
	def __val_description_trace_callback(self,i,v):
		if self.__cmd_change_disable is True or self.__frame_pack is False or self.__gui_shown is False or self.__quit_now is True:
			return
		if 'CMD' not in self.__cmd_dict or i not in self.__cmd_dict['CMD']:
			return
		cur_group_index = self.__cmd_dict['CMD'][i]['group_index']
		cur_cmd_index   = i
		new_desc        = v.get().strip()
		old_text,old_desc = self.cmd_text(cur_group_index, cur_cmd_index, None, new_desc)
		if old_desc != new_desc:
			self.set_cmd_changed(True)
		
	def __init_cmd_dict_var(self,key_word):
		if not key_word in self.__cmd_dict:
			self.__cmd_dict.setdefault(key_word, {})
		
		__cmd_dict = self.__cmd_dict[key_word]
		
		for i in range(1,self.__min_cmd_per_group+1):
			val = {}
			val['group_index'] = 0
			val['ver'] = 0
			val['text'] = Tkinter.StringVar(self.__root)
			val['template'] = None
			val['calctext'] = None
			val['description'] = Tkinter.StringVar(self.__root)
			val['select'] = Tkinter.BooleanVar(self.__root)
			val['timeout'] = 10
			val['tail'] = False
			val['frame'] = None
			val['entry'] = None
			val['button'] = None
			val['preset'] = False
			val['show'] = False
			val['text'].trace_variable('w',lambda a,b,c,idx=i,v=val['text']: self.__val_text_trace_callback(idx,v))
			val['description'].trace_variable('w',lambda a,b,c,idx=i,v=val['description']: self.__val_description_trace_callback(idx,v))
			__cmd_dict.setdefault(i, val)
			
	def _check_active_tlv_editer(self,key_word,event=None):
		if self.__auto_send_enable is True:
			self.show_tips('could not edit command when auto send',0)
			return
		ctx = self.get_cmd_context('CMD', key_word)
		if ctx is None:
			return
		def _change_state(new_state):
			self.change_readonly_state(self.__auto_send_ctrl, new_state)
			self.change_readonly_state(self.__cmd_group_list, new_state)
		def _editer_win_close_callback(w):
			self.__toplevel_win_count -= 1
			if self.__toplevel_win_count == 0:
				_change_state('normal')
			
		self.__toplevel_win_count += 1
		_change_state('disabled')
		self.do_gui_callback(event,'start_TLV',root=self.__root,data_val=ctx['text'],description_val=ctx['description'],
								title=' %s cmd %d'%(self.__win_title,key_word), close_callback=_editer_win_close_callback)
		
	def show_cmd_dict(self,top_frame,key_word):
		'''show the command list UI'''
		def cmd_focus_up(event,key_word,type_key):
			try:
				ctx = self.get_cmd_context('CMD', key_word-1)
				if ctx is not None:
					ctx[type_key].focus()
				else:
					self.__cmd_group_list.focus()
			except:
				print ('error up')
				self.__cmd_group_list.focus()
				pass
		def cmd_focus_down(event,key_word,type_key):
			try:
				ctx = self.get_cmd_context('CMD', key_word+1)
				if ctx is not None:
					ctx[type_key].focus()
				else:
					self.__send_frame_entry.focus()
			except:
				print ('error down')
				self.__send_frame_entry.focus()
				pass
		def cmd_scroll(event):
			self.__right_bottom_frame.Scroll(event)
		x = 6
		y = 0
		__cmd_dict = self.__cmd_dict[key_word]
		frm = top_frame
		
		for key in range(1,self.__min_cmd_per_group+1):
			#print key,__cmd_dict
			_grid_row = key + 3
			l = ttk.Entry(frm, textvariable=__cmd_dict[key]['text'],style="cmd.TEntry")
			l.bind('<Return>', lambda event,k=key:self.__do_send_command(event,None,k))
			l.bind('<Up>', lambda event,k=key: cmd_focus_up(event,k,'entry'))
			l.bind('<Down>', lambda event,k=key: cmd_focus_down(event,k,'entry'))
			l.bind('<FocusIn>', lambda event,idx=key:self.show_cmd_tips(idx,event))
			l.bind('<MouseWheel>', cmd_scroll)
			l.grid(row=_grid_row, column=0, columnspan=5, padx=2, pady=0, sticky=E+W+S+N)#
			
			b = ttk.Button(frm, text=str(key),width=5,style="cmd.TButton")
			b.grid(row=_grid_row, column=5, padx=2, pady=0)
			
			b.bind("<Button-1>",self.__do_send_command)
			b.bind("<Return>",self.__do_send_command)
			b.bind("<Button-3>",lambda event,idx=key:self.show_cmd_tips(idx,event))
			b.bind('<Double-Button-3>', lambda event,k=key:self._check_active_tlv_editer(k,event))
			b.bind('<Left>', lambda event,the_label=l: the_label.focus())
			b.bind('<Up>', lambda event,k=key: cmd_focus_up(event,k,'button'))
			b.bind('<Down>', lambda event,k=key: cmd_focus_down(event,k,'button'))
			
			ckb = ttk.Checkbutton(frm, text='', variable=__cmd_dict[key]['select'],style="cmd.TCheckbutton")
			ckb.grid(row=_grid_row, column=6, padx=2, pady=0)
			
			__cmd_dict[key]['frame'] = frm
			__cmd_dict[key]['entry'] = l
			__cmd_dict[key]['button'] = b
			__cmd_dict[key]['show'] = True
		
	def get_dev_dictkey(self,key_word,text_name,i=0):
		text_str = text_name.upper()
		comindex = text_str.find('(' + key_word)+1
		if comindex < 0:
			comindex = text_str.find(key_word)
		comnum = None
		if comindex >= 0:
			comstr = text_str[comindex:].replace(key_word,'')
			try:
				if key_word == self.__serial_common_name:
					comnum_len = len(comstr)+1
					int_count = [idx for idx in range(0,comnum_len) if comstr[0:idx].isdigit()]
					if int_count:
						comnum = int(comstr[0:int_count[-1]])
					else:
						comnum = int(comstr.strip('(').strip(')'))
				elif key_word == self.__net_key_word:
					#genarate key index from MAC
					comstr = comstr.strip('(').strip(')')
					mac_index = comstr.find('MAC:')
					if mac_index >= 0:
						mac_index += len('MAC:')
						mac_data = [_.strip() for _ in comstr[mac_index:].split('-')]
						mac_data = ''.join([_[0:2] for _ in mac_data if len(_)>=2 ])
						if mac_data in self.__mac_index_table:
							comnum = self.__mac_index_table[mac_data]
						else:
							comnum = len(self.__mac_index_table)+1
							self.__mac_index_table.setdefault(mac_data,comnum)
					elif comstr.startswith('ADB:') is True:
						comnum = 30 + i
					else:
						comnum = 40 + i
			except Exception as e:
				print ('get_dev_dictkey err:%s'%e)
				pass
		return comnum
	
	def build_dev_dict(self,dev_list,key_word):
		if not key_word in self.__dev_dict:
			self.__dev_dict.setdefault(key_word, {})
		
		__dev_dict = self.__dev_dict[key_word]
		for key,val in __dev_dict.items():
			val['preset'] = False
		
		i = 0
		dev_num = len(dev_list)
		#if key_word== self.__net_key_word:
		#	print dev_list
		for i in range(0,dev_num):
			#print i,len(__dev_dict)
			comnum = self.get_dev_dictkey(key_word,dev_list[i],i)
			#print (key_word,comnum)
			if comnum is not None:
				com_name = key_word+str(comnum)
				
				if comnum in __dev_dict:
					__dev_dict[comnum]['description'].set(dev_list[i])
					__dev_dict[comnum]['com'].set(com_name)
					__dev_dict[comnum]['preset'] = True
				else:
					description = Tkinter.StringVar(self.__root)
					value = Tkinter.StringVar(self.__root)
					description.set(dev_list[i])
					value.set(com_name)
					__dev_dict.setdefault(comnum, {'description':description, 'com':value, 'preset':True})
	
	def change_readonly_state(self,widget_to_change,state_new=None):
		if state_new is not None and type(state_new) == type(''):
			widget_to_change.config(state=state_new)
		elif widget_to_change['state'] == 'readonly':
			widget_to_change.config(state='normal')
		else:
			widget_to_change.config(state='readonly')
		widget_to_change.pack_propagate(1)
		
	def get_net_info(self,net_str):
		net_ip = None
		gw_ip = None
		ip_offset = net_str.find('#IP:')
		gw_offset = net_str.find('GW:')
		if ip_offset >=0 and gw_offset >=0:
			ip_info = net_str[ip_offset+4:gw_offset].strip()  #+3 to skip #IP:
			gw_info = net_str[gw_offset+3:].strip()		#+3 to skip GW:
			net_ip = ip_info.split()
			gw_ip = gw_info.split()
			
		return net_ip,gw_ip
	
	def __auto_com_entry_set_autocomplete(self,auto_wiget):
		auto_list = []
		custom_com =  self.__custom_com_var.get()
		if custom_com:
			auto_list.append(custom_com)
		com_dev_array = self.get_dev_names(self.__serial_common_name)
		for com_dev in com_dev_array:
			comnum = self.get_dev_dictkey(self.__serial_common_name,com_dev,1)
			if "PC UI" in com_dev or "PCUI" in com_dev:
				auto_list.append('%s%s'%(self.__serial_common_name,str(comnum)))
				break
		if not auto_list:
			auto_list.append('%s%d'%(self.__serial_common_name,1))
		net_dev_array = self.get_dev_names(self.__net_common_name)
		for net_dev in net_dev_array:
			ip,gw = self.get_net_info(net_dev)
			if ip is not None and gw is not None and not ip[0].startswith('0') and not gw[0].startswith('0'):
				auto_list.append("tcp://%s:0@%s:%d"%(ip[0],gw[0],3000))
				auto_list.append("tcp://%s:0@%s:%d"%(ip[0],gw[0],20249))
				auto_list.append("udp://%s:0@%s:%d"%(ip[0],gw[0],3000))
				auto_list.append("telnet://%s:0@%s:%d"%(ip[0],gw[0],23))
				auto_list.append("telnet://%s:0@%s:%d"%(ip[0],gw[0],8023))
		auto_wiget.set_completion_list(auto_list)
		auto_wiget['values'] = auto_list
	def set_mouse_on_flag(self,mouse_on_flag,flag_val):
		if mouse_on_flag in self.__dev_mouse_on:
			self.__dev_mouse_on[mouse_on_flag] = flag_val
		
	def get_serial_setting(self):
		return {'baudrate':self.__serial_bitrate_var.get(),
				'databit':self.__serial_databit_var.get(),
				'stopbit':self.__serial_stopbit_var.get(),
				'checkbit':self.__serial_checkbit_var.get(),
				'flowctrl':self.__serial_flowctrl_var.get(),
				'log':None,
				'localecho':self.__local_echo_var.get(),
				'showtime':self.__show_timestamp_var.get()}
		
	def show_serial_setting(self,top_frame):
		setting_frm = top_frame#ttk.LabelFrame(top_frame, text="serial setting", borderwidth=1)
		bitrate_label=ttk.Label(setting_frm,text='BaudRate')
		bitrate_label.grid(row=1,column=1)
		self.__bitrate_combo_list = ['256000','128000','115200','57600','56000','38400','19200','14400','9600','4800','2400','1800','1200','600','300','200','150','110','75','50']
		cmbEditCombo = ttk.Combobox(setting_frm, textvariable=self.__serial_bitrate_var,width=8,values=self.__bitrate_combo_list,postcommand=self.__commbo_display)
		cmbEditCombo.current(2)
		cmbEditCombo.grid(row=1,column=2,padx=2)
		
		self.__databit_combo_list = ['5','6','7','8']
		self.__stopbit_combo_list = ['1','1.5','2']
		self.__checkbit_combo_list = ['None','Odd','Even','Mark','Space']
		show_more_serial_setting = True
		if self.__expert_mode is True:
			show_more_serial_setting = True
		if show_more_serial_setting is True:
			databit_label=ttk.Label(setting_frm,text='DataBit ')
			databit_label.grid(row=2,column=1)
			cmbEditCombo = ttk.Combobox(setting_frm, textvariable=self.__serial_databit_var,width=8,values=self.__databit_combo_list,postcommand=self.__commbo_display)
			cmbEditCombo.current(3)
			cmbEditCombo.grid(row=2,column=2,padx=2)
			
			stopbit_label=ttk.Label(setting_frm,text='StopBit ')
			stopbit_label.grid(row=3,column=1)
			cmbEditCombo = ttk.Combobox(setting_frm, textvariable=self.__serial_stopbit_var,width=8,values=self.__stopbit_combo_list,postcommand=self.__commbo_display)
			cmbEditCombo.current(0)
			cmbEditCombo.grid(row=3,column=2,padx=2)
			
			checkbit_label=ttk.Label(setting_frm,text='Parity  ')
			checkbit_label.grid(row=4,column=1)
			cmbEditCombo = ttk.Combobox(setting_frm, textvariable=self.__serial_checkbit_var,width=8,values=self.__checkbit_combo_list,postcommand=self.__commbo_display)
			cmbEditCombo.current(0)
			cmbEditCombo.grid(row=4,column=2,padx=2)
		else:
			self.__serial_databit_var.set(self.__databit_combo_list[3])
			self.__serial_stopbit_var.set(self.__stopbit_combo_list[0])
			self.__serial_checkbit_var.set(self.__checkbit_combo_list[0])
		#flowctrl_label=ttk.Label(setting_frm,text='FlowCtrl')
		#flowctrl_label.grid(row=5,column=1)
		#self.__flowctrl_combo_list = ['None','Hardware','Software']
		#cmbEditCombo = ttk.Combobox(setting_frm, textvariable=self.__serial_flowctrl_var,width=8,values=self.__flowctrl_combo_list,postcommand=self.__commbo_display)
		#cmbEditCombo.current(0)
		#cmbEditCombo.grid(row=5,column=2,padx=2)
		#setting_frm.pack(side=TOP,padx=2,pady=0)
		setting_frm.grid(row=0,rowspan=3,column=0,padx=2,pady=0)
		
	def change_font_size(self,event=None,f_size=None):
		if f_size is not None:
			font_size = int(f_size)
		else:
			font_size = 10
		
		if font_size != self.__font_size:
			self.__style_set.configure('cmd.TEntry', font=('Helvetica', font_size-1, 'normal'))
			self.__style_set.configure('cmd.TButton', font=('Helvetica', font_size-1, 'normal'))
			self.__style_set.configure('send.TButton', font=('Helvetica', font_size, 'normal'))
			self.__style_set.configure('send.TCheckbutton', font=('Helvetica', font_size-1, 'normal'))
			self.__send_frame_entry.config(font=('Helvetica', font_size*2, 'normal'))
			for key_word in range(1,self.__min_cmd_per_group+1):
				ctx = self.get_cmd_context('CMD', key_word)
				if ctx is not None and 'entry' in ctx and ctx['entry'] is not None:
					ctx['entry'].config(font=('Helvetica', font_size, 'normal'))
			self.__font_size = font_size
	def set_always_on_top(self,event=None):
		if self.__always_top_var.get() > 0:
			self.__root.wm_attributes('-topmost',1)
		else:
			self.__root.wm_attributes('-topmost',0)
	def set_window_alpha(self,event=None):
		if self.__alpha_scale_ctrl is not None:
			self.__root.attributes("-alpha",self.__alpha_scale_ctrl.get())
	def show_license(self,event=None):
		try:
			print (self.__base_dir,self.get_base_dir())
			os.startfile(os.path.join(self.__base_dir,'license.txt'))
		except Exception as e:
			print("open license file err%s"%e)
			pass
	def show_server_setting_box(self,top_frame):
		frm = top_frame#ttk.LabelFrame(top_frame, text="common setting", borderwidth=1)
		
		try:
			tcp_port = int(self.__config['tcp_srv_port']) + self.__instance_num
		except:
			tcp_port = 3000
			pass
		try:
			udp_port = int(self.__config['udp_srv_port']) + self.__instance_num
		except:
			udp_port = 3000
			pass
		try:
			multicast_ip = self.__config['multicast_ip']
			multicast_port = int(self.__config['multicast_port'])
		except:
			multicast_ip = '224.0.0.119'
			multicast_port = 30000
			pass
		if is_module_exists('ICOM_netsrv'):
			ckb = ttk.Checkbutton(frm, text="TCP Server", variable=self.__auto_start_tcp_server_var)
			lab = ttk.Label(frm, text=": %d"%tcp_port)
			ckb.grid(row=1,column=1, padx=2, pady=0, sticky=E+W)
			lab.grid(row=1,column=2, padx=2, pady=0, sticky=E+W)
			ckb.bind("<Button-1>",lambda e:self.do_gui_callback(e,'start_tcp_srv',type='tcp',port=tcp_port,var=self.__auto_start_tcp_server_var))
			ckb = ttk.Checkbutton(frm, text="UDP Server", variable=self.__auto_start_udp_server_var)
			lab = ttk.Label(frm, text=": %d"%udp_port)
			ckb.grid(row=2,column=1, padx=2, pady=0, sticky=E+W)
			lab.grid(row=2,column=2, padx=2, pady=0, sticky=E+W)
			ckb.bind("<Button-1>",lambda e:self.do_gui_callback(e,'start_udp_srv',type='udp',port=udp_port,var=self.__auto_start_udp_server_var))
			#if self.__expert_mode is True:
			ckb = ttk.Checkbutton(frm, text="MultiCast", variable=self.__auto_start_multicast_server_var)
			lab = ttk.Label(frm, text=": %d"%multicast_port)
			ckb.grid(row=3,column=1, padx=2, pady=0, sticky=E+W)
			lab.grid(row=3,column=2, padx=2, pady=0, sticky=E+W)
			ckb.bind("<Button-1>",lambda e:self.do_gui_callback(e,'start_multicast_srv',type='udp_cast',port=multicast_port,multicast=multicast_ip,var=self.__auto_start_multicast_server_var))
	def __set_send_encoding(self,event=None):
		try:
			new_codec = self.__send_encoding_var.get()
			print (event, new_codec)
			'send_encoding.test'.encode(new_codec)
			self.__config['send_encoding'] = new_codec
		except Exception as e:
			self.show_tips('set send codec(%s) error'%e,0)
			self.__send_encoding_var.set(self.__config['send_encoding'])
			pass
		self.__commbo_display()
	def __set_recv_decoding(self,event=None):
		try:
			new_codec = self.__recv_decoding_var.get()
			b'recv_decoding.test'.decode(new_codec)
			self.__config['display_encoding'] = new_codec
		except Exception as e:
			self.show_tips('set recv codec(%s) error'%e,0)
			self.__recv_decoding_var.set(self.__config['display_encoding'])
			pass
		self.__commbo_display()
	def show_codec_setting_box(self,top_frame):
		frm = top_frame#ttk.LabelFrame(top_frame, text="common setting", borderwidth=1)
		send_encoding = self.__config['send_encoding']
		recv_decoding = self.__config['display_encoding']
		send_codec_label = ttk.Label(frm,text='SendEncode ')
		row_idx = 0
		send_codec_label.grid(row=row_idx,column=0)
		if send_encoding not in self.__send_encoding_combo_list:
			self.__send_encoding_combo_list.append(send_encoding)
		cmbEditCombo = ttk.Combobox(frm, textvariable=self.__send_encoding_var, width=7,values=self.__send_encoding_combo_list,postcommand=self.__set_send_encoding)
		cmbEditCombo.current(self.__send_encoding_combo_list.index(send_encoding))
		cmbEditCombo.grid(row=row_idx,column=1,padx=2)
		cmbEditCombo.bind('<<ComboboxSelected>>',self.__set_send_encoding)
		
		row_idx += 1
		recv_codec_label = ttk.Label(frm,text='RecvDecode ')
		recv_codec_label.grid(row=row_idx,column=0)
		if recv_decoding not in self.__recv_decoding_combo_list:
			self.__recv_decoding_combo_list.append(recv_decoding)
		cmbEditCombo = ttk.Combobox(frm, textvariable=self.__recv_decoding_var, width=7,values=self.__recv_decoding_combo_list,postcommand=self.__set_recv_decoding)
		cmbEditCombo.current(self.__recv_decoding_combo_list.index(recv_decoding))
		cmbEditCombo.grid(row=row_idx,column=1,padx=2)
		cmbEditCombo.bind('<<ComboboxSelected>>',self.__set_recv_decoding)
		row_idx += 1
		self.__keep_ascii_single_byte.set(1)
		ckb = ttk.Checkbutton(frm, text="KeepAsciiCodec", variable=self.__keep_ascii_single_byte)
		ckb.grid(row=row_idx,column=0,columnspan=2,sticky=W)
		frm.grid(row=3,rowspan=2,column=0,padx=2, pady=4, sticky=E+W)
	def display_text_var_change(self,a=None,b=None,c=None):
		self.__display_hex = self.__display_hex_var.get()
	def auto_line_swrap_change(self,a=None,b=None,c=None):
		self.__auto_line_wrap_show = self.__auto_line_wrap_show_var.get()
	def show_common_setting_box(self,top_frame):
		#top_frame.columnconfigure(5, weight=1)
		frm = top_frame#ttk.LabelFrame(top_frame, text="common setting", borderwidth=1)
		row_idx = 0
		self.__auto_save_log_var.set(1)
		ckb = ttk.Checkbutton(frm, text="SaveLog", variable=self.__auto_save_log_var)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		lab = ttk.Label(frm, text="Open")
		lab.bind("<Button-1>",lambda e:self.do_gui_callback(e,'show_log_file_dir',port_name=self.get_select_tab(),open_type='file'))
		lab.bind("<Button-2>",lambda e:self.do_gui_callback(e,'show_log_file_dir',port_name=self.get_select_tab(),open_type='dir'))
		lab.grid(row=row_idx,column=2,padx=2, pady=0, sticky=E+W)
		
		row_idx += 1
		self.__local_echo_var.set(0)
		ckb = ttk.Checkbutton(frm, text="LocalEcho", variable=self.__local_echo_var)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		self.__local_echo_var.trace_variable('w',lambda a,b,c:self.do_gui_callback(None,'local_echo',port_name=self.get_select_tab(),localecho=True if self.__local_echo_var.get() else False))
		lab = ttk.Label(frm, text=" ")
		lab.grid(row=row_idx,column=2,padx=2, pady=0, sticky=E+W)
		
		row_idx += 1
		self.__auto_line_wrap_show_var.set(0)
		ckb = ttk.Checkbutton(frm, text="AutoWrap", variable=self.__auto_line_wrap_show_var)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		self.__auto_line_wrap_show_var.trace_variable('w',self.auto_line_swrap_change)
		lab = ttk.Label(frm, text=" ")
		lab.grid(row=row_idx,column=2,padx=2, pady=0, sticky=E+W)
		
		row_idx += 1
		self.__display_hex_var.set(0)
		ckb = ttk.Checkbutton(frm, text="ShowHex", variable=self.__display_hex_var)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		self.__display_hex_var.trace_variable('w',self.display_text_var_change)
		
		row_idx += 1
		self.__show_timestamp_var.set(0)
		ckb = ttk.Checkbutton(frm, text="ShowTime", variable=self.__show_timestamp_var)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		self.__show_timestamp_var.trace_variable('w',lambda a,b,c:self.do_gui_callback(None,'show_time',port_name=self.get_select_tab(),show=True if self.__show_timestamp_var.get() else False))
		lab = ttk.Label(frm, text=" ")
		lab.grid(row=row_idx,column=2,padx=2, pady=0, sticky=E+W)
		
		row_idx += 1
		self.__always_top_var.set(0)
		ckb = ttk.Checkbutton(frm, text="Always Top", variable=self.__always_top_var, command=self.set_always_on_top)
		ckb.grid(row=row_idx,column=1,padx=2, pady=0, sticky=E+W)
		
		scale_bar = ttk.Scale(frm,orient=Tkinter.HORIZONTAL, value=1.0, length=42, from_=0.3, to=1.0, command=self.set_window_alpha) #,from="0.2",to="1.0"
		scale_bar.grid(row=row_idx,column=2,padx=2, pady=0, sticky=E+W)
		self.__alpha_scale_ctrl = scale_bar
		
		frm.grid(row=3,rowspan=2,column=0,padx=2, pady=4, sticky=E+W)
	def show_tab_setting(self,top_frame):
		tab_setting_frame = ttk.LabelFrame(top_frame, text="setting", borderwidth=1)
		setting_notebook = ttk.Notebook(tab_setting_frame,width=160)
		tab_setting_serial = ttk.Frame(self.__root, borderwidth=0,height=100)
		tab_setting_server = ttk.Frame(self.__root, borderwidth=0,height=100)
		tab_setting_codec = ttk.Frame(self.__root, borderwidth=0,height=100)
		self.show_serial_setting(tab_setting_serial)
		self.show_server_setting_box(tab_setting_server)
		self.show_codec_setting_box(tab_setting_codec)
		setting_notebook.add(tab_setting_serial, text='Serial')
		setting_notebook.tab(tab_setting_serial, sticky='nsew')
		setting_notebook.add(tab_setting_server, text='Server')
		setting_notebook.tab(tab_setting_server, sticky='nsew')
		setting_notebook.add(tab_setting_codec, text='Codec')
		setting_notebook.tab(tab_setting_codec, sticky='nsew')
		setting_notebook.grid(row=0,rowspan=2,column=0,columnspan=5,padx=2, pady=0, sticky=E+W)
		tab_setting_frame.grid(row=0,column=0,columnspan=5,padx=2, pady=0, sticky=E+W)
	def show_common_setting(self,top_frame):
		comm_setting_frame = ttk.LabelFrame(top_frame, text="common setting", borderwidth=1)
		self.show_common_setting_box(comm_setting_frame)
		comm_setting_frame.grid(row=1,column=0,columnspan=5,padx=2, pady=0, sticky=E+W)
	def show_setting(self,setting_frame):
		setting_frame.rowconfigure(2, weight=1)
		setting_frame.columnconfigure(5, weight=1)
		self.show_tab_setting(setting_frame)
		self.show_common_setting(setting_frame)
	def show_dev_dict(self,key_word,callback,top_frame):
		__dev_dict = self.__dev_dict[key_word]
		
		#if key_word == self.__net_key_word:
		#	print (__dev_tuple)
		is_com_dev = True
		if key_word != self.__serial_common_name:
			is_com_dev = False
		
		dev_frame = top_frame
		#add custom com set Entry
		if is_com_dev is True and self.__custom_com_show is not True:
			if self.__entry_height is not None:
				frm = ttk.Frame(dev_frame, borderwidth=0,height=self.__entry_height)
			else:
				frm = ttk.Frame(dev_frame, borderwidth=0)
			if 'autocom' in self.__config:
				self.__custom_com_var.set(self.__config['autocom'])
			else:
				self.__custom_com_var.set(self.__serial_common_name)
			frm.columnconfigure(1, weight=1)
			l=AutocompleteCombobox(frm, textvariable=self.__custom_com_var, takefocus=0, width=33, postcommand=self.__commbo_display)#bd=0,highlightthickness=0,relief='flat', 
			l.bind_auto_key_event()
			l.grid(row=0,column=0,columnspan=2,padx=0, pady=0, sticky=E+W)
			b = Tkinter.Button(frm, textvariable=self.__custom_com_var, width=9, padx=0, pady=1, font=('Helvetica', 9, 'normal'))
			b.bind("<Button-1>",lambda event,param=self.__custom_com_var:callback(param.get(),event))
			b.bind("<Double-Button-1>",lambda event,param=self.__custom_com_var:callback(param.get(),event))
			b.bind("<Return>",lambda event,param=self.__custom_com_var:callback(param.get(),event))
			b.grid(row=0,column=2,padx=0, pady=0, sticky=E+W)
			l.bind("<<ReadOnlyToggle>>",lambda event,lab=l:self.change_readonly_state(lab))
			l.bind("<Return>",lambda event,bn=b:bn.focus())
			#l.bind("<KeyRelease>",lambda event:self.__auto_com_entry_callback(event))
			#if self.__entry_height is not None:
			#	frm.pack_propagate(0)
			frm.grid(row=0,column=0,columnspan=2,padx=0, pady=0, sticky=E+W)
			self.__auto_open_dev_entry = l
			self.__auto_open_dev_btn = b
			self.__custom_com_show = True
			
		if self.__auto_open_dev_entry is not None:
			self.__auto_com_entry_set_autocomplete(self.__auto_open_dev_entry)
		
		if not __dev_dict:
			return
		__dev_tuple = [tuple(item) for item in __dev_dict.items()]
		__dev_tuple.sort()
		self.__last_dev = None
		self.__first_dev = None
		
		for key,val in __dev_tuple:
			#print ('show_dev_dict k:%s,v:%s'%(key,val))
			if not isinstance(key,int):
				continue
			row_index = key
			if not 'show' in val:		#device insert 
				port_name = val['com'].get()
				print('insert %s'%port_name)
				if self.__entry_height is not None:
					frm = ttk.Frame(dev_frame, borderwidth=0, height=self.__entry_height)
				else:
					frm = ttk.Frame(dev_frame, borderwidth=0)
				frm.columnconfigure(1, weight=1)
				l=Tkinter.Entry(frm, relief='flat', highlightcolor='lightblue', state='readonly', bd=0, textvariable=val['description'], takefocus=0, highlightthickness=1, width=36)#'#E8E8FF'
				if is_com_dev is True:
					l.grid(row=0,column=0,columnspan=2,padx=0, pady=0, sticky=E+W)
				else:
					l.grid(row=0,column=0,columnspan=3,padx=0, pady=0, sticky=E+W)
				
				b = None
				if is_com_dev is True:
					b = Tkinter.Button(frm, textvariable=val['com'], width=9, padx=0, pady=1, font=('Helvetica', 9, 'normal'))
					b.bind("<Double-Button-1>",lambda event,param=port_name:callback(param,event))
					b.bind("<Button-1>",lambda event,param=port_name:callback(param,event))
					b.bind("<Button-3>",lambda event,param=port_name:callback(param,event))
					b.bind("<Return>",lambda event,param=port_name:callback(param,event))
					b.grid(row=0,column=2,padx=0, pady=0, sticky=E+W)
				
				frm.grid(row=row_index,column=0, columnspan=2, padx=0, pady=0, sticky=E+W)
				val['frame'] = frm
				val['show'] = True
				val['button'] = b
			elif val['preset'] is False and val['show'] is True:	#device removed
				port_name = val['com'].get()
				print('remove %s'%port_name)
				val['frame'].grid_remove()
				val['show'] = False
				if port_name in self.__dev_open_buttons:
					self.submit_control_text(port_name,"%s========%s DEVICE REMOVE========%s"%(os.linesep,time.strftime("%y-%m-%d %H:%M:%S"),os.linesep))
				self.do_gui_callback(None,'dev_remove',dev_name=port_name, is_com_dev=is_com_dev, button=val['button'])
			elif val['preset'] is True and val['show'] is False:		#device insert again
				port_name = val['com'].get()
				print('insert again %s'%port_name)
				val['frame'].grid(row=row_index,column=0, columnspan=2, padx=0, pady=0, sticky=E+W)
				val['show'] = True
			
			if val['show'] is True and val['button'] is not None:
				self.__last_dev = val
			if self.__first_dev is None and val['show'] is True and val['button'] is not None:
				self.__first_dev = val
				
		
	def show_tips(self,tips_string,auto_timeout_ms=None,add=None):
		if self.__top_tips_label is None and self.__tips_label is None:
			self.__tips__after_task_id = None
			return
		tips_var = self.__top_tips_var
		#print (tips_string,auto_timeout_ms)
		if self.__tips_label is not None and self.check_visible(self.__top_frame) is True:
			tips_var = self.__tips_var
		
		def tips_auto_clear():
			self.__tips__after_task_id = None
			self.__top_tips_var.set('')
			self.__tips_var.set('')
		
		if add is True:
			tips_string = tips_var.get() + tips_string
			
		tips_var.set(tips_string)
		if self.__tips__after_task_id is not None:
			self._cancel_schecule('show_tips_clean')
			self._cancel_schecule('show_tips')
			self.__tips__after_task_id = None
			
		if auto_timeout_ms and auto_timeout_ms > 0:
			self.__tips__after_task_id = self._after_schecule('show_tips_clean',auto_timeout_ms,tips_auto_clear)
		else:
			self.__tips__after_task_id = None
		
	def aboutCallBack(self,event):
		self.show_tips('ICOM Tools Version %d.%d. Please edit cmdlist.autosave.xml to config you own commands.'%(icom_version,icom_subversion), 3000)
	
	def aboutCallBackAuthor(self,event):
		self.show_tips('Any suggestion, please contact shujunwei@QQ.com', 3000)
		
	def change_cmd_group(self,event):
		try:
			group_index = self.get_select_cmd_group_index()
			self.build_cmd_dict(self.__min_cmd_per_group, group_index, 'CMD')
		except Exception as e:
			self.show_tips('Change command group failed:%s'%e, 3000)
			pass
		
	def __try_auto_open_dev(self):
		dev_name = self.check_need_auto_open_dev()
		if dev_name:
			devkey = self.get_dev_dictkey(self.__serial_common_name,dev_name,0)
			if devkey is not None and devkey in self.__dev_dict[self.__serial_common_name]:
				if self.__dev_dict[self.__serial_common_name][devkey]['preset'] is True:
					if dev_name in self.__dev_open_buttons:
						self.submit_control_text(dev_name,"%s========%s DEVICE OPEN RETRY========%s"%(os.linesep,time.strftime("%y-%m-%d %H:%M:%S"),os.linesep))
					self.__auto_open_dev_btn['relief'] = Tkinter.RAISED
					self.__auto_open_dev_btn.event_generate('<Button-1>', x=0, y=0)
				
	def refresh_gui(self):
		if self.__quit_now is True:
			return 0
		refresh = 2
		
		win_state_now = self.__root.state()
		if win_state_now == 'iconic' or win_state_now == 'icon':
			refresh = refresh * 5
		
		is_dev_change = self.get_all_dev()
		
		if is_dev_change is False: #no change return directly
			return refresh
		
		self.build_dev_dict(self.get_dev_names(self.__serial_common_name), self.__serial_common_name)
		self.show_dev_dict(self.__serial_common_name, self.open_or_close_port, self.__left_top_frame_com)
		if self.__expert_mode is True or self.__net_dev_cur_show is True:
			self.build_dev_dict(self.get_dev_names(self.__net_common_name), self.__net_key_word)
			self.show_dev_dict(self.__net_key_word, self.open_or_close_port, self.__left_top_frame_net)
			refresh = refresh / 2 + 1
		self.__try_auto_open_dev()
		
		is_changed,change_ver = self.get_cmd_changed()
		if self.check_set_config(self.__config) is True or is_changed is True:
			self.do_gui_callback(None,'auto_save',config=self.__config,ver=change_ver)
		
		return refresh
		
	def _on_windows_focus(self,event):
		if event.widget == self.__root:
			self.__is_focus_in = True
			self.do_gui_callback(None,'focus_in',cause='focus_in_event')
	def _onwindows_focus_out(self,event):
		if event.widget == self.__root:
			self.__is_focus_in = False
			self.do_gui_callback(None,'focus_out',cause='focus_out_event')
			self.__state = ''
	def _on_windows_msg_timeout(self,event=None):
		self.__sync_msg_rate = self.__sync_msg_count
		self.__sync_msg_count = 0
		#print("msg rate",self.__sync_msg_rate)
		self.do_gui_callback(None,'msg_sync',timeout=True)
	def _on_windows_msg_sync(self,*args):
		event_info = args[0]
		self.__sync_msg_count += 1
		#print ('Q-event',event_info.serial, event_info.x, event_info.y)
		#event_info.rootx, event_info.rooty
		self.do_gui_callback(None,'msg_sync')
	def _on_windows_msg_quit(self,*args):
		event_info = args[0]
		#print ('Q-event',event_info.serial, event_info.x, event_info.y)
		self.do_gui_callback(None,'msg_quit',cause='ctrl_quit')
	def _on_save_config_done(self,*args):
		print("args", args)
		ver = args[0]
		if isinstance(ver, int):
			self.set_cmd_auto_save_ver(ver)
	def refresh_serial_and_nets(self):
		if self.__need_refresh_gui_dev is False:
			return
		self.__need_refresh_gui_dev = False
		self.build_dev_dict(self.get_dev_names(self.__serial_common_name), self.__serial_common_name)
		self.show_dev_dict(self.__serial_common_name, self.open_or_close_port, self.__left_top_frame_com)
		if self.__expert_mode is True or self.__net_dev_cur_show is True or \
				len(dev_dict[self.__adb_common_name]) > 0 or len(self.__dev_list[self.__serial_common_name]) <= 8:
			self.build_dev_dict(self.get_dev_names(self.__net_common_name), self.__net_key_word)
			self.show_dev_dict(self.__net_key_word, self.open_or_close_port, self.__left_top_frame_net)
			self.__net_dev_cur_show = True
		
		self.__try_auto_open_dev()
	def refresh_devs_serial(self,dev_dict):
		if self.__serial_common_name in dev_dict:
			self.__dev_list[self.__serial_common_name] = dev_dict[self.__serial_common_name]
		
		self.__state = cur_state = self.__root.wm_state()
		if 'icon' == cur_state or 'iconic' == cur_state or 'withdrawn' == cur_state:
			self.__need_refresh_gui_dev = True
			return
		
		self.build_dev_dict(self.get_dev_names(self.__serial_common_name), self.__serial_common_name)
		self.show_dev_dict(self.__serial_common_name, self.open_or_close_port, self.__left_top_frame_com)
		self.__try_auto_open_dev()
	
	def refresh_devs_nets(self,dev_dict):
		if self.__net_common_name in dev_dict:
			self.__dev_list[self.__net_common_name] = dev_dict[self.__net_common_name]
		if self.__adb_common_name in dev_dict:
			self.__dev_list[self.__net_common_name] += dev_dict[self.__adb_common_name]
			
		self.__state = cur_state = self.__root.wm_state()
		if 'icon' == cur_state or 'iconic' == cur_state or 'withdrawn' == cur_state:
			self.__need_refresh_gui_dev = True
			return
		
		if self.__expert_mode is True or self.__net_dev_cur_show is True or \
				len(dev_dict[self.__adb_common_name]) > 0 or len(self.__dev_list[self.__serial_common_name]) <= 8:
			self.build_dev_dict(self.get_dev_names(self.__net_common_name), self.__net_key_word)
			self.show_dev_dict(self.__net_key_word, self.open_or_close_port, self.__left_top_frame_net)
			self.__net_dev_cur_show = True
			
		self.__try_auto_open_dev()
		
	def set_gui_window_size(self):
		print (self.__root.geometry())
		try:
			if 'window_size' in self.__config:
				self.__root.geometry(self.__config['window_size'])
				print (self.__config['window_size'])
			else:
				self.__root.geometry('792x727')
			#self.__root.attributes("-alpha",0.5)
		except:
			#self.__root.geometry(self.__config['window_size'])
			#self.__root.geometry("")
			pass
		self.__root.update_idletasks()
	def do_show_gui(self):
		#self.__root.attributes("-alpha",0.4)
		#self.__root.update_idletasks()
		self.__root.deiconify()
		#self.__root.attributes("-alpha",0.8)
		group_index = self.get_select_cmd_group_index()
		#print 'group_index',group_index
		self.__root.update_idletasks()
		#self.__root.attributes("-alpha",1.0)
		if group_index is None:
			group_index = 0
		self.build_cmd_dict(self.__min_cmd_per_group, group_index, 'CMD')
		self.__gui_shown = True
		self.__state = 'normal'
		print (self.__root.geometry())
		#self.__root.update()
	
	def update_gui(self,btn_callback,cmd_callback):
		self.__send_cmd_callback = cmd_callback
		self.__port_callback = btn_callback
		
		#self.get_all_dev()
		self.set_gui_window_size()
		self.build_dev_dict(self.get_dev_names(self.__serial_common_name), self.__serial_common_name)
		self.show_dev_dict(self.__serial_common_name, self.open_or_close_port, self.__left_top_frame_com)
		if self.__expert_mode is True:
			self.build_dev_dict(self.get_dev_names(self.__net_common_name), self.__net_key_word)
			self.show_dev_dict(self.__net_key_word, self.open_or_close_port, self.__left_top_frame_net)
			self.__net_dev_cur_show = True
		self.show_text_nodebook(self.__left_middle_frame)
		self.show_auto_send_ctrl_box(self.__right_bottom_frame.interior)
		
		self.show_cmd_dict(self.__right_bottom_frame.interior, 'CMD')
		
		if self.__frame_pack is False:
			self.show_tips_area()
			self.show_command_group(self.__right_frame,row=0,column=0,sticky=W+E)
			self.show_auto_parse_area(self.__right_frame,row=0,column=1,sticky=W+E+N+S)
			self.show_setting(self.__left_top_frame_setting)
			self._do_setup_external_execute_env()
			self.show_send_box(self.__send_frame)
			self.show_filter_box(self.__filter_frame)
			
			def select_all_text(event):
				try:
					event.widget.tag_add(Tkinter.SEL, "1.0", Tkinter.END)
				except:
					event.widget.select_range(0, Tkinter.END)
					pass
			def onCut(event):
				textstr = event.widget.get(Tkinter.SEL_FIRST, Tkinter.SEL_LAST)       
				event.widget.delete(Tkinter.SEL_FIRST, Tkinter.SEL_LAST)          
				self.__root.clipboard_clear()             
				self.__root.clipboard_append(textstr)
			def do_on_paste(event):
				try:
					cur_widget = event.widget
					if cur_widget.focus_get() == cur_widget:
						if cur_widget.selection_present():
							textstr = cur_widget.selection_get()
							cur_widget.clipboard_clear()
							cur_widget.clipboard_append(textstr)
						else:
							textstr = cur_widget.selection_get(selection='CLIPBOARD')
							if textstr != '':
								cur_widget.insert(Tkinter.INSERT, textstr)
				except Exception as e:
					print ('paste err:%s'%e)
					pass
			self.__root.bind_class('Text','<Control-Key-A>',select_all_text)
			self.__root.bind_class('Text','<Control-Key-a>',select_all_text)
			self.__root.bind_class('TEntry','<Control-Key-A>',select_all_text)
			self.__root.bind_class('TEntry','<Control-Key-a>',select_all_text)
			self.__root.bind_class('TCombobox','<Control-Key-A>',select_all_text)
			self.__root.bind_class('TCombobox','<Control-Key-a>',select_all_text)
			self.__root.bind_class('TEntry','<Button-3>',do_on_paste)
			self.__root.bind_class('TCombobox','<Button-3>',do_on_paste)
			self.__root.bind('<FocusIn>',self._on_windows_focus)
			self.__root.bind('<FocusOut>',self._onwindows_focus_out)
			#self.__root.bind('<F5>',self._on_windows_destroy)
			#self.__root.bind('<F6>',self._on_windows_destroy)
			self.__root.bind('<KeyRelease-F6>',self._on_windows_msg_timeout)
			self.__root.bind('<KeyPress-F5>',self._on_windows_msg_sync)
			self.__root.bind('<KeyRelease-F5>',self._on_windows_msg_sync)
			#self.__root.bind('<Visibility>',lambda event:self._on_windows_focus(event,'Visibility'))
			#self.__root.bind('<Activate>',lambda event:self._on_windows_focus(event,'Activate'))
			#self.__root.bind_class('TCombobox','<<ComboboxSelected>>',self.__commbo_display_hide) #bug fix for old ver
			self.__root.bind('<<Q-event-T>>',self._on_windows_msg_timeout)
			self.__root.bind('<<Q-event-Q>>',self._on_windows_msg_sync)
			self.__root.bind('<<QUIT-event-QUIT>>',self._on_windows_msg_sync)
			self.__root.bind('<<save-config-done>>', self._on_save_config_done)
			
			self.__left_frame.rowconfigure(10, weight=1)
			self.__left_frame.columnconfigure(2, weight=1)
			self.__right_frame.rowconfigure(1, weight=1)
			self.__right_frame.columnconfigure(1, weight=1)
			self.__left_top_frame.rowconfigure(1, weight=1)
			self.__left_top_frame.rowconfigure(1, weight=1)
			self.__left_top_frame.rowconfigure(3, weight=1)
			self.__left_top_frame.columnconfigure(2, weight=1)
			self.__left_middle_frame.rowconfigure(0, weight=1)
			self.__left_middle_frame.columnconfigure(1, weight=1)
			
			self.__left_top_frame_setting.grid(row=0,rowspan=4,column=0,sticky=W+N)
			self.__left_top_frame_com.grid(row=0,rowspan=2,column=1,columnspan=2,sticky=E+W+N)
			self.__left_top_frame_net.grid(row=2,rowspan=2,column=1,columnspan=2,sticky=E+W+N)
			self.__left_top_frame_com.columnconfigure(1, weight=1)
			self.__left_top_frame_net.columnconfigure(1, weight=1)
			self.__left_top_frame_com.bind("<Double-Button-1>",self.show_dev_frame_toggle)
			self.__left_top_frame_net.bind("<Double-Button-1>",self.show_dev_frame_toggle)
			
			self.__left_top_frame.grid(row=0,rowspan=8,column=0,columnspan=3,sticky=E+W)
			self.__left_middle_frame.grid(row=8,rowspan=3,column=0,columnspan=3,sticky=E+W+S+N)
			
			if self.__left_bottom_frame_pack is True:
				self.__left_bottom_frame.grid(row=11,rowspan=2,column=0,columnspan=3,sticky=E+W)
			self.__right_bottom_frame.grid(row=1,rowspan=self.__min_cmd_per_group,column=0,columnspan=2,sticky=E+W+S+N)
			
			def _grid_the_gui():
				self.__root.rowconfigure(4, weight=1)
				self.__root.columnconfigure(2, weight=1)
				self.__root.columnconfigure(4, weight=2)
				self.__main_paned_frame.grid(row=2,rowspan=3,column=0,columnspan=5,sticky=E+W+S+N)
				self.__button_frame.grid(row=0,column=0,columnspan=5,sticky=E+W)
				
				#self.__top_frame.grid(row=1,column=0,columnspan=5,sticky=E+W)
				if self.__right_frame_pack is True:
					self.__main_paned_frame.add(self.__left_frame,stretch="always",minsize="400")
					self.__main_paned_frame.add(self.__right_frame,stretch="always",minsize="200")
				else:
					self.__main_paned_frame.add(self.__left_frame,stretch="always",minsize="400")
					
				if self.__send_frame_pack is True:
					self.__send_frame.grid(row=5,column=0,columnspan=5,sticky=E+W)
				if self.__filter_frame_pack is True:
					self.__filter_frame.grid(row=6,column=0,columnspan=5,sticky=E+W)
			_grid_the_gui()
			self.__frame_pack = True


default_config_xml_content=r'''<?xml version="1.0" encoding="utf-8"?>
<icom>
	<config>
	<expert_mode>0</expert_mode>
	<shell>cmd.exe</shell>
	<textbackground>white</textbackground>
	<textforeground>black</textforeground>
	<textwidth>80</textwidth>
	<entryheight>25</entryheight>
	<listheight>6</listheight>
	<poll_timer>3000</poll_timer>
	<baudrate>115200</baudrate>
	<send_encoding>utf-8</send_encoding>
	<diaplay_encoding>utf-8</diaplay_encoding>
	<auto_start_multicast_server>1</auto_start_multicast_server>
	<auto_start_tcp_server>0</auto_start_tcp_server>
	<auto_start_udp_server>0</auto_start_udp_server>
	<tcp_srv_port>3000</tcp_srv_port>
	<udp_srv_port>3000</udp_srv_port>
	<multicast_ip>224.0.0.119</multicast_ip>
	<multicast_port>30000</multicast_port>
	<parse_key_word>61 74 </parse_key_word>
	<realtime>0</realtime>
	</config>
	<groups>
	<group name="AT" timeout="2000" tail="\r\n">
		<string desc="modem off">at+cfun=0</string>
		<string desc="modem on">at+cfun=1</string>
		<string desc="show infomation">ati</string>
		<string desc="show version">at^version?</string>
		<string desc="sysinfoex query">at^sysinfoex</string>
		<string desc="syscfgex query">at^syscfgex?</string>
		<string desc="pin status query">at^cpin?</string>
		<string desc="echo on">ate</string>
		<string desc="show AT error string">at+cmee=2</string>
		<string desc="ussd mode">at^ussdmode=0</string>
		<string desc="ussd 123 query number">AT+CUSD=1,"123",15</string>
	</group>
	<group name="linux" timeout="500" tail="\r\n">
		<string desc="busybox sh">busybox sh</string>
		<string desc="ifconfig">ifconfig</string>
		<string desc="list">ls</string>
		<string desc="ps">ps</string>
		<string desc="show current dir">pwd</string>
	</group>
	<group name="DOS" timeout="200" tail="\r\n">
		<string desc="list dir">dir</string>
		<string desc="list dir">cd</string>
		<string desc="show netcard ip">ipconfig</string>
		<string desc="show route">route print</string>
	</group>
	</groups>
</icom>'''
