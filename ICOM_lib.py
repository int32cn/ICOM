#!/usr/bin/python
# -*- coding= utf-8 -*-
import sys
from icom_view import *
from xml_json import xml_to_dict,do_parse_dict_to_xml,do_parse_json_file_to_xml
#from dos import dos_ops
from threading import Thread,current_thread
from icom_ctrl_msg_id import *
import traceback

TOOL_SHORT_NAME = "ICOM"
CONFIG_FILE_NAME = ".%s_config.xml"%TOOL_SHORT_NAME
CONFIG_BAKUP_FILE_NAME = ".%s_config_autobakup.xml"%TOOL_SHORT_NAME

app_tile = 'icom'

ports_gui = None
Dos_App = None
_tk_root = None
_win_icom = None
srv_server = None
udp_srv_online = False
parse_key_word = None
timver_interval = 5000
timer_interval_scale = 1
gui_refresh_done = None
gui_refresh_count = 0
shell_program = "cmd.exe"
net_auto_send_data = "AT\r"
tray_icon = None
g_multicast_allow = False
g_instance_num = 0
xml_config_dict = None
g_config_list = None
logger = None

ctrl_Q = None
out_Q = None
tray_ctrl_Q = None
netsrv_ctrl_Q = None
main_loop_tasks = []
g_base_dir = '.'
g_debug_mode = False
parse_xml_error = False

def set_ports_gui_var(ports_gui_var,shell_program_var,net_auto_send_data_var,win_icom_var,config_list,ctrl_q_var,out_q_var,tray_ctrl_q_var,netsrv_ctrl_q_var,base_dir_var):
	global ports_gui
	global shell_program
	global net_auto_send_data
	global _win_icom
	global g_config_list
	global ctrl_Q
	global out_Q
	global tray_ctrl_Q
	global netsrv_ctrl_Q
	global g_base_dir
	ports_gui = ports_gui_var
	shell_program = shell_program_var
	net_auto_send_data = net_auto_send_data_var
	_win_icom = win_icom_var
	g_config_list = config_list
	ctrl_Q = ctrl_q_var
	out_Q = out_q_var
	tray_ctrl_Q = tray_ctrl_q_var
	netsrv_ctrl_Q = netsrv_ctrl_q_var
	g_base_dir = base_dir_var
	

def ports_refresh(event=None):
	global gui_refresh_done
	global timer_interval_scale
	if ports_gui is not None:
		timer_interval_scale = ports_gui.refresh_gui()
		ports_gui.dev_frame_auto_hide_check()
		ports_gui.actions_idle_task_check()
		gui_refresh_done = True

def ports_change_refresh(ref_dev_dict):
	if ports_gui is not None and _win_icom is not None:
		ports_gui.refresh_devs_serial(ref_dev_dict)

def nets_change_refresh(ref_dev_dict):
	if ports_gui is not None and _win_icom is not None:
		ports_gui.refresh_devs_nets(ref_dev_dict)

def adb_change_refresh(ref_dev_dict):
	if ports_gui is not None and _win_icom is not None:
		ports_gui.refresh_devs_nets(ref_dev_dict)

def port_read_callback(port_name,ser_handle,data_in):
	if ports_gui is not None:
		ports_gui.submit_add_text(port_name,None,data_in)

def show_log_file_or_dir_callback(e,**kargs):
	if 'port_name' in kargs and 'open_type' in kargs:
		send_show_log_ports_req(kargs['port_name'],kargs['open_type'])

def set_local_echo_callback(e,**kargs):
	if 'port_name' in kargs and 'localecho' in kargs:
		return send_ctrl_cmd_to_ports('LOCAL-ECHO',kargs['port_name'],kargs['localecho'])

def show_timestamp_callback(e,**kargs):
	if 'port_name' in kargs and 'show' in kargs:
		send_show_timestamp_ports_req(kargs['port_name'],kargs['show'])

def auto_send_time_set_callback(e,**kargs):
	if 'time_interval' in kargs and 'port_name' in kargs and 'auto_send' in kargs:
		send_auto_send_time_interval_ports_req(kargs['port_name'],kargs['time_interval'],kargs['auto_send'])

def auto_send_cmd_list_callback(e,**kargs):
	if 'cmd_list' in kargs and 'time_interval' in kargs and 'auto_send' in kargs:
		send_auto_send_cmd_list_ports_req(kargs['cmd_list'],kargs['time_interval'],kargs['auto_send'])
		send_auto_send_cmd_list_ports_req(kargs['cmd_list'],kargs['time_interval'],kargs['auto_send'])

def auto_send_cmd_from_cmd_list_idx_callback(e,**kargs):
	if 'cmd_idx' in kargs and 'port_name' in kargs:
		if 'text' in kargs:
			send_auto_send_cmd_idx_data_req(kargs['port_name'],kargs['cmd_idx'],kargs['text'])
		else:
			send_auto_send_cmd_idx_data_req(kargs['port_name'],kargs['cmd_idx'],None)

def send_file_to_ports_callback(e,**kargs):
	if 'port_name' in kargs and 'file_name' in kargs:
		send_file_to_ports_req(kargs['port_name'],kargs['file_name'])

def send_zmodem_path_to_ports_callback(e,**kargs):
	if 'port_name' in kargs and 'file_path' in kargs:
		send_zmodem_to_ports_req(kargs['port_name'],kargs['file_path'])
	
def port_cmd_callback(cmd_type,port_name,ret_code,ret_str):
	if ports_gui is None:
		return
	if 'S' == cmd_type:
		if 0 != ret_code:
			port_error_callback(port_name,None,ret_str)
	elif 'OPEN' == cmd_type:
		if 0 != ret_code:
			ports_gui.disconnect_open_dev(port_name)
			ports_gui._after_schecule('ports-%s-open-fail-tips'%port_name,30,ports_gui.show_tips,' Open %s %s'%(port_name,ret_str),0)
		else:
			ports_gui.open_dev_status(port_name,'CONNECT')
			send_start_ports_req(port_name)
			ports_gui._after_schecule('ports-%s-open-success-tips'%port_name,30,ports_gui.show_tips,' Open %s %s'%(port_name,ret_str),0)
	elif 'START' == cmd_type:
		if 0 != ret_code:
			port_error_callback(port_name,None,ret_str)
		else:
			ports_gui.connect_open_dev(port_name)
			if len(net_auto_send_data) > 0 and check_sock_com(port_name) is True:
				send_data_req(port_name,net_auto_send_data,ports_gui.get_send_encoding())
	elif 'CLOSE' == cmd_type:
		if 0 != ret_code:
			port_error_callback(port_name,None,ret_str)
	elif 'SHOW-LOG' == cmd_type:
		if 0 != ret_code:
			ports_gui._after_schecule('SHOW-LOG',30,ports_gui.show_tips,' Show Log %s %s'%(port_name,ret_str),0)
	elif 'AUTO-SEND-TIME' == cmd_type:
		print ('auto send time set:%d'%ret_code)
	elif ret_code != 0 or (ret_str and 'ok' != ret_str):
		print ('unkown cmd callback',cmd_type,port_name,ret_code,ret_str)

def tray_notify_proc(cmd_type,cmd_args):
	if ports_gui is None:
		return
	global g_debug_mode
	
	if g_debug_mode is not True and ('PORTS_CHANGE' == cmd_type or 'NETS_CHANGE' == cmd_type or 'ADB_CHANGE' == cmd_type):
		print (cmd_type,cmd_args)
	if 'PORTS_CHANGE' == cmd_type:
		ports_change_refresh(cmd_args)
	elif 'NETS_CHANGE' == cmd_type:
		nets_change_refresh(cmd_args)
	elif 'ADB_CHANGE' == cmd_type:
		adb_change_refresh(cmd_args)
	elif 'QUIT' == cmd_type:
		ports_gui._after_schecule('destroy',0,win_destroy_pre)
		ports_gui._after_schecule('destroy2',3000,win_destroy_pre)
	elif 'LICENSE' == cmd_type:
		ports_gui._after_schecule('show_license',0,ports_gui.show_license,cmd_args)
	elif 'SHOW' == cmd_type:
		ports_gui.show_gui()
	elif 'HIDE' == cmd_type:
		ports_gui.hide_gui()
	elif 'SHOW-OR-HIDE' == cmd_type:
		ports_gui.show_or_hide_gui()
	elif 'EXPERT MODE' == cmd_type:
		if cmd_args is True:
			g_config_list['expert_mode'] = 0
		else:
			g_config_list['expert_mode'] = 1
		ports_gui.set_cmd_changed(True)
		print ('EXPERT MODE',cmd_args)
	elif 'DEBUG MODE' == cmd_type:
		print ('DEBUG MODE',cmd_args)
		if cmd_args is False:
			g_debug_mode = True
		else:
			g_debug_mode = False
		ports_gui.set_debug_mode(g_debug_mode)
	elif 'TRAY-DATA' == cmd_type:
		expert_mode = get_expert_mode(g_config_list)
		tray_icon_path = os.path.join(g_base_dir,'earth.ico')
		if 'encoding' in g_config_list:
			_encoding = g_config_list['encoding']
		else:
			_encoding = 'utf-8'
		send_ctrl_cmd_to_Q(tray_ctrl_Q,'INIT-DATA',{'expert_mode':expert_mode,'icon':tray_icon_path,'encoding':_encoding})
	else:
		print ('tray_notify_proc unkonwn',cmd_type)
	
def port_err_tips_scedule(port_name,tips_info,timeout):
	#print port_name,data_in
	if ports_gui is not None:
		ports_gui.show_tips('%s ERROR: %s'%(port_name,tips_info), timeout)
		ports_gui.open_dev_error(port_name)
	
def port_error_callback(port_name,ser_handle,data_in):
	#print port_name,data_in
	if ports_gui is not None:
		port_err_tips_scedule(port_name,data_in,0)

def check_server_message_dev(dev_name):
	if dev_name.startswith('tcp(') or dev_name.startswith('udp('):
		return True
	return False

def check_sock_com(text_str):
	'''check if sock com format local_addr@dst_addr:dst_port'''
	is_net_port = True
	step_check = 0
	if text_str.startswith(r'tcp://') or text_str.startswith(r'udp://'):
		text_str = text_str[6:]
	elif text_str.startswith(r'telnet://') or text_str.startswith(r'TELNET://'):
		text_str = text_str[9:]
	for ch in text_str:
		if ch != '.' and ch != ':' and ch != '@' and not ch.isdigit():
			is_net_port = False
			break
		
	if is_net_port is True:
		net_info = text_str.split('@')
		if len(net_info) == 2:
			net_local_addr = net_info[0]
			dst_info = net_info[1].split(':')
			if len(dst_info) == 2 and dst_info[1].isdigit():
				net_dst_addr = dst_info[0]
				net_dst_port = int(dst_info[1])
			else:
				is_net_port = False
		else:
			is_net_port = False
	return is_net_port


def send_ctrl_cmd_to_Q(ctrl_Q,*msg_data):
	try:
		ctrl_Q.put(msg_data)
		if g_debug_mode is True or ('SI' != msg_data[0] and 'S' != msg_data[0] and 'CMD-LIST' != msg_data[0]):
			print ('lib send_ctrl',msg_data)
	except Exception as e:
		print ('lib send_ctrl error',msg_data,e)
		pass
	return 0

def send_ctrl_cmd_to_ports(*msg_data):
	return send_ctrl_cmd_to_Q(ctrl_Q,*msg_data)

def send_open_ports_req(port_name,port_type,port_setting):
	return send_ctrl_cmd_to_ports('OPEN',port_name,port_type,port_setting)

def send_start_ports_req(port_name):
	return send_ctrl_cmd_to_ports('START',port_name)

def send_show_log_ports_req(port_name,open_type):
	return send_ctrl_cmd_to_ports('SHOW-LOG',port_name,open_type)

def send_show_timestamp_ports_req(port_name,show):
	return send_ctrl_cmd_to_ports('SHOW-TIMESTAMP',port_name,show)

def send_auto_send_time_interval_ports_req(port_name,time_interval,auto_send):
	return send_ctrl_cmd_to_ports('AUTO-SEND-TIME',port_name,time_interval,auto_send)

def send_auto_send_cmd_list_ports_req(cmd_list,time_interval,auto_send):
	send_ctrl_cmd_to_netsrv('CMD-LIST',cmd_list,time_interval,auto_send)
	return send_ctrl_cmd_to_ports('CMD-LIST',cmd_list,time_interval,auto_send)

def send_auto_send_cmd_idx_data_req(port_name,cmd_idx,update_data=None):
	if check_server_message_dev(port_name):
		return send_ctrl_cmd_to_netsrv('SI',port_name,cmd_idx,update_data)
	return send_ctrl_cmd_to_ports('SI',port_name,cmd_idx,update_data)

def send_file_to_ports_req(port_name,file_name):
	if check_server_message_dev(port_name):
		return send_ctrl_cmd_to_netsrv('SEND-FILE',port_name,file_name)
	return send_ctrl_cmd_to_ports('SEND-FILE',port_name,file_name)

def send_zmodem_to_ports_req(port_name,file_path):
	if check_server_message_dev(port_name):
		return send_ctrl_cmd_to_netsrv('SEND-ZMODEM',port_name,file_path)
	return send_ctrl_cmd_to_ports('SEND-ZMODEM',port_name,file_path)
	
def send_sync_msg_flowctrl_req(msg_count):
	return send_ctrl_cmd_to_ports('FLOW-CTRL',msg_count)

def send_data_req(port_name,real_data_str,_encoding):
	send_encoding = _encoding if 'utf-8' != _encoding else None #default to utf-8, not need send default value
	if check_server_message_dev(port_name):
	    return send_ctrl_cmd_to_netsrv('S',port_name,real_data_str,send_encoding)
	return send_ctrl_cmd_to_ports('S',port_name,real_data_str,send_encoding)

def send_close_ports_req(port_name):
	return send_ctrl_cmd_to_ports('CLOSE',port_name)

def send_close_all_ports_req():
	return send_ctrl_cmd_to_ports('CLOSE-ALL','PORTS-NO-OPEN')
	
def send_close_work_process_req():
	return send_ctrl_cmd_to_ports('CLOSE-ALL','PORTS-ALL-CLOSE')

def send_ctrl_cmd_to_netsrv(*msg_data):
	if netsrv_ctrl_Q is None:
		return None
	return send_ctrl_cmd_to_Q(netsrv_ctrl_Q,*msg_data)

def send_timer_ctrl_cmd(*msg_data):
	if ctrl_Q is None:
		return None
	return send_ctrl_cmd_to_Q(ctrl_Q,*msg_data)

def start_srv_options(sock_type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
	return send_ctrl_cmd_to_netsrv('START-SRV',sock_type,host,port,multicast_ip)
	
def stop_srv_options(sock_type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
	return send_ctrl_cmd_to_netsrv('STOP-SRV',sock_type,host,port,multicast_ip)

def send_data_to_netsrv_req(cur_dev,real_send_str,_encoding):
	return send_ctrl_cmd_to_netsrv('S',cur_dev,real_send_str,_encoding)
	
def start_srv():
	return send_ctrl_cmd_to_netsrv('START-ALL',0)

def stop_srv():
	return send_ctrl_cmd_to_netsrv('STOP-ALL',0)

def user_get_all_list():
	return send_ctrl_cmd_to_netsrv('GET-USER-LIST',0)

def user_loggin_change(online):
	return send_ctrl_cmd_to_netsrv('USER-CHANGE',online)

def user_logoff():
	return send_ctrl_cmd_to_netsrv('USER-LOGOFF','QUIT')

def user_module_finalize():
	return send_ctrl_cmd_to_netsrv('USER-FINALIZE','QUIT')
	
def port_click_callback(text_str,cur_action,event=None):
	
	try:
		if not isinstance(text_str,str):
			text_str = str(text_str)
		port_type = 'NET'
		is_net_port_com = check_sock_com(text_str)
		__serial_common_name,__net_common_name = ports_gui.get_dev_common_name()
		comindex = text_str.find(__serial_common_name)
		netindex = text_str.find(__net_common_name)
		if comindex >= 0 or is_net_port_com is True:
			port_name = text_str
			if is_net_port_com is not True:
				comnum = text_str[comindex:].replace(__serial_common_name,'')
				comnum = comnum.strip(')')
				port_name = __serial_common_name+comnum
				port_type = 'COM'
			if cur_action == 'open':
				serial_settings = ports_gui.get_serial_setting()
				log_name = ports_gui.get_log_file_name(port_name)
				serial_settings['log'] = log_name
				send_open_ports_req(port_name,port_type,serial_settings)
				ports_gui.add_open_dev(port_name,event)
				
			else:
				ports_gui.disconnect_open_dev(port_name,event)
				send_close_ports_req(port_name)
			return True
		elif netindex >=0:
			port_name = text_str[netindex:]
			ports_gui.show_tips('get adapter info'+str(port_name), 3000)
		else:
			ports_gui.show_tips('get info error'+str(text_str), 3000)
	except Exception as e:
		print (text_str, 'port_click_callback error',e)
		ports_gui.show_tips('port_click_callback error:%s,%s'%(text_str,e), 3000)
		pass
	return False


def cmd_click_callback(cmd_ctx):
	send_str = ''
	
	try:
		if cmd_ctx is not None:
			cur_dev = send_str = ''
			if 'calctext' in cmd_ctx and cmd_ctx['calctext'] is not None:
				send_str = cmd_ctx['calctext']
			elif hasattr(cmd_ctx['text'],'get'):
				send_str = cmd_ctx['text'].get()
			elif isinstance(cmd_ctx['text'],bytes):
				send_str = cmd_ctx['text'].decode('utf-8')
			else:
				send_str = str(cmd_ctx['text'])
			tail_str = cmd_ctx['tail']
			send_str = send_str + tail_str
			real_send_str = ports_gui.get_real_string(send_str)
			cur_encoding = ports_gui.get_send_encoding()
			real_send_bytes = ports_gui.get_bytes_from_string(real_send_str)
			if 'senddev' in cmd_ctx and cmd_ctx['senddev'] is not None:
				cur_dev = cmd_ctx['senddev']
			else:
				cur_dev = ports_gui.get_select_tab()
			
			if not cur_dev:
				ports_gui.show_tips('not find current open device %s'%cmd_ctx,3000)
			else:
				ret = send_data_req(cur_dev,real_send_bytes,cur_encoding)
				if ret == None:
					ports_gui.show_tips(real_send_str+' send error!',3000)
	except Exception as e:
		print ('cmd_click_callback error', send_str,e)
		ports_gui.show_tips('send (%s) error(%s)'%(send_str,e),3000)
		pass

def all_ports_close_callback(e,**kargs):
	if isinstance(kargs,dict) and 'cause' in kargs:
		if kargs['cause'] == 'no_dev_tabs':
			send_close_work_process_req()
		elif kargs['cause'] == 'no_dev_open':
			send_close_all_ports_req()

def port_remove_callback(e,**kargs):
	is_com_dev = kargs['is_com_dev'] if 'is_com_dev' in kargs else False
	port_name = kargs['dev_name'] if 'dev_name' in kargs else None
	btn = kargs['button'] if 'button' in kargs else None
	if is_com_dev is False or port_name is None:
		return
	try:
		if ports_gui is not None:
			ports_gui.disconnect_open_dev(port_name,None)
		send_close_ports_req(port_name)
		if btn is not None and hasattr(btn,'relief') and btn['relief'] != Tkinter.RAISED:
			btn['relief'] = Tkinter.RAISED
	except Exception as e:
		print ('remove callback error', port_name, e)
		pass

def start_srv_callback(e,**kargs):
	#print (e,kargs)
	global udp_srv_online
	#if 'var' in kargs:
	#	print (kargs['var'].get())
	multicast_ip = None
	if 'multicast' in kargs:
		multicast_ip = kargs['multicast']
	if 'port' in kargs and 'type' in kargs and 'var' in kargs:
		cur_srv_online_status = False
		enable_val = kargs['var'].get()
		srv_type  = kargs['type']
		
		if enable_val == 0:
			start_srv_options(srv_type,'0.0.0.0',kargs['port'],multicast_ip)
			start_srv()
			cur_srv_online_status = True
		else:
			stop_srv_options(srv_type,'0.0.0.0',kargs['port'],multicast_ip)
			
		if srv_type == 'udp':
			udp_srv_online = cur_srv_online_status
		if srv_type == 'udp_cast' and multicast_ip is not None:
			if cur_srv_online_status == True:
				set_cur_multicast_allow(True)
			else:
				set_cur_multicast_allow(False)
		if srv_type == 'udp' and get_cur_multicast_allow() is True:
			user_loggin_change(udp_srv_online)

def get_cur_udp_port(config_list):
	port = 0
	if 'udp_srv_port' in config_list and config_list['udp_srv_port'].isdigit():
		port = int(config_list['udp_srv_port']) + g_instance_num
	if port <= 0:
		port = 3000 #default value
	return port

def get_cur_multicast_allow():
	return g_multicast_allow
	
def set_cur_multicast_allow(allow):
	global g_multicast_allow
	g_multicast_allow = allow
	

def get_expert_mode(config_list):
	expert_mode = False
	if 'expert_mode' in config_list and config_list['expert_mode'].isdigit():
		if int(config_list['expert_mode']) > 0:
			expert_mode = True
	else:
		config_list.setdefault('expert_mode',0)
	return expert_mode

def get_realtime_mode(config_list):
	realtime = False
	if 'realtime' in config_list and config_list['realtime'].isdigit():
		if int(config_list['realtime']) > 0:
			realtime = True
	else:
		config_list.setdefault('realtime',0)
	return realtime

def working_thread_task(work_Q,task_down_callback=None):
	global worker_Queue
	task_doing = 0
	while True:
		data = None
		try:
			if task_doing > 0:
				data = work_Q.get_nowait()
			else:
				data = work_Q.get()
		except Exception as e:
			#all task done
			if task_down_callback is not None:
				task_down_callback(task_doing,None)
			task_doing = 0
			pass
		#print data,task_doing
		if data is not None:
			if data[0] == 'quit':
				break;
			try:
				task_doing = 1
				data[0](data[1])
				task_doing = 2
			except Exception as e:
				print ('worker error:',e)
				task_doing = 3
				pass
			if task_down_callback is not None:
				task_down_callback(task_doing,data[1])
	worker_Queue = None
	print ('worker thread quit')
	
worker_Queue = None

def task_done_callback(done_status,task_param):
	if ports_gui is not None and _win_icom is not None:
		if isinstance(task_param,dict) and 'ver' in task_param and isinstance(task_param['ver'],int):
			#ports_gui.set_cmd_auto_save_ver(task_param)
			_win_icom.event_generate('<<QUIT-event-QUIT>>', data=task_param['ver'])
			#ports_gui._after_schecule('save-config-done',0,ports_gui.set_cmd_auto_save_ver,task_param['ver'])
		elif task_param is not None:
			#frm = ports_gui.get_drop_area_wiget().config(bg='#FFFFF0')
			#frm.config(bg='#FFFFF0')
			ports_gui._after_schecule('task-done',0,lambda :ports_gui.get_drop_area_wiget().config(bg='#FFFFF0'))
		else:
			print ('task done',done_status,task_param)
	
def start_working_thread():
	try:
		from queue import Queue
	except:
		from Queue import Queue
	global worker_Queue
	worker_Queue = Q = Queue()
	t = Thread(target=working_thread_task,args=(Q,task_done_callback))
	t.setDaemon(True)
	t.start()
	
def set_parse_key_word(key_word):
	global parse_key_word
	parse_key_word = key_word
	
def start_convert(at_txt_file):
	import ShowAtCmd
	try_codec_list = ('utf-8','utf-16','gb2312')
	if parse_key_word is not None:
		k_words = ShowAtCmd.getAtKeyWords()
		if parse_key_word not in k_words:
			ShowAtCmd.setAtKeyWord(parse_key_word)
	ret = ShowAtCmd.changeAtDisplay(at_txt_file)
	if 0 != ret:
		for try_codec in try_codec_list:
			try:
				at_txt_file = at_txt_file.decode(try_codec)
				ret = ShowAtCmd.changeAtDisplay(at_txt_file)
				print ("start_convert, ret:%s"%ret)
			except Exception as e:
				print ("start_convert, decode ut-8:%s"%e)
				ret = -1;
				pass
			if 0 == ret:
				break
	
def add_working_task(task_entry,task_param=None):
	if worker_Queue is None:
		start_working_thread()
	if worker_Queue is not None:
		worker_Queue.put((task_entry,task_param))

def stop_working_thread():
	if worker_Queue is not None:
		add_working_task('quit')
	
def wait_working_thread_quit():
	while worker_Queue is not None:
		add_working_task('quit')
		time.sleep(0.1)

def process_start_ready(process_name,*args):
	if 'PORTS' == process_name:
		expert_mode = get_expert_mode(g_config_list)
		realtime = get_realtime_mode(g_config_list)
		send_ctrl_cmd_to_Q(ctrl_Q,'READY-ACK',{'title':app_tile,'expert_mode':expert_mode,'realtime':realtime})
	elif 'NETSRV' == process_name and netsrv_ctrl_Q:
		send_ctrl_cmd_to_Q(netsrv_ctrl_Q,'READY-ACK',
			{'title':app_tile,'basedir':g_base_dir,
				'version':[icom_version*100+icom_subversion,icom_version_description],'config':g_config_list})

def netsrv_cmd_response_proc(cmd_type,ret_code,ret_str):
	if cmd_type == 'GET-USER-LIST':
		if ret_str != '' and ret_str != None and ret_code == 0:
			port_read_callback('user',{},'%s%s%s'%(os.linesep,ret_str,os.linesep))
		elif get_expert_mode(g_config_list):
			port_read_callback('user',{},'%s%s%s'%(os.linesep,ret_str,os.linesep))
	elif ret_code != 0:
		ports_gui._after_schecule('netsrv-cmd-err',0,ports_gui.show_tips,' execute %s err:%s'%(cmd_type,ret_str),0)
	
def receive_data_proc(msg_type,*msg_data):
	need_submit_trig = False
	if g_debug_mode is True:
		print ('recv',msg_type,msg_data)
	if msg_type == 'D':  # data
		port_name = msg_data[0]
		port_data = msg_data[1]
		port_read_callback(port_name,None,port_data)
		need_submit_trig = True
	elif msg_type == 'C': # command
		cmd_type = msg_data[0]
		port_name = msg_data[1]
		ret_code = msg_data[2]
		ret_str = msg_data[3]
		port_cmd_callback(cmd_type,port_name,ret_code,ret_str)
	elif msg_type == 'C-NETSRV':
		cmd_type = msg_data[0]
		ret_code = msg_data[1]
		ret_str = msg_data[2]
		netsrv_cmd_response_proc(cmd_type,ret_code,ret_str)
		need_submit_trig = True
	elif msg_type == 'E': # error
		port_name = msg_data[0]
		port_data = msg_data[1]
		port_error_callback(port_name,None,port_data)
	elif msg_type == 'NOTIFY': # sys-tray nofity:
		item_name = msg_data[0]
		item_para = msg_data[1]
		tray_notify_proc(item_name,item_para)
	elif msg_type == 'READY':
		name = msg_data[0]
		process_start_ready(name,*msg_data)
	else:
		print ('get data',msg_data)
	
	return need_submit_trig

def show_focus_in_callback(e,**kargs):
	#print ('focus_in callback',current_thread().ident)
	ports_gui.refresh_serial_and_nets()
	receive_data_thread_task(True)

def show_focus_out_callback(e,**kargs):
	#print ('focus_out callback')
	ports_gui._after_schecule('Q',100,lambda:receive_data_thread_task(True))

def msg_sync_callback(e,**kargs):
	#print ('msg_sync callback')
	if 'timeout' in kargs:
		receive_data_thread_task(True)
	else:
		receive_data_thread_task()

def receive_data_thread_task(timeout_sync=False):
	msg_count = 0
	need_triger_text_Q = False
	while True:
		try:
			out_data = out_Q.get(block=False)
			print (type(out_data),out_data)
			if isinstance(out_data,list):
				for data_msg in out_data:
					need_trig = receive_data_proc(*data_msg)
					msg_count += 1
			else:
				need_trig = receive_data_proc(*out_data)
				msg_count += 1
			
			if not need_triger_text_Q and need_trig:
				need_triger_text_Q = True
		except Exception as e:
			#print ('recv_data Exception',e)
			break
			pass
	if not ports_gui:
		return
	if need_triger_text_Q:
		ports_gui.triger_show_text()
	elif timeout_sync and not ports_gui.check_is_display_text_queue_empty():
		ports_gui.triger_show_text()
	#if msg_count != 1:
	#	print('dataproc tid:%d\n'%current_thread().ident)
	#print ('msg cnt',msg_count)

def get_sync_msg_param(msg_int_data):
	msg_int_param1 = msg_int_param2 = msg_int_param3 = msg_int_param4 = 0
	msg_data_count = len(msg_int_data)
	if msg_data_count <= 1:
		pass
	elif msg_data_count <= 2:
		msg_int_param1 = msg_int_data[1]
	elif msg_data_count <= 3:
		msg_int_param1 = msg_int_data[1]
		msg_int_param2 = msg_int_data[2]
	elif msg_data_count <= 4:
		msg_int_param1 = msg_int_data[1]
		msg_int_param2 = msg_int_data[2]
		msg_int_param3 = msg_int_data[3]
	else:
		msg_int_param1 = msg_int_data[1]
		msg_int_param2 = msg_int_data[2]
		msg_int_param3 = msg_int_data[3]
		msg_int_param4 = msg_int_data[4]
	
	msg_int_type = msg_int_data[0]
	return (msg_int_type, msg_int_param1, msg_int_param2, msg_int_param3, msg_int_param4)

def receive_msg_Q_thread_task(*args):
	gui_sync_ctrl_Q = args[0]
	while True:
		try:
			msg_int_data = gui_sync_ctrl_Q.get(block=True)
			if not ports_gui:
				print ('receive_msg_Q_thread_task break')
				break
				
			msg_int_type, msg_int_param1, msg_int_param2, msg_int_param3, msg_int_param4 = get_sync_msg_param(msg_int_data)
			if ICOM_CTRL_MSG.ID_PROC_QUIT_MSG == msg_int_type:
				_win_icom.event_generate('<<QUIT-event-QUIT>>', data='this is test data', serial=msg_int_type, x=msg_int_param1, y=msg_int_param2, rootx=msg_int_param3,rooty=msg_int_param4)
			else:
				#print ('event-genarate', msg_int_type, msg_int_param1, msg_int_param2, msg_int_param3, msg_int_param4)
				if ICOM_CTRL_MSG.ID_TIMER_TIMEOUT ==  msg_int_type:
					_win_icom.event_generate('<<Q-event-T>>', serial=msg_int_type, x=msg_int_param1)
				else:
					_win_icom.event_generate('<<Q-event-Q>>', serial=msg_int_type, x=msg_int_param1, y=msg_int_param2, rootx=msg_int_param3,rooty=msg_int_param4)
		except Exception as e:
			print ('recv_data Exception',e)
			#print (traceback.print_exc())
			pass
def start_recv_data_thread(gui_sync_ctrl_Q):
	t = Thread(target=receive_msg_Q_thread_task,args=(gui_sync_ctrl_Q,))
	t.setDaemon(True)
	t.start()
	
def drop_down_callback(data):
	print (type(data), data)
	def change_drop_area():
		if ports_gui is not None:
			frm = ports_gui.get_drop_area_wiget()
			frm.config(bg='#00FF7F')
	for file_name in data:
		print ("fileName", file_name)
		ports_gui._after_schecule('save-config',2000,add_working_task,start_convert,file_name)
	if ports_gui is not None:
		#frm = ports_gui.get_drop_area_wiget()
		#frm.config(bg='#00FF7F')
		ports_gui._after_schecule('drop-down',0,change_drop_area)


def tlv_manager_callback(e,**kargs):
	#print (e,kargs)
	import stk_tlv
	init_data_val = None
	description_data_val = None
	title_val = 'Editer'
	close_callback = None
	if 'root' not in kargs:
		return
	if 'data_val' in kargs:
		init_data_val = kargs['data_val']
	if 'description_val' in kargs:
		description_data_val = kargs['description_val']
	if 'title' in kargs:
		title_val = kargs['title']
	if 'close_callback' in kargs:
		close_callback = kargs['close_callback']
	def _toplevel_win_destroy(self):
		if close_callback is not None:
			close_callback(self)
		self.destroy()
		pass
	root_win = kargs['root']
	stk_tlv.register_stk_tlv_struct()
	editer_win = Tkinter.Toplevel(root_win)
	editer_win.title('%s'%title_val)
	editer_win.protocol("WM_DELETE_WINDOW",lambda w=editer_win:_toplevel_win_destroy(w))
	ui = stk_tlv.TLV_GUI(editer_win,init_data_val,description_data_val)
	stk_tlv.set_tlv_gui_obj(ui)
	#buf = hex_to_str("D0308103014003820281820500350702020405051F023902058E47080761706E2D6C74653C030208AE3E0521D30101039000")
	#TLV_ParseAll(buf)
	ui.gui_init()
	ui.gui_run()

def get_app_title():
	app_tile = 'iCOM for Windows'
	if OS_name.upper() != 'NT':
		app_tile = 'iCOM for %s'%OS_name
	if g_instance_num > 0:
		app_tile = '%s (%d)'%(app_tile,g_instance_num)
	return app_tile

def set_logger(_logger):
	global logger
	logger = _logger

def win_close_sys_stay(program_share_status):
	if g_instance_num > 0:
		program_share_status[0] = 1
		win_destroy_schedule()
	elif ports_gui:
		ports_gui.hide_gui()
	
def win_destroy_schedule():
	ports_gui._after_schecule('destroy',0,win_destroy_pre)
	ports_gui._after_schecule('destroy-x',3000,win_destroy_pre)

def win_destroy_pre():
	global _tk_root
	posts_gui_config_change = True
	destroy_try_times = 0
	for task_id in main_loop_tasks:
		try:
			_win_icom.after_cancel(task_id)
		except Exception as e:
			print ('_win_icom.after_cancel:%s'%e)
			pass
	try:
		posts_gui_config_change = ports_gui.check_set_config(g_config_list) is True or ports_gui.get_cmd_changed()[0] is True
		ports_gui.all_task_destroy()
	except Exception as e:
		print ('win destroy_pre:%s'%e)
		pass
	print ('posts_gui_config_change:%d'%posts_gui_config_change)
	
	if posts_gui_config_change is True or os.path.exists(CONFIG_FILE_NAME) is not True:
		if xml_config_dict is not None and parse_xml_error is False:
			try:
				print ('need save cmdlist')
				if worker_Queue is None:
					do_parse_dict_to_xml(xml_config_dict,CONFIG_FILE_NAME)
					print ('new cmdlist saved')
			except Exception as e:
				print ('save config error:%s'%e)
				pass
	else:
		print ('no change')
	#print ('save cmdlist ok')
	try:
		user_logoff()
		stop_srv()
		stop_working_thread()
		user_module_finalize()
	except Exception as e:
		print ('descroy exception:%s'%e)
		pass
	print ('stop work thread ok')
	wait_working_thread_quit()
	while destroy_try_times < 3:
		try:
			_win_icom.destroy()
			break
		except Exception as e:
			print ('_win_icom.destroy:%s'%e)
			destroy_try_times += 1
			pass
	print ('_win_icom.destroy ok')
	destroy_try_times = 0
	while destroy_try_times < 3:
		try:
			_tk_root.destroy()
			break
		except Exception as e:
			print ('_tk_root.destroy:%s'%e)
			destroy_try_times += 1
			pass
	print ('_tk_root.destroy ok')
	_tk_root = None

def get_config_and_cmd_list():
	global xml_config_dict
	global parse_xml_error
	conf_file_names = (CONFIG_FILE_NAME,CONFIG_BAKUP_FILE_NAME)
	for i in (0,1):
		conf_file_name = conf_file_names[i]
		str_xml,user_config_file = load_config(conf_file_name)
		if user_config_file is False and 0 == i:
			continue
		#convert xml to dict
		cmd_list = {}
		config_list = {}
		parse_xml_error = False
		try:
			xml_config_dict = xml_to_dict(str_xml)
			if 'icom' in xml_config_dict:
				cmd_list = xml_config_dict['icom']
				if 'config' in cmd_list:
					config_list = cmd_list['config']
				if 'groups' in cmd_list:
					cmd_list = cmd_list['groups']
			else:
				raise 'error config formant'
		except Exception as e:
			print ('config file:%s parse error:%s'%(conf_file_name,e))
			parse_xml_error = True
			cmd_list = {}
			config_list = {}
			pass
		
		if i == 0 and user_config_file is True and parse_xml_error is False:
			#bakup config file
			f = open(conf_file_names[-1], 'wb')
			if f:
				f.write(str_xml)
				f.close()
			break
	#print (time.time(),config_list)
	if 'group' in cmd_list:
		cmd_list = cmd_list['group']
	
	return config_list,cmd_list

def get_default_win_info(config_list):
	win_info = []
	if 'window_size' in config_list:
		cur_window_size = config_list['window_size']#792x727+593+144
		cur_window_size = cur_window_size.replace('x',' ').replace('+',' ').replace('-',' -')
		list_one = cur_window_size.split()
		if len(list_one) == 4:
			win_info = [int(e) for e in list_one if e.isdigit() or e[1:].isdigit()]
	return (cur_window_size,win_info) if len(win_info) == 4 else (None,None)
	
def gui_main(logger,cur_instance_num,win_title,manager_Q,ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,gui_sync_ctrl_Q,out_Q,pro_share_status):
	global g_instance_num
	global _tk_root
	global _win_icom
	global main_loop_tasks
	global app_tile
	g_instance_num = cur_instance_num
	
	config_list, cmd_list = get_config_and_cmd_list()
	expert_mode = get_expert_mode(config_list)
	
	try:
		if expert_mode and is_module_exists('ICOM_netsrv'):
			from TkinterDnD2 import TkinterDnD
			Tkinter.NoDefaultRoot()
			_tk_root = TkinterDnD.Tk()
		else:
			Tkinter.NoDefaultRoot()
			_tk_root = Tkinter.Tk()
	except Exception as e:
		print ('tkinter error:%s\n'%e)
		Tkinter.NoDefaultRoot()
		_tk_root = Tkinter.Tk()
	
	cur_window_geometry,win_info = get_default_win_info(config_list)
	print ('expert_mode:%d,cur_window_geometry:%s win_info:%s\n'%(expert_mode,cur_window_geometry,win_info))
	_win_icom = None
	
	try:
		if win_info:
			_win_icom = Tkinter.Toplevel(_tk_root, width=win_info[0], height=win_info[1], bd=0)
		else:
			_win_icom = Tkinter.Toplevel(_tk_root, width=792, height=727, bd=0)
	except Exception as e:
		print ("creat Toplevel exception %s"%e)
		_win_icom = Tkinter.Toplevel(_tk_root)
		pass
	
	_tk_root.withdraw()
	_win_icom.minsize(width=600, height=500)
	
	shell_program = "cmd.exe"
	net_port_auto_send_data = "AT\r"
	ports_gui = com_ports_gui(_win_icom, win_title)
	ports_gui.set_instance_num(g_instance_num)
	ports_gui.load_icon()
	
	if 'shell' in config_list and config_list['shell'] != '':
		shell_program = config_list['shell']
	if 'net_config_data' in config_list and config_list['net_config_data'] != '':
		net_port_auto_send_data = ports_gui.get_real_string(config_list['net_config_data'])
	if 'parse_key_word' in config_list:
		set_parse_key_word(config_list['parse_key_word'])
	set_ports_gui_var(ports_gui,shell_program,net_port_auto_send_data,_win_icom,
					config_list,ctrl_Q,out_Q,tray_ctrl_Q,netsrv_ctrl_Q,ports_gui.get_base_dir())
	
	#print cmd_list
	ports_gui.set_cmd_list(cmd_list)
	ports_gui.set_config(config_list)
	
	def work_config_auto_save(task_param):
		try:
			if 'config' in task_param:
				do_parse_dict_to_xml(task_param['config'],CONFIG_FILE_NAME)
		except Exception as e:
			print ('auto save fail:%s'%e)
			if ports_gui is not None and win is not None:
				ports_gui._after_schecule('auto-save-config-fail',0,ports_gui.show_tips,'auto save config fail:%s'%e,0)
			pass
	
	def config_auto_save(event,**kargs):
		if 'ver' in kargs and isinstance(kargs['ver'],int):
			task_param = {}
			xml_config_dict_save = xml_config_dict.copy()
			task_param.setdefault('ver', kargs['ver'])
			task_param.setdefault('config', xml_config_dict_save)
			add_working_task(work_config_auto_save,task_param)
			
	ports_gui.set_dropdown_callback(drop_down_callback)
	ports_gui.set_userlist_callback(user_get_all_list)
	ports_gui.register_callback('dev_remove',port_remove_callback)
	ports_gui.register_callback('start_TLV',tlv_manager_callback)
	ports_gui.register_callback('auto_save',config_auto_save)
	ports_gui.register_callback('ports_all_close',all_ports_close_callback)
	ports_gui.register_callback('start_tcp_srv',start_srv_callback)
	ports_gui.register_callback('start_udp_srv',start_srv_callback)
	ports_gui.register_callback('start_multicast_srv',start_srv_callback)
	ports_gui.register_callback('show_log_file_dir',show_log_file_or_dir_callback)
	ports_gui.register_callback('local_echo',set_local_echo_callback)
	ports_gui.register_callback('show_time',show_timestamp_callback)
	ports_gui.register_callback('time_interval',auto_send_time_set_callback)
	ports_gui.register_callback('cmd_list',auto_send_cmd_list_callback)
	ports_gui.register_callback('auto_send_cmd_idx',auto_send_cmd_from_cmd_list_idx_callback)
	ports_gui.register_callback('send_file',send_file_to_ports_callback)
	ports_gui.register_callback('send_zmodem_path',send_zmodem_path_to_ports_callback)
	ports_gui.register_callback('focus_in',show_focus_in_callback)
	ports_gui.register_callback('focus_out',show_focus_out_callback)
	ports_gui.register_callback('msg_sync',msg_sync_callback)
	ports_gui.register_callback('msg_quit',win_destroy_schedule)
	
	start_recv_data_thread(gui_sync_ctrl_Q)
	ports_gui.update_gui(port_click_callback, cmd_click_callback)
	_win_icom.protocol('WM_DELETE_WINDOW',lambda s=pro_share_status:win_close_sys_stay(s))
	
	ports_gui.do_show_gui()
	
	print('start mainloop time: %d tid:%d\n'%(time.time(),current_thread().ident))
	_tk_root.mainloop()
	print ('mainloop out')
	pro_share_status[0] += 100
	ports_gui = None
	sys.exit(0)

if __name__ == '__main__':
	from queue import Queue
	manager_Q,ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,out_Q = Queue(),Queue(),Queue(),Queue(),Queue()
	pro_status = [range(6)]
	gui_main(sys.stdout,0,"iCOM",manager_Q,ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,out_Q,pro_status)
