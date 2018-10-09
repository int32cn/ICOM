#!/usr/bin/python
# -*- coding= utf-8 -*-

from icom_ctrl_msg_id import *
srv_server = None
netsrv_ctrl_Q = None
gui_Q = None
gui_sync_ctrl_Q = None

g_instance_num = 0
g_multicast_allow = False
udp_srv_online = False

user_name = 'unknown'
manager_u = None
manager_m = None
user_m = None


def netsrv_set_vars(cur_instance_num,netsrv_ctrl_q_var,gui_sync_ctrl_Q_var,gui_q_var):
	global netsrv_ctrl_Q
	global gui_Q
	global gui_sync_ctrl_Q
	global g_instance_num
	g_instance_num = cur_instance_num
	netsrv_ctrl_Q = netsrv_ctrl_q_var
	gui_Q = gui_q_var
	gui_sync_ctrl_Q = gui_sync_ctrl_Q_var

def get_expert_mode(config_list):
	expert_mode = False
	if 'expert_mode' in config_list and config_list['expert_mode'].isdigit():
		if int(config_list['expert_mode']) > 0:
			expert_mode = True
	else:
		config_list.setdefault('expert_mode',0)
	return expert_mode

def start_srv_options(type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
	global srv_server
	if srv_server is not None:
		srv_server.start_server(type,host,port,multicast_ip)
	
def stop_srv_options(sock_type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
	global srv_server
	if srv_server is not None:
		srv_server.stop_server(sock_type,host,port,multicast_ip)

def start_srv_timer(timer_id,timer_len):
	if srv_server is not None:
		srv_server.start_timer(timer_id,timer_len)
def modify_srv_timer(timer_id,timer_len):
	if srv_server is not None:
		srv_server.modify_timer(timer_id,timer_len)
def stop_srv_timer(timer_id):
	if srv_server is not None:
		srv_server.stop_timer(timer_id)

def netsrv_send_data(cur_dev,real_send_bytes,_encoding):
	if srv_server is not None:
		return srv_server.send_data(cur_dev,real_send_bytes,_encoding)
	return None
def netsrv_set_cmd_list(cmd_list,time_interval,auto_send):
	if srv_server is not None:
		srv_server.set_cmd_list(cmd_list,time_interval,auto_send)
	else:
		return -1,'srv_server Open None'
	return 0,'ok'

def netsrv_send_data_from_cmd_index(cur_dev,cmd_index,update_data):
	if srv_server is not None:
		ret = srv_server.auto_send_from_cmd_list(cur_dev,cmd_index,update_data)
		return (0,'ok') if ret else (-1,'send err')
	return -1,'srv-none'

def user_multicast_msg_process(peer,srv_info,msg_data):
	if manager_m is not None and srv_server is not None:
		return manager_m.multicast_receive(srv_server.get_inet_aton(peer[0]),msg_data)
	return False
	
def user_loggin_change(status):
	if user_m is not None and get_cur_multicast_allow() is True:
		user_m.start_login(user_name,status)
		print ('start user:%s %d\n'%(user_name,status))

def user_logoff():
	if user_m is not None and get_cur_multicast_allow() is True:
		user_m.start_logoff()
		print ('stop user:%s\n'%user_name)

def send_msg_to_Q(ctrl_Q,*msg_data):
	try:
		ctrl_Q.put(msg_data)
	except Exception as e:
		print ('send_ctrl error',msg_data,e)
		pass
	return 0

def send_data_to_gui_Q(ctrl_Q,*msg_data):
	try:
		ctrl_Q.put(msg_data)
	except Exception as e:
		print ('send_ctrl error',msg_data,e)
		pass
	return 0

def send_timer_msg_to_gui_ctrl_Q(ctrl_Q,*msg_data):
	try:
		ctrl_Q.put(msg_data)
	except Exception as e:
		print ('send_ctrl error',msg_data,e)
		pass
	return 0

def port_read_callback(port_name,srv_info, msg_data):
	return send_msg_to_Q(gui_Q,'D',port_name,msg_data)
	
def port_error_callback(port_name,srv_info,err_cause):
	return send_msg_to_Q(gui_Q,'E',port_name,err_cause)

def port_timer_callback(timer_id,timer_len):
	if gui_Q is not None:
		return gui_Q.do_timer_out(timer_id,timer_len)
	
def start_srv():
	if srv_server is not None:
		def callback(pear,srv_info,msg_data):
			if isinstance(pear,tuple):
				port_read_callback('tcp(%s:%d)'%(pear[0],pear[1]),srv_info, msg_data)
			elif isinstance(pear,str):
				port_read_callback(pear,srv_info, msg_data)
			else:
				port_read_callback('tcp %s'%str(pear),srv_info, msg_data)
		def udp_callback(pear,srv_info,msg_data):
			if isinstance(pear,tuple):
				port_read_callback('udp(%s:%d)'%(pear[0],pear[1]),srv_info, msg_data)
			elif isinstance(pear,str):
				port_read_callback(pear,srv_info, msg_data)
			else:
				port_read_callback('udp %s'%str(pear),srv_info, msg_data)
		def tcp_err_callback(pear,srv_info,err_cause):
			port_error_callback('tcp(%s:%d)'%(pear[0],pear[1]),srv_info, err_cause)
		def udp_err_callback(pear,srv_info,err_cause):
			port_error_callback('udp(%s:%d)'%(pear[0],pear[1]),srv_info, err_cause)
		def timer_callback(timer_id,time_out):
			port_timer_callback(timer_id, time_out)
		def udp_cast_callback(pear,srv_info,msg_data):
			processed_data = user_multicast_msg_process(pear,srv_info,msg_data)
			if processed_data is not None:
				if not isinstance(processed_data,str):
					try:
						processed_data = processed_data.decode()
					except Exception as e:
						print('multicast data err:%s'%e)
						processed_data = str(processed_data)
						pass
				port_read_callback('multicast %s'%str(pear),srv_info,processed_data)
		srv_server.set_callback('tcp',callback)
		srv_server.set_callback('udp',udp_callback)
		srv_server.set_callback('udp_cast',udp_cast_callback)
		srv_server.set_callback('tcp_err',tcp_err_callback)
		srv_server.set_callback('udp_err',udp_err_callback)
		srv_server.set_callback('timer',timer_callback)
		srv_server.run()

def stop_srv():
	if srv_server is not None:
		srv_server.stop()

def srv_stop_and_destrory():
	global srv_server
	if srv_server is not None:
		srv_server.stop()
	srv_server = None
	
def check_start_srv(config_list):
	try:
		global udp_srv_online
		global srv_server
		if srv_server is None:
			import as_select
			event = as_select.Event()
			event_loop_thread = as_select.EventLoopThread(event)
			event_loop_thread.setDaemon(True)
			event_loop_thread.start()
			
			srv_server = as_select.srv_control(event_loop_thread)
			event.wait() # Let the loop's thread signal us, rather than sleeping
			
			#import srv_select
			#srv_server = srv_select.tcp_srv()
		
		if 'auto_start_tcp_server' in config_list and 'tcp_srv_port' in config_list:
			if isinstance(config_list['auto_start_tcp_server'],int) or config_list['auto_start_tcp_server'].isdigit():
				if isinstance(config_list['tcp_srv_port'],int) or config_list['tcp_srv_port'].isdigit():
					tcp_allow = int(config_list['auto_start_tcp_server'])
					port = int(config_list['tcp_srv_port']) + g_instance_num
					if tcp_allow > 0 and port > 0:
						start_srv_options('tcp','0.0.0.0',port)
		if 'auto_start_udp_server' in config_list and 'udp_srv_port' in config_list:
			if  isinstance(config_list['auto_start_udp_server'],int) or config_list['auto_start_udp_server'].isdigit():
				if  isinstance(config_list['udp_srv_port'],int) or config_list['udp_srv_port'].isdigit():
					udp_allow = int(config_list['auto_start_udp_server'])
					port = int(config_list['udp_srv_port']) + g_instance_num
					if udp_allow > 0 and port > 0:
						start_srv_options('udp','0.0.0.0',port)
						udp_srv_online = True
			
		expert_mode = get_expert_mode(config_list)
		if expert_mode is True and 'auto_start_multicast_server' in config_list and 'multicast_port' in config_list:
			if isinstance(config_list['auto_start_multicast_server'],int) or config_list['auto_start_multicast_server'].isdigit():
				if  isinstance(config_list['multicast_port'],int) or config_list['multicast_port'].isdigit():
					multicast_allow = int(config_list['auto_start_multicast_server'])
					port = int(config_list['multicast_port']) + g_instance_num
					if multicast_allow > 0 and port > 0 and len(config_list['multicast_ip']) > 0:
						start_srv_options('udp','0.0.0.0',port,config_list['multicast_ip'])
						set_cur_multicast_allow(True)
		start_srv()
	except Exception as e:
		print ('start srv err:%s'%e)
		pass

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
	
def get_cur_udp_online(config_list):
	udp_allow = 0
	port = 0
	if 'auto_start_udp_server' in config_list and config_list['auto_start_udp_server'].isdigit():
		udp_allow = int(config_list['auto_start_udp_server'])
	if 'udp_srv_port' in config_list and config_list['udp_srv_port'].isdigit():
		port = int(config_list['udp_srv_port'])
	if srv_server is not None and udp_allow > 0 and port > 0:
		return True
	return False

def user_module_init(root,config_list,step,basedir,cur_version):
	global user_name
	global manager_u
	global manager_m
	global user_m
	global srv_server
	if step == 0:
		import getpass
		user_name = getpass.getuser()
		if g_instance_num > 0:
			user_name = '%s-%d'%(user_name,g_instance_num)
	elif step == 1:
		from UserP import logger,user_manager,multicast_manager,UserManager
		manager_u = user_manager(logger)
		manager_m = multicast_manager(logger)
		user_m = UserManager(manager_u,manager_m,root)
	elif step == 2:
		user_m.load_key_from_path(basedir)
	elif step == 3:
		if srv_server is not None:
			manager_m.set_send_function(srv_server.do_send_udp_cast)
			#set current user
			user_key_list = srv_server.get_own_addr_hash_list()
			user_m.set_current_user(user_key_list, user_name, get_cur_udp_port(config_list))
		user_m.set_current_verion(cur_version[0],cur_version[1])

def user_module_finalize():
	if user_m is not None:
		print ('stop run\n')

def user_get_all_list():
	if user_m is None:
		return None
	user_list = user_m.get_user_list()
	if user_list is not None and srv_server is not None:
		user_all = []
		for user_key,user_info in user_list.items():
			user_all.append('%s Addr:%s Port:%d Status:%d\n'%(user_info.NickName,srv_server.get_inet_ntoa(user_info.Addr),user_info.UdpPort,user_info.Status))
		return ''.join(user_all)
	return None

def netsrv_send_ctrl_cmd_response(*msg_data):
	return send_msg_to_Q(gui_Q,*msg_data)

def netsrv_send_normal_success_ctrl_cmd_response(*msg_data):
	return send_msg_to_Q(gui_sync_ctrl_Q,*msg_data)

def netsrv_send_cmd_result(cmd_type,result_code,result_str):
	if cmd_type == "S" and result_code == 0:
		gui_Q.do_cmd_cnf(cmd_type,"NETSRV",result_code,result_str)
	else:
		netsrv_send_ctrl_cmd_response('C-NETSRV',cmd_type,result_code,result_str)

def netsrv_send_self_quit_msg(*msg_data):
	return send_msg_to_Q(netsrv_ctrl_Q,*msg_data)

def netsrv_ready_ack_msg_proc(config_list,basedir,cur_version):
	if get_expert_mode(config_list) is False:
		netsrv_send_self_quit_msg("QUIT","NOT-EXPERT-MODE-NET-SRV-QUIT")
		return
	#print config_list
	check_start_srv(config_list)
	if 'expert_mode' in config_list and isinstance(config_list['expert_mode'],bool) and config_list['expert_mode'] is True:
		user_module_init(None,config_list,0,basedir,cur_version)
		user_module_init(None,config_list,1,basedir,cur_version)
		user_module_init(None,config_list,2,basedir,cur_version)
		user_module_init(None,config_list,3,basedir,cur_version)
		user_loggin_change(get_cur_udp_online(config_list))

def netsrv_msg_proc(msg_type,*msg_data):
	ret_code = -1
	ret_str = 'unknown'
	if 'SI' == msg_type:
		cur_dev = msg_data[0]
		cmd_index = msg_data[1]
		update_data = msg_data[2]
		ret_code,ret_str = netsrv_send_data_from_cmd_index(cur_dev,cmd_index,update_data)
	elif msg_type == 'S':
		cur_dev = msg_data[0]
		real_send_bytes = msg_data[1]
		_encoding = msg_data[2] if msg_data[2] else 'utf-8'
		if not isinstance(real_send_bytes,bytes):
			real_send_bytes = bytes(real_send_bytes,_encoding)
		ret = netsrv_send_data(cur_dev,real_send_bytes,_encoding)
		ret_code = 0 if ret else -1
	elif msg_type == 'READY-ACK':
		config_list = msg_data[0]['config']
		basedir = msg_data[0]['basedir']
		cur_version = msg_data[0]['version']
		app_title = msg_data[0]['title']
		netsrv_ready_ack_msg_proc(config_list,basedir,cur_version)
		return
	elif msg_type == 'START-TIMER':
		timer_id = msg_data[0]
		timer_len = msg_data[0]
		start_srv_timer(timer_id,timer_len)
		ret_code = 0
	elif msg_type == 'STOP-TIMER':
		timer_id = msg_data[0]
		stop_srv_timer(timer_id)
		ret_code = 0
	elif msg_type == 'MODIFY-TIMER':
		timer_id = msg_data[0]
		timer_len = msg_data[1]
		modify_srv_timer(timer_id,timer_len)
		ret_code = 0
		return
	elif 'CMD-LIST' == msg_type:
		cmd_list = msg_data[0]
		time_interval = msg_data[1]
		auto_send = msg_data[2]
		ret_code,ret_str = netsrv_set_cmd_list(cmd_list,time_interval,auto_send)
	elif msg_type == 'START-SRV':
		type = msg_data[0]
		host = msg_data[1]
		port = msg_data[2]
		multicast_ip = msg_data[3]
		start_srv_options(type,host,port,multicast_ip)
		ret_code = 0
	elif msg_type == 'STOP-SRV':
		type = msg_data[0]
		host = msg_data[1]
		port = msg_data[2]
		multicast_ip = msg_data[3]
		stop_srv_options(type,host,port,multicast_ip)
		ret_code = 0
	elif msg_type == 'START-ALL':
		start_srv()
		ret_code = 0
	elif msg_type == 'STOP-ALL':
		stop_srv()
		ret_code = 0
	elif msg_type == 'USER-CHANGE':
		online = msg_data[0]
		user_loggin_change(online)
		ret_code = 0
	elif msg_type == 'USER-LOGOFF':
		user_loggin_change(False)
		ret_code = 0
	elif msg_type == 'USER-FINALIZE':
		user_module_finalize()
		ret_code = 0
	elif msg_type == 'GET-USER-LIST':
		ret_code = 0
		ret_str = user_get_all_list()
	elif msg_type == 'QUIT':
		srv_stop_and_destrory()
		return
	else:
		print ('NETSRV_RCV unknown msg',msg_type,msg_data)
		
	netsrv_send_cmd_result(msg_type,ret_code,ret_str)
	