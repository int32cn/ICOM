#!/usr/bin/python
# -*- coding= utf-8 -*-

import os
import traceback

from icom_ctrl_msg_id import *

Ports_App = None
manager_Q = None
ctrl_Q = None
gui_data_Q = None
gui_sync_ctrl_Q = None

def ports_set_vars(manager_q_var,ctrl_q_var,gui_sync_ctrl_Q_var,gui_data_Q__var):
	global ctrl_Q
	global gui_data_Q
	global manager_Q
	global gui_sync_ctrl_Q
	ctrl_Q = ctrl_q_var
	gui_data_Q = gui_data_Q__var
	manager_Q = manager_q_var
	gui_sync_ctrl_Q = gui_sync_ctrl_Q_var

def init_get_ports_app():
	global Ports_App
	if Ports_App is None:
		from telnet_ser import telnet_ports_ops
		Ports_App = telnet_ports_ops()
		Ports_App.set_callback('timer',port_timer_callback)
	return Ports_App

def ports_send_normal_success_ctrl_cmd_response(*msg_data):
	if gui_sync_ctrl_Q is not None:
		gui_sync_ctrl_Q.put(msg_data,True)

def ports_send_ctrl_cmd_response(*msg_data):
	if gui_data_Q is not None:
		gui_data_Q.put(msg_data,True)
		gui_data_Q.do_sync()

def get_flow_ctrl_info():
	return gui_data_Q.get_flow_ctrl_info()

def start_ports_timer(timer_id,timer_len):
	if Ports_App is not None:
		Ports_App.start_timer(timer_id,timer_len)
def modify_ports_timer(timer_id,timer_len):
	if Ports_App is not None:
		Ports_App.modify_timer(timer_id,timer_len)
def stop_ports_timer(timer_id):
	if Ports_App is not None:
		Ports_App.stop_timer(timer_id)

def ports_send_data_msg(*msg_data):
	if gui_data_Q is not None:
		gui_data_Q.put(msg_data,True)

def port_timer_callback(timer_id,timer_len):
	if gui_data_Q is not None:
		gui_data_Q.do_timer_out(timer_id,timer_len)

def ports_data_msg_do_sync():
	if gui_data_Q is not None:
		gui_data_Q.do_sync()

def ports_msg_flow_ctrl(msg_count):
	if gui_data_Q is not None:
		gui_data_Q.flow_ctrl(msg_count)
	if Ports_App is not None:
		Ports_App.set_flow_ctrl(msg_count)
	
def ports_send_manager_cmd_response(*msg_data):
	if manager_Q is not None:
		manager_Q.put(msg_data)

def ports_send_cmd_result(cmd_type,port_name,result_code,result_str):
	if gui_data_Q is not None:
		gui_data_Q.do_cmd_cnf(cmd_type,port_name,result_code,result_str)

def ports_error_callback(port_name,ser_handle,data_in):
	#print port_name,data_in
	ports_send_ctrl_cmd_response('E',port_name,data_in)

def ports_read_callback(port_name,ser_handle,data_in):
	#print port_name,data_in
	ports_send_data_msg('D',port_name,data_in)

def ports_open_log_file(port_name,open_type):
	if Ports_App is not None:
		Ports_App.flush_log_to_file(port_name)
		Ports_App.open_show_log_file(port_name,open_type)
	else:
		import os
		if os.path.exists(os.path.abspath('log')):
			os.startfile(os.path.abspath('log'))
	return 0,'ok'

def ports_set_time_interval(port_name,time_interval,auto_send):
	if Ports_App is not None:
		Ports_App.set_time_interval(port_name,time_interval,auto_send)
	else:
		return -1,'Ports App Open None'
	return 0,'ok'

def ports_set_cmd_list(cmd_list,time_interval,auto_send):
	if Ports_App is not None:
		Ports_App.set_cmd_list(cmd_list,time_interval,auto_send)
	else:
		return -1,'Ports App Open None'
	return 0,'ok'

def ports_set_local_echo(port_name,local_echo):
	if Ports_App is not None:
		Ports_App.set_local_echo(port_name,local_echo)
	else:
		return -1,'Ports App Open None'
	return 0,'ok'

def ports_set_show_timestamp(port_name,show_timestamp):
	if Ports_App is not None:
		Ports_App.set_timestamp_onoff(port_name,show_timestamp)
	else:
		return -1,'Ports App Open None'
	return 0,'show-timestamp:%s'%show_timestamp

def ports_send_file(port_name, file_name):
	if Ports_App is not None:
		Ports_App.send_file(port_name,file_name)
	else:
		return -1,'Ports App Open None'
	return 0,None

def ports_send_zmodem(port_name, file_path):
	if Ports_App is not None:
		Ports_App.send_zmodem(port_name,file_path)
	else:
		return -1,'Ports App Open None'
	return 0,None

def ports_open_ports_srv(port_name,port_type,serial_settings):
	global Ports_App
	ret_code = -1
	ret_str = 'error-start'
	
	try:
		if Ports_App is None:
			Ports_App = init_get_ports_app()
		name,ser_info = Ports_App.open_port(port_name,ports_read_callback,serial_settings)
		Ports_App.set_error_callback(port_name,ports_error_callback)
		Ports_App.set_sync_callback(ports_data_msg_do_sync)
		
		ret_code = 0
		ret_str = 'successful %s'%ser_info
	except Exception as e:
		traceback.print_exc()
		ret_str = 'exception %s when start-ports-srv'%e
		pass
	return ret_code,ret_str

def ports_start_ports_srv(port_name):
	global Ports_App
	ret_code = -1
	ret_str = 'error-start'
	try:
		if Ports_App is not None:
			Ports_App.start_port(port_name)
			ret_code = 0
			ret_str = 'ok'
	except Exception as e:
		ret_str = 'exception %s when start-ports-srv'%e
		pass
	return ret_code,ret_str

def ports_stop_ports_srv(port_name):
	ret_code = -1
	ret_str = 'error-stop'
	try:
		if Ports_App is not None:
			Ports_App.stop_port(port_name)
		ret_code = 0
		ret_str = 'ok'
	except Exception as e:
		ret_str = 'exception %s when stop-ports-srv'%e
		pass
	return ret_code,ret_str

def ports_stop_all_ports_srv():
	ret_code = -1
	ret_str = 'error-stop-all'
	try:
		if Ports_App is not None:
			Ports_App.stop_all_ports()
		ret_code = 0
		ret_str = 'ok'
	except Exception as e:
		ret_str = 'exception %s when stop-all-ports-srv'%e
		pass
	return ret_code,ret_str

def ports_stop_all_destrory():
	ret_code = -1
	ret_str = 'error-stop-all'
	try:
		if Ports_App is not None:
			Ports_App.stop_and_destrory()
		del Ports_App
		ret_code = 0
		ret_str = 'ok'
	except Exception as e:
		ret_str = 'exception %s when stop-all-ports-srv'%e
		pass
	return ret_code,ret_str

def ports_data_send(cur_dev,real_send_str,data_encoding):
	ret = None
	ret_code = -1
	ret_str = 'err-send'
	try:
		if cur_dev is not None:
			#print (cur_dev)
			if Ports_App is not None:
				ret = Ports_App.send_data(cur_dev,real_send_str,data_encoding)
				if ret is not None:
					ret_code = 0
					ret_str = 'ok'
			else:
				ret_str = "%s not-send"%real_send_str
	except Exception as e:
		ret_str = "exception %s when send:[%s]"%(e,real_send_str)
		pass
	
	return ret_code,ret_str

def ports_send_data_from_cmd_index(cur_dev,cmd_idx,update_data):
	ret = None
	ret_code = -1
	ret_str = 'err-send'
	try:
		if cur_dev is not None:
			if Ports_App is not None:
				ret = Ports_App.auto_send_from_cmd_list(cur_dev,cmd_idx,update_data)
				if ret is not None:
					ret_code = 0
					ret_str = 'ok'
			else:
				ret_str = "%s,%d not-send"%(cur_dev,cmd_idx)
	except Exception as e:
		ret_str = "exception %s when send:[%s,%d]"%(e,cur_dev,cmd_idx)
		pass
	
	return ret_code,ret_str

def ports_msg_proc(msg_type,*msg_data):
	#if 'S' != msg_type:
	#	print ('PROCESS',msg_type,msg_data)
	port_name = None
	ret_code = -100
	ret_str = 'unknown'
	if 'SI' == msg_type:
		port_name = msg_data[0]
		cmd_index = msg_data[1]
		update_data = msg_data[2]
		ret_code,ret_str = ports_send_data_from_cmd_index(port_name,cmd_index,update_data)
	elif 'S' == msg_type: #send data
		port_name = msg_data[0]
		real_send_str = msg_data[1]
		data_encoding = msg_data[2]
		ret_code,ret_str = ports_data_send(port_name,real_send_str,data_encoding)
	elif 'OPEN' == msg_type:
		port_name = msg_data[0]
		port_type = msg_data[1]
		serial_settings = msg_data[2]
		ret_code,ret_str = ports_open_ports_srv(port_name,port_type,serial_settings)
	elif 'START' == msg_type:
		port_name = msg_data[0]
		ret_code,ret_str = ports_start_ports_srv(port_name)
	elif 'CLOSE' == msg_type:
		port_name = msg_data[0]
		ret_code,ret_str = ports_stop_ports_srv(port_name)
	elif 'KEEP-ALIVE' == msg_type:
		ports_send_manager_cmd_response('KEEP-ALIVE')
		return
	elif 'FLOW-CTRL' == msg_type:
		msg_ctrl_count = msg_data[0]
		ports_msg_flow_ctrl(msg_ctrl_count)
		return
	elif msg_type == 'START-TIMER':
		timer_id = msg_data[0]
		timer_len = msg_data[0]
		start_ports_timer(timer_id,timer_len)
		ret_code = 0
	elif msg_type == 'STOP-TIMER':
		timer_id = msg_data[0]
		stop_ports_timer(timer_id)
		ret_code = 0
	elif msg_type == 'MODIFY-TIMER':
		timer_id = msg_data[0]
		timer_len = msg_data[1]
		modify_ports_timer(timer_id,timer_len)
		ret_code = 0
		return
	elif 'CLOSE-ALL' == msg_type:
		port_name = 'all-devs'
		ret_code,ret_str = ports_stop_all_ports_srv()
	elif 'SHOW-LOG' == msg_type:
		port_name = msg_data[0]
		open_type = msg_data[1]
		ret_code,ret_str = ports_open_log_file(port_name,open_type)
	elif 'AUTO-SEND-TIME' == msg_type:
		port_name = msg_data[0]
		time_interval = msg_data[1]
		auto_send = msg_data[2]
		ret_code,ret_str = ports_set_time_interval(port_name,time_interval,auto_send)
	elif 'CMD-LIST' == msg_type:
		cmd_list = msg_data[0]
		time_interval = msg_data[1]
		auto_send = msg_data[2]
		ret_code,ret_str = ports_set_cmd_list(cmd_list,time_interval,auto_send)
	elif 'LOCAL-ECHO' == msg_type:
		port_name = msg_data[0]
		set_local_echo = msg_data[1]
		ret_code,ret_str = ports_set_local_echo(port_name,set_local_echo)
	elif 'SHOW-TIMESTAMP' == msg_type:
		port_name = msg_data[0]
		show_time_stamp = msg_data[1]
		ret_code,ret_str = ports_set_show_timestamp(port_name,show_time_stamp)
	elif 'SEND-FILE' == msg_type:
		port_name = msg_data[0]
		file_name = msg_data[1]
		ret_code,ret_str = ports_send_file(port_name,file_name)
	elif 'SEND-ZMODEM' == msg_type:
		port_name = msg_data[0]
		file_path = msg_data[1]
		ret_code,ret_str = ports_send_zmodem(port_name,file_path)
	elif 'READY-ACK' == msg_type:
		read_ack_data = msg_data[0]
		return
	elif msg_type == 'QUIT':
		ports_stop_all_destrory()
		return
	elif msg_type == 'INIT-PORTS':
		port_name = ""
		if init_get_ports_app() is not None:
			ret_code = 0
			ret_str = "ok"
	else:
		print ('unknown msg %s,%s' %(msg_type,msg_data))
		return
	
	ports_send_cmd_result(msg_type,port_name,ret_code,ret_str)


def work_ports_main(cur_instance_num,win_title,manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q):
	ports_set_vars(manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q)
	pro_ok = 0
	pro_fail = 0
	gui_data_Q.put(('READY','PORTS',os.getpid()))
	#print ('ports_ctrl_Q',ports_ctrl_Q.qsize(),ports_ctrl_Q.__dict__)
	
	while True:   #ctrl quit status
		try:
			msg_data =  ports_ctrl_Q.get()
			#if not IN_FROZEN_STATE:
			#	print ('work',msg_data)
			if msg_data[0] == 'QUIT':
				ICOM_ports.ports_msg_proc(*msg_data)
				break
			ICOM_ports.ports_msg_proc(*msg_data)
			pro_ok += 1
		except Exception as e:
			print ('work process exception',e)
			pro_fail += 1
			pass
	
	print ('work process quit ok:%d,fail:%d\n'%(pro_ok,pro_fail))
	os._exit(0)
	
if __name__ == '__main__':
	from queue import Queue
	manager_Q,ports_ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q = Queue(),Queue(),Queue(),Queue(),Queue(),Queue()
	pro_status = [range(6)]
	work_ports_process(0,"iCOM",manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q)
	
	
	
