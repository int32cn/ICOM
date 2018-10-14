#!/usr/bin/python
# -*- coding= utf-8 -*-

import multiprocessing 
import os
import sys
from datetime import datetime
from multiprocessing.queues import Queue
from threading import current_thread

import time
from multiprocessing.dummy import Process as dummyProcess
from multiprocessing.dummy import Lock as dummyLock
from icom_ctrl_msg_id import *
import icom_flow_ctrl

NET_SRV_PROCESS_DELAY_START = 1
IN_FROZEN_STATE = False
gui_sync_ctrl_Q = None
processers_count = 1
g_cur_instance_num = 1

#if hasattr(os,'environ') and 'NUMBER_OF_PROCESSORS' in os.environ:
#	processers_count = os.environ['NUMBER_OF_PROCESSORS']

# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking


if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

def gui_process(pro_name,cur_instance_num,win_title,manager_Q,ports_ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status,__stdout):
	from ICOM_lib import gui_main
	if is_in_frozen_state():
		sys.stdout = __stdout
		sys.stderr = __stdout
	gui_main(__stdout,cur_instance_num,win_title,manager_Q,ports_ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status)

def work_ports_process(pro_name,cur_instance_num,win_title,manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q):
	import ICOM_ports
	ICOM_ports.ports_set_vars(manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q)
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

def netsrv_process(pro_name,cur_instance_num,win_title,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_Q,pro_status):
	import ICOM_netsrv
	ICOM_netsrv.netsrv_set_vars(cur_instance_num,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_Q)
	pro_ok = 0
	pro_fail = 0
	gui_Q.put(('READY','NETSRV',os.getpid()))
	
	while True:   #ctrl quit status
		try:
			msg_data =  netsrv_ctrl_Q.get()
			#print ('work',msg_data)
			if msg_data[0] == 'QUIT':
				pro_status[3] = 1
				ICOM_netsrv.netsrv_msg_proc(*msg_data)
				break
			ICOM_netsrv.netsrv_msg_proc(*msg_data)
			pro_ok += 1
		except Exception as e:
			print ('netsrv process exception',e,msg_data)
			pro_fail += 1
			pass
	
	print ('netsrv process quit ok:%d,fail:%d\n'%(pro_ok,pro_fail))
	os._exit(0)

def send_quit_message_to_process(ctrl_Q):
	try:
		ctrl_Q.put(('QUIT',100))
	except Exception as e:
		print ('send_quit_message_to_process err:%s'%e)
		pass
	

class StdoutQueue(Queue):
	def __init__(self, maxsize=0):
		Queue.__init__(self,maxsize,ctx=multiprocessing)
	def get_timestamp(self):
		t = datetime.now()
		return t.strftime("%Y-%m-%d %H:%M:%S.%f")
	def write(self,msg):
		if msg != '\r\n' and msg != '\n' and msg != ' ':
			log_msg = '%s %s'%(self.get_timestamp(),msg)
		else:
			log_msg = msg
		self.put(log_msg)
	def error(self,msg):
		log_msg = '%s %s\n'%(self.get_timestamp(),msg)
		self.put(log_msg)
	def debug(self,msg):
		log_msg = '%s %s\n'%(self.get_timestamp(),msg)
		self.put(log_msg)
	def info(self,msg):
		log_msg = '%s %s\n'%(self.get_timestamp(),msg)
		self.put(log_msg)
	def flush(self):
		if sys.__stdout__:
			sys.__stdout__.flush()

	
log_file = None
def open_file_log():
	global log_file
	try:
		if is_in_frozen_state():
			t = datetime.now()
			f_name = os.path.abspath(os.path.join('log','icom_debug%d_%s.log'%(g_cur_instance_num,t.strftime("%M"))))
			log_file = open(f_name,'w')
			print ('start log:%s %s'%(f_name,log_file))
	except:
		pass
	

def record_file_log(log_Q, pro_status):
	global log_file
	if not log_file:
		return
	
	while True:
		try:
			msg_data =  log_Q.get_nowait()
			if msg_data:
				log_file.write(msg_data)
			else:
				break
		except Exception as e:
			break

def record_file_log_flush():
	if log_file:
		log_file.flush()
	
def close_file_log(pro_status):
	if log_file:
		t = datetime.now()
		log_file.write('%s pro_status:%s\n'%(t.strftime("%Y-%m-%d %H:%M:%S %f"),pro_status[:]))
		log_file.flush()
		log_file.close()
	
def is_module_exists(module_name):
	_is_exists = False
	try:
		__import__(module_name)
		_is_exists = True
	except ImportError:
		pass
	return _is_exists	

def is_in_frozen_state():
	if hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'):
		global IN_FROZEN_STATE
		IN_FROZEN_STATE = True
		return sys._MEIPASS
	return None

def get_app_title(instance_num):
	app_tile = 'iCOM for Windows'
	if os.name.upper() != 'NT':
		app_tile = 'iCOM for %s'%os.name
	if instance_num > 0:
		app_tile = '%s (%d)'%(app_tile,instance_num)
	return app_tile

def get_instance_num():
	instance_num = 1
	return instance_num

frozen_dir_clean = False
frozen_dirs_list = []
import shutil
def get_frozen_tem_dir_prefix(cur_tmp_dir):
	base_name = os.path.basename(cur_tmp_dir)
	_prefix = ''.join([_ for _ in base_name if not _.isdigit()])
	return _prefix

def get_forzen_dirs():
	frozen_dir = is_in_frozen_state()
	if frozen_dir:
		frozen_parent_dir = os.path.abspath(os.path.join(frozen_dir,'..'))
		frozen_dir = frozen_dir[0:-1] if frozen_dir[-1] == os.sep else frozen_dir
		frozen_prefix = get_frozen_tem_dir_prefix(frozen_dir)
		return frozen_dir,frozen_parent_dir,frozen_prefix
	return None,None,None

def clean_frozen_tmp_dir(cur_tmp_dir,frozen_parent_dir,frozen_prefix,cur_exe):
	global frozen_dir_clean
	global frozen_dirs_list
	
	if frozen_dir_clean is True:
		return
	
	try:
		if not frozen_dirs_list:
			dir_list = os.listdir(frozen_parent_dir)
			frozen_dirs_list = [os.path.join(frozen_parent_dir,x) for x in dir_list if x != cur_tmp_dir and x.startswith(frozen_prefix) ]
		if frozen_dirs_list:
			st_time_sec = os.stat(frozen_dirs_list[-1]).st_ctime
			today = datetime.today()
			st_time = datetime.fromtimestamp(st_time_sec)
			pass_time = today - st_time 
			
			cur_del_dir = frozen_dirs_list[-1]
			del frozen_dirs_list[-1]
			if not frozen_dirs_list:
				frozen_dir_clean = True
			
			if pass_time.days >= 3 and os.path.exists(os.path.join(cur_del_dir,'%s.manifest'%cur_exe)):
				os.remove(os.path.join(cur_del_dir,'_multiprocessing.pyd'))
				os.remove(os.path.join(cur_del_dir,'_ctypes.pyd'))
				shutil.rmtree(cur_del_dir)
			
	except Exception as e:
		print ('clean tmp file err:%s\n'%e)
		pass
	return

class win_gui_Queue(Queue):
	__SAMPLE_SIZE = 4
	__MAX_MSG_RATE_THREDHOLD = 80
	__sync_flow_ctrl_count = 0
	__flow_ctrl_interger = 0
	__flow_ctrl_remainder = 0
	__msg_count = 0
	__real_proc_data_msg_count = 0
	__msg_reminder_count = 0
	__data_queue_msg_count = 0
	__nodata_timeout_count = 0
	sync_ctrl_Q = None
	__send_lock = dummyLock()
	def __init__(self,maxsize=0):
		Queue.__init__(self,maxsize,ctx=multiprocessing)
		self.__timer_ctrl_func = None
		self._flow_ctrl = icom_flow_ctrl.flow_ctrl(current_thread().ident)
		self._win_msg = None
		self.__buffer_msg = []
		self._flow_ctrl.set_timer_req_function(self.req_timer_ctrl_Q_cmd)
		self._flow_ctrl.set_flow_ctrl_req_function(self.req_flow_ctrl_Q_cmd)
		self._flow_ctrl.set_enable(True)
	def set_win_pid(self,win_pid):
		self._win_msg = None
	def set_timer_ctrl_function(self,timer_ctrl_func):
		self.__timer_ctrl_func = timer_ctrl_func
	def req_timer_ctrl_Q_cmd(self,cmd,timer_id,timer_len):
		if self.__timer_ctrl_func:
			self.__timer_ctrl_func(cmd,timer_id,timer_len)
	def req_flow_ctrl_Q_cmd(self,cmd,ctrl_msg_count):
		self.flow_ctrl(ctrl_msg_count)
	def set_sync_ctrl_Q(self,sync_ctrl_Q):
		win_gui_Queue.sync_ctrl_Q = sync_ctrl_Q
		win_gui_Queue.__sync_flow_ctrl_count = win_gui_Queue.__SAMPLE_SIZE
		win_gui_Queue.__msg_count = 0
		win_gui_Queue.__msg_reminder_count = 0
	def flow_ctrl(self,msg_count):
		#collect and group data msg count(unit 1/4), 6 means group 6/4(1.5) packet and send a sync ctrl message. <=4 means do not group data message.
		#win_gui_Queue.__send_lock.acquire()
		if msg_count > 4:
			interger = msg_count//win_gui_Queue.__SAMPLE_SIZE
			reminder = msg_count%win_gui_Queue.__SAMPLE_SIZE
			if reminder > 0:
				win_gui_Queue.__flow_ctrl_interger = interger + 1
				new_reminder = win_gui_Queue.__SAMPLE_SIZE - reminder
				win_gui_Queue.__flow_ctrl_remainder =  (win_gui_Queue.__flow_ctrl_interger * msg_count + reminder//2)//new_reminder
			else:
				win_gui_Queue.__flow_ctrl_interger  = interger
				win_gui_Queue.__flow_ctrl_remainder = 0
			win_gui_Queue.__sync_flow_ctrl_count = msg_count #enable flow ctrl now
			print ('flow-ctrl set:%d,%d,%d,%d'%(msg_count,win_gui_Queue.__flow_ctrl_interger,win_gui_Queue.__flow_ctrl_remainder,win_gui_Queue.__msg_count))
		else:
			win_gui_Queue.__sync_flow_ctrl_count = win_gui_Queue.__SAMPLE_SIZE
			win_gui_Queue.__flow_ctrl_interger  = 0
			win_gui_Queue.__flow_ctrl_remainder =  0
			print ('flow-ctrl set',msg_count)
		cur_msg_count = win_gui_Queue.__msg_count
		#win_gui_Queue.__send_lock.release()
		#self.do_send_ctrl_msg(ICOM_CTRL_MSG.ID_FLOW_CTRL_CNF,msg_count,cur_msg_count)
		self._flow_ctrl.process_flow_ctrl(ICOM_CTRL_MSG.ID_FLOW_CTRL_CNF, msg_count,cur_msg_count, 0, 0)
	def get_flow_ctrl_info(self):
		return win_gui_Queue.__sync_flow_ctrl_count,win_gui_Queue.__flow_ctrl_interger,win_gui_Queue.__flow_ctrl_remainder
	def do_send_ctrl_msg(self,msg_int_type,msg_int_param1=None,msg_int_param2=None,msg_int_param3=None,msg_int_param4=None):
		if not win_gui_Queue.sync_ctrl_Q:
			return
		if win_gui_Queue.sync_ctrl_Q.full():
			print('self.sync_ctrl_Q full full full')
			return
		
		msg_para_list = (msg_int_type,msg_int_param1)
		if msg_int_param4:
			msg_para_list = (msg_int_type,msg_int_param1,msg_int_param2,msg_int_param3,msg_int_param4)
		elif msg_int_param3:
			msg_int_param4 = 0
			msg_para_list = (msg_int_type,msg_int_param1,msg_int_param2,msg_int_param3)
		elif msg_int_param2:
			msg_int_param3 = msg_int_param4 = 0
			msg_para_list = (msg_int_type,msg_int_param1,msg_int_param2)
		elif msg_int_param1:
			msg_int_param2 = msg_int_param3 = msg_int_param4 = 0
		else:
			msg_int_param1 = msg_int_param2 = msg_int_param3 = msg_int_param4 = 0
			msg_para_list = (msg_int_type,)
		
		win_gui_Queue.__send_lock.acquire()
		data_queue_msg_count = self.__data_queue_msg_count
		if msg_int_type == ICOM_CTRL_MSG.ID_TIMER_TIMEOUT:
			win_gui_Queue.__real_proc_data_msg_count = 0
		else:
			win_gui_Queue.__real_proc_data_msg_count += 1
		need_continue_proc = self._flow_ctrl.process_flow_ctrl(msg_int_type, msg_int_param1, msg_int_param2, msg_int_param3, msg_int_param4)
		win_gui_Queue.__send_lock.release()
		
		if need_continue_proc is False:
			#print ('nd',msg_int_type)
			return
		if data_queue_msg_count <= 0 and msg_int_type == ICOM_CTRL_MSG.ID_SEND_DATA_CNF_OK:
			#print ('cd')
			return
		if msg_int_type == ICOM_CTRL_MSG.ID_PROC_QUIT_MSG or msg_int_type == ICOM_CTRL_MSG.ID_TIMER_TIMEOUT:
			if not self._win_msg or self._win_msg.send_sync_msg(msg_para_list) is False:
				return win_gui_Queue.sync_ctrl_Q.put(msg_para_list)
		else:
			return win_gui_Queue.sync_ctrl_Q.put(msg_para_list)
	def send_data_sync_msg(self,msg_obj=None,msg_type=None,force_sync=None):
		need_send_ctrl_msg = False
		win_gui_Queue.__send_lock.acquire()
		win_gui_Queue.__msg_count += 1
		win_gui_Queue.__msg_reminder_count += 1
		data_msg_cnt = win_gui_Queue.__sync_flow_ctrl_count
		
		if force_sync is True:
			need_send_ctrl_msg = True
			data_msg_cnt = (win_gui_Queue.__msg_count + win_gui_Queue.__msg_reminder_count)*win_gui_Queue.__SAMPLE_SIZE//2
			win_gui_Queue.__msg_count = 0
			win_gui_Queue.__msg_reminder_count = 0
		elif win_gui_Queue.__msg_count >= win_gui_Queue.__flow_ctrl_interger:
			need_send_ctrl_msg = True
			win_gui_Queue.__msg_count = 0
		elif win_gui_Queue.__msg_reminder_count >= win_gui_Queue.__flow_ctrl_remainder > win_gui_Queue.__flow_ctrl_interger:
			need_send_ctrl_msg = True
			win_gui_Queue.__msg_reminder_count = 0
			
		if msg_obj:
			self.__data_queue_msg_count += 1
			if self.__buffer_msg:
				self.__buffer_msg.append(msg_obj)
			elif win_gui_Queue.__sync_flow_ctrl_count >= win_gui_Queue.__SAMPLE_SIZE *5:
				self.__buffer_msg.append(msg_obj)
			else:
				Queue.put(self,msg_obj)
				
		if need_send_ctrl_msg is True:
			if self.__buffer_msg:
				Queue.put(self,self.__buffer_msg)
				self.__buffer_msg = []
			self.__data_queue_msg_count = 0
		elif len(self.__buffer_msg) > 3:
			Queue.put(self,self.__buffer_msg)
			self.__buffer_msg = []
		win_gui_Queue.__send_lock.release()
		if need_send_ctrl_msg is True:
			self.do_send_ctrl_msg(msg_type if msg_type else ICOM_CTRL_MSG.ID_PROC_DATA_MSG,data_msg_cnt)
			
	def __put(self, obj, block=True, timeout=None):
		if win_gui_Queue.__sync_flow_ctrl_count <= win_gui_Queue.__SAMPLE_SIZE:
			Queue.put(self,obj, block, timeout)
			if win_gui_Queue.__real_proc_data_msg_count > win_gui_Queue.__MAX_MSG_RATE_THREDHOLD:
				self.flow_ctrl(win_gui_Queue.__real_proc_data_msg_count*win_gui_Queue.__SAMPLE_SIZE//(win_gui_Queue.__MAX_MSG_RATE_THREDHOLD))
			return self.do_send_ctrl_msg(ICOM_CTRL_MSG.ID_PROC_DATA_MSG, win_gui_Queue.__SAMPLE_SIZE)
		
		self.send_data_sync_msg(obj)
	def put(self, obj, block=True, timeout=None):
		self.__put(obj, block, timeout)
	def do_send_quit_msg(self):
		self.do_send_ctrl_msg(ICOM_CTRL_MSG.ID_PROC_QUIT_MSG)
	def do_sync(self):
		self.send_data_sync_msg(None,ICOM_CTRL_MSG.ID_FORCE_SYNC_MSG,True)
	def do_timer_out(self,timer_id,timer_len):
		return self.do_send_ctrl_msg(ICOM_CTRL_MSG.ID_TIMER_TIMEOUT,timer_id,timer_len)
	def do_cmd_cnf(self,cmd_type, port_name, result_code, result_str=None):
		if result_code == 0 and (cmd_type == "SI" or cmd_type == "S"):
			self.send_data_sync_msg(None,ICOM_CTRL_MSG.ID_SEND_DATA_CNF_OK)
		else:
			self.__put(("C",cmd_type,port_name,result_code,result_str))
	def put_nowait(self, obj):
		self.send_data_sync_msg(obj)
	def set_app_title(self,app_title):
		pass
	
def icom_main(argv):
	global g_cur_instance_num
	g_cur_instance_num = cur_instance_num = get_instance_num()
	win_title = get_app_title(g_cur_instance_num)
	process_work = None
	process_tray = None
	pro_status = multiprocessing.Array('i', [0 for i in range(8)])
	current_process = multiprocessing.current_process()
	print ('current_process',current_process.pid,current_process.name)
	ports_ctrl_Q = multiprocessing.Queue()
	tray_ctrl_Q = multiprocessing.Queue(maxsize=1)
	gui_sync_ctrl_Q = multiprocessing.Queue()
	gui_data_Q = win_gui_Queue()
	gui_data_Q.set_sync_ctrl_Q(gui_sync_ctrl_Q)
	manager_Q = multiprocessing.Queue()
	netsrv_ctrl_Q = None
	if is_module_exists('ICOM_netsrv'):
		netsrv_ctrl_Q = multiprocessing.Queue()
	
	__stdout = StdoutQueue()
	
	process_netsrv = None
	process_gui = multiprocessing.Process(target=gui_process,name='GUI',
							args=('main-gui',cur_instance_num,win_title,manager_Q,ports_ctrl_Q,tray_ctrl_Q,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status,__stdout))
	process_gui.start()
	gui_data_Q.set_win_pid(process_gui.pid)
	gui_data_Q.set_timer_ctrl_function(lambda cmd,timer_id,timer_len:ports_ctrl_Q.put((cmd,timer_id,timer_len)))
	#process_tray = dummyProcess(target=sys_tray_process,name='TRAY', args=('sys-tray',cur_instance_num,win_title,manager_Q,tray_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status))
	process_work = dummyProcess(target=work_ports_process,name='PORTS', args=('work-ports',cur_instance_num,win_title,manager_Q,ports_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q))
	
	if netsrv_ctrl_Q:
		process_netsrv = dummyProcess(target=netsrv_process,name='NETSRV', args=('net-srv',cur_instance_num,win_title,netsrv_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status))
	
	print ('start_process')
	#process_tray.setDaemon(True)
	#process_tray.start()
	process_work.setDaemon(True)
	process_work.start()
	#if process_netsrv:
	#	process_netsrv.setDaemon(True)
	#	process_netsrv.start()
	#current_process.daemon = True
	
	open_file_log()
	if is_in_frozen_state():
		sys.stdout = __stdout
		sys.stderr = __stdout
	
	print ('gui',process_gui.pid)
	#print ('tray',process_tray.pid)
	#print ('ports',process_work.pid)
	#if process_netsrv:
	#	print ('netsrv',process_netsrv.pid)
	
	frozen_dir,frozen_parent_dir,frozen_prefix = get_forzen_dirs()
	def tray_periel_callback(lparam, loop_count):
		cur_exe = os.path.basename(argv[0] if len(argv) > 0 else 'ICOM.exe')
		
		if not process_gui.is_alive() or 0 != pro_status[0]:
			send_quit_message_to_process(tray_ctrl_Q)
			return 0
		
		try:
			#delay 3 sec to startup netsrv process
			if NET_SRV_PROCESS_DELAY_START == loop_count and  isinstance(process_netsrv,(multiprocessing.Process,dummyProcess)):
				print ('process_netsrv start')
				process_netsrv.setDaemon(True)
				process_netsrv.start()
				#print ('netsrv',process_netsrv.pid)
			
			#print ('active_children',multiprocessing.active_children())
			#print ('process_work need restart',ports_ctrl_Q.__dict__)
			if not isinstance(process_work,(multiprocessing.Process,dummyProcess)) or not process_work.is_alive():
				print ('process_work quit:%d'%loop_count)
				
			if (NET_SRV_PROCESS_DELAY_START < loop_count) and process_netsrv and (not isinstance(process_netsrv,(multiprocessing.Process,dummyProcess)) or not process_netsrv.is_alive()):
				print ('process_netsrv quit:%d'%loop_count)
				
			if frozen_dir and cur_instance_num == 0:
				clean_frozen_tmp_dir(frozen_dir,frozen_parent_dir,frozen_prefix,cur_exe)
			
			record_file_log(__stdout,pro_status)
			
			if loop_count % 10 == 0:
				record_file_log_flush()
			#loop_count = loop_count + 1 if loop_count < 30000 else NET_SRV_PROCESS_DELAY_START + 1
		except Exception as e:
			print ('check exception %s'%e)
			pass
		return loop_count + 1 if loop_count < 30000 else NET_SRV_PROCESS_DELAY_START + 1
	
	#sys_tray_process('sys-tray',cur_instance_num,win_title,manager_Q,tray_ctrl_Q,gui_sync_ctrl_Q,gui_data_Q,pro_status,tray_periel_callback)
	
	try:
		gui_exit_code = process_gui.exitcode
		print ('process_gui.exitcode',gui_exit_code)
		process_gui.join(timeout = 3)
		print ('process_gui.ok')

		if process_work and isinstance(process_work,(multiprocessing.Process,dummyProcess)):
			if process_work.is_alive() and hasattr(process_tray,'terminate'):
				process_work.terminate()
			print ('process_work.exitcode',process_work.exitcode)
			process_work.join(timeout = 3)
		if process_netsrv and isinstance(process_netsrv,(multiprocessing.Process,dummyProcess)) and hasattr(process_tray,'terminate'):
			process_netsrv.terminate()
			print ('process_netsrv.exitcode',process_netsrv.exitcode)
			process_netsrv.join(timeout = 3)
	except Exception as e:
		print ('terminate exception %s'%e)
		pass
	print ('process share status %s'%pro_status[:])
	
	record_file_log(__stdout,pro_status)
	print ('record log.ok')
	close_file_log(pro_status)
	print ('all quit.ok')
	
	return 0

