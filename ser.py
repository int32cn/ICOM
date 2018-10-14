from threading import Thread, RLock, Condition
from serial import Serial
from datetime import datetime
import time
import traceback
from modem import ZMODEM

import as_event_loop
import asyncio
from icom_ctrl_msg_id import *
from comm_work_data_proc import CommWorkDataPro

from collections import deque

import io
try:
    file_types = (file, io.IOBase)
except NameError:
    file_types = (io.IOBase,)


class ports_ops(CommWorkDataPro):
	MAX_INTERVAL = 2.0
	MIN_INTERVAL = 0.005
	THREDHOLD_INTERVAL = 0.8
	DEFAULT_FLOWCTRL_TIMER_LEN = 1
	def __init__(self):
		super().__init__()
		self.__args = {}
		self._save_log_file = {}
		self._save_log_file_name = {}
		self.__args_lock = RLock()
		self.con_sig = Condition()
		self.__sync_callback = None
		self.__need_sync_data = False
		self.__stop_and_destroy = False
		self.__zmodem_send_flag = False
		self.__zmodem_recv_deque = deque()
		self.__zmodem_port_name = None
		self.__event = as_event_loop.Event()
		self._create_common_thread_and_Q()
	def get_event_and_loop(self):
		return self.__event,self._event_loop_thread
	def port_thread_read(self, *args, **kwds):
		print ('args:',args,kwds)
		port_name = args[0] if args else None
		self.set_sub_args(port_name,'reading', True)
		while self.__stop_and_destroy is not True:
			try:
				ser_handle = self.get_sub_args(port_name,'handle')
				if not ser_handle or self.get_sub_args(port_name,'quit') is True:
					if hasattr(ser_handle,'cancel_write'):
						ser_handle.cancel_write()
					break
				
				if hasattr(ser_handle, 'read'):
					read_data = ser_handle.read(1)
					if read_data:
						if hasattr(ser_handle, 'read_all'):
							read_data += ser_handle.read_all()
					if read_data:
						self.port_readcallback(port_name, ser_handle, read_data)
					elif read_data is None:#means EOF
						raise Exception('get None,pear may close')
					if self._show_timestamp is False and self._flow_ctrl_count > 20:
						time.sleep(0.02)
				else:
					print('read not support sleep')
					time.sleep(1)
			except Exception as e:
				try:
					print ('exception read in ',port_name,e)
					#print (traceback.print_exc())
					exception_times = self.get_sub_args(port_name,'exception')
					if isinstance(exception_times,int):
						#print ('set exception_times',exception_times)
						self.set_sub_args(port_name,'exception',exception_times+1)
						self.error_callback(port_name, None, 'exception %s read times:%d'%(e,exception_times))
						if exception_times > 3:
							break
				except Exception as e:
					print ('excep re-ocer in %s:%s'%(port_name,e))
					pass
				pass
		if self.get_sub_args(port_name,'reading'):
			self.set_sub_args(port_name,'reading',False)
		self.close_log_file(port_name)
		self.__send_internal_ctrl_data(port_name,b'')#try trigle to quit
		print ('thread quit',args)
		
	def __check_process_quit(self):
		port_name_map_ori = self.get_args()
		have_open_ports = False
		for port_name,port_attr in port_name_map_ori.items():
			if 'handle' not in port_attr:
				self.set_args(port_name, None)
				continue
			ser_handle = port_attr['handle']
			if self.get_sub_args(port_name,'quit') is True:
				if hasattr(ser_handle,'cancel_read') and self.get_sub_args(port_name,'reading') is True:
					ser_handle.cancel_read()
				if ser_handle:
					ser_handle.close()
				self.set_args(port_name, None)
			elif port_attr['exception'] > 3:
				self.error_callback(port_name, ser_handle, 'exception, close now')
				if hasattr(ser_handle,'cancel_read') and self.get_sub_args(port_name,'reading') is True:
					ser_handle.cancel_read()
				if ser_handle:
					ser_handle.close()
				self.set_args(port_name, None)
			elif hasattr(ser_handle, 'write'):
				have_open_ports = True
		return have_open_ports
	@asyncio.coroutine
	def port_thread_one(self):
		while self.__stop_and_destroy is not True:
			have_open_ports = True
			port_name = None
			
			try:
				have_open_ports = self.__check_process_quit()
				out_data,port_name,ctrl_flag = yield from self._event_loop_thread.msg_Q.get()
				if out_data and ctrl_flag is None:
					out_data_len = len(out_data)
					ser_handle = self.get_sub_args(port_name,'handle')
					write_timenow = datetime.now() if self._local_echo and self._show_timestamp else None
					send_len = ser_handle.write(out_data) if ser_handle else 0
					if send_len and send_len < out_data_len:
						raise Exception('send data error: %d < %d'%(send_len,out_data_len))
					if self._local_echo:
						self.port_echocallback(port_name, write_timenow, out_data)
				have_open_ports = self.__check_process_quit()
			except Exception as e:
				try:
					print ('exception in thread_one ',port_name,e)
					print (traceback.print_exc())
					exception_times = self.get_sub_args(port_name,'exception')
					if isinstance(exception_times,int):
						print ('set exception_times',exception_times)
						self.set_sub_args(port_name,'exception',exception_times+1)
						self.error_callback(port_name, None, 'exception write times:%d'%exception_times)
				except Exception as e:
					print ('excep re-ocer in %s:%s'%(port_name,e))
					pass
				pass
			
			#if not have_open_ports:
			#	print ('have ports open',have_open_ports)
	def error_callback(self,port_name,ser_handle,err):
		callback = self.get_sub_args(port_name,'err_callback')
		if callback is not None:
			callback(port_name, self.__args[port_name], 'error hanppens: %s'%err)
			
	def zmodem_info_callback(self, data):
		try:
			if not isinstance(data, bytes):
				data = bytes(data, 'utf-8')
			port_name = self.__zmodem_port_name
			timestamp_now = datetime.now() if self._show_timestamp else None
			self.port_echocallback(port_name,timestamp_now,data)
		except Exception as e:
			pass
	def port_readcallback(self,port_name,ser_handle,data):
		#print ser_handle.port,data
		if self.__zmodem_send_flag is True and self.__zmodem_port_name == port_name:
			for ch in data:
				self.__zmodem_recv_deque.append(ch)
			return
		callback = self.get_sub_args(port_name,'read_callback')
		t_str = None
		if self._show_timestamp:
			timenow = datetime.now()
			t_bytes = b'[%02d:%02d:%02d.%06d]'%(timenow.hour, timenow.minute, timenow.second, timenow.microsecond)
			t_str = '[%02d:%02d:%02d.%06d]'%(timenow.hour, timenow.minute, timenow.second, timenow.microsecond)
			self.record_log_to_file(port_name,t_bytes)
		
		self.record_log_to_file(port_name,data)
		if callback is not None:
			callback(port_name,self.__args[port_name],(data,t_str,0))
		
	def port_echocallback(self,port_name,timenow,data):
		#print ser_handle.port,data
		callback = self.get_sub_args(port_name,'read_callback')
		t_str = None
		if self._show_timestamp and timenow is not None:
			t_bytes = b'[%02d:%02d:%02d.%06d]'%(timenow.hour, timenow.minute, timenow.second, timenow.microsecond)
			t_str = '[%02d:%02d:%02d.%06d]'%(timenow.hour, timenow.minute, timenow.second, timenow.microsecond)
			self.record_log_to_file(port_name,t_bytes)
		self.record_log_to_file(port_name,data)
		if callback is not None:
			callback(port_name,self.__args[port_name],(data,t_str,1))
	
	def sync_callback(self,force_keyup=False):
		if self.__sync_callback:
			self.__need_sync_data = False
			self.__sync_callback(force_keyup)
	def send_notify(self):
		self.con_sig.acquire()
		self.con_sig.notifyAll()
		self.con_sig.release()
		
	def set_args(self,arg_name,arg_val):
		self.__args_lock.acquire()
		if arg_name in self.__args and arg_val is None:
			del self.__args[arg_name]
		elif arg_name:
			self.__args[arg_name] = arg_val
		self.__args_lock.release()
		
	def set_sub_args(self,arg_name,sub_arg_key,sub_srg_val):
		self.__args_lock.acquire()
		if arg_name and arg_name in self.__args:
			if sub_arg_key in self.__args[arg_name]:
				self.__args[arg_name][sub_arg_key] = sub_srg_val
			else:
				self.__args[arg_name].setdefault(sub_arg_key,sub_srg_val)
		self.__args_lock.release()
		
	def get_sub_args(self,arg_name,sub_arg_key):
		sub_args = None
		self.__args_lock.acquire()
		if arg_name in self.__args:
			if sub_arg_key in self.__args[arg_name]:
				sub_args = self.__args[arg_name][sub_arg_key]
		self.__args_lock.release()
		return sub_args
		
	def get_args(self,arg_name=None):
		args = None
		self.__args_lock.acquire()
		if arg_name is None:
			args = self.__args.copy()
		elif arg_name in self.__args:
			args = self.__args[arg_name].copy()
		self.__args_lock.release()
		return args
		
	def set_error_callback(self,port_name,err_callback):
		self.set_sub_args(port_name, 'err_callback', err_callback)
	def set_sync_callback(self,sync_callback):
		if sync_callback != self.__sync_callback:
			self.__sync_callback = sync_callback
	
	def _create_common_thread_and_Q(self):
		if not isinstance(self._event_loop_thread, Thread):
			self._event_loop_thread = as_event_loop.EventLoopThread(self.__event,self.port_thread_one)
			self._event_loop_thread.set_callback("timer",self.timer_timeout_proc)
			self._event_loop_thread.setDaemon(True)
	def open_port(self,port_name,rd_callback=None,serial_setting=None):
		stop_try_count = 0
		while self.get_args(port_name) is not None and stop_try_count < 2:
			self.stop_port(port_name)
			time.sleep(1)
			stop_try_count += 1
		print ('start open',port_name,stop_try_count)
		ser = Serial(port_name,timeout=60)
		ser_info = ser.get_settings()
		print ('default ser_info',ser_info)
		#{'parity': 'N', 'baudrate': 9600, 'bytesize': 8, 'xonxoff': False, 'rtscts': False, 'timeout': 10, 
		#'inter_byte_timeout': None, 'stopbits': 1, 'dsrdtr': False, 'write_timeout': None}
		if serial_setting is not None:
			try:
				print ('serial_setting',serial_setting)
				if 'showtime' in serial_setting and isinstance(serial_setting['showtime'],int):
					self._show_timestamp = True if serial_setting['showtime'] > 0 else False
				if 'localecho' in serial_setting and isinstance(serial_setting['localecho'],int):
					self._local_echo = True if serial_setting['localecho'] > 0 else False
				
				if 'baudrate' in serial_setting and serial_setting['baudrate'].isdigit():
					ser_info['baudrate'] = int(serial_setting['baudrate'])
				if 'databit' in serial_setting and serial_setting['databit'].isdigit():
					ser_info['bytesize'] = int(serial_setting['databit'])
				if 'stopbit' in serial_setting and serial_setting['stopbit'].count('.') <= 1:
					split_list = serial_setting['stopbit'].split('.')
					num_list = [n for n in split_list if n.isdigit()]
					if len(split_list) == len(num_list):
						ser_info['stopbits'] = float(serial_setting['stopbit'])
				if 'checkbit' in serial_setting and len(serial_setting['checkbit']) > 0:
					ser_info['parity'] = serial_setting['checkbit'][0]
				#if 'flowctrl' in serial_setting:
				#	ser_info['rtscts'] = serial_setting['flowctrl']
				print ('to apply setting',ser_info)
				ser.apply_settings(ser_info)
			except Exception as e:
				print ("set apply_settings err:%s"%e)
				pass
		
		#ser_info = ser.get_settings()
		print ('port %s setting ok'%port_name)
		read_thread = Thread(target=self.port_thread_read,args=(port_name,))
		read_thread.setDaemon(True)
		self.set_args(port_name, {'handle':ser,'start':False,'name':port_name,'type':'serial','exception':0,'read_callback':rd_callback,'thread':read_thread,'quit':False})
		
		return (port_name,ser_info)
		
	def set_time_interval(self,port_name,time_interval_ms,auto_send):
		if time_interval_ms > 0:
			self._time_interval = time_interval_ms / 1000.0
		else:
			self._time_interval = self.__time_interval_default
		self._auto_send = True if auto_send else False
	def set_timestamp_onoff(self,port_name,show_timestamp):
		self._show_timestamp = show_timestamp
	def set_local_echo(self,port_name,local_echo):
		self._local_echo = local_echo
	def open_log_file(self,port_name,log_name):
		if port_name in self._save_log_file and isinstance(self._save_log_file[port_name],file_types):
			try:
				self._save_log_file[port_name].close()
			except Exception as e:
				print ('open_log_file try close err:%s'%e)
				pass
		self._save_log_file[port_name] = open(log_name,'ab')
		self._save_log_file_name[port_name] = log_name
		
	def flush_log_to_file(self,port_name):
		if port_name in self._save_log_file and isinstance(self._save_log_file[port_name],file_types):
			try:
				self._save_log_file[port_name].flush()
			except Exception as e:
				print ('record_log_to_file err:%s'%e)
				pass
	def open_show_log_file(self,port_name,open_type):
		import os
		try:
			if open_type != 'file' or port_name is None or port_name not in self._save_log_file_name:
				os.startfile(os.path.abspath('log'))
			elif self._save_log_file_name[port_name] is not None and os.path.exists(self._save_log_file_name[port_name]):
				self.flush_log_to_file(port_name)
				os.startfile(self._save_log_file_name[port_name])
			else:
				os.startfile(os.path.abspath('log'))
		except Exception as e:
			pass
	def record_log_to_file(self,port_name,log_msg):
		if port_name in self._save_log_file and isinstance(self._save_log_file[port_name],file_types):
			try:
				self._save_log_file[port_name].write(log_msg)
			except Exception as e:
				print ('record_log_to_file err:%s'%e)
				pass
	def close_log_file(self,port_name):
		if port_name in self._save_log_file:
			if isinstance(self._save_log_file[port_name],file_types):
				try:
					self._save_log_file[port_name].close()
					del self._save_log_file[port_name]
				except Exception as e:
					print ('close_log_file close err:%s'%e)
					pass
			self._save_log_file_name[port_name] = None
		
	def start_port(self,port_name):
		__thread_id = self.get_sub_args(port_name,'thread')
		if not isinstance(__thread_id, Thread):
			raise Exception('serial start_port %s thread_id error'%port_name)
		if not __thread_id.isAlive():
			__thread_id.start()
		
		if not self._event_loop_thread.isAlive():
			self._event_loop_thread.start()
			self.__event.wait() #wait untill the eventloop thread start running
			
		self.start_timer(ICOM_TIMER.ID_FLOW_CTRL, self.DEFAULT_FLOWCTRL_TIMER_LEN)
		#else:
		#	self.send_notify()
	def stop_port(self,port_name):
		if self.get_args(port_name) is not None:
			self.set_sub_args(port_name,'quit',True)
			self.set_sub_args(port_name,'thread',None)
			self.__send_internal_ctrl_data(port_name,b'')#trigle to quit
			print ('stop port in',port_name)
		
	def stop_all_ports(self):
		self.__args_lock.acquire()
		for port_name,port_attr in self.__args.items():
			self.stop_port(port_name)
		self.__args_lock.release()
		
	def stop_and_destrory(self):
		self.__stop_and_destroy = True
		self.stop_all_ports()
		self.send_notify()#re notify
		if self._event_loop_thread:
			self._event_loop_thread.stop()
	def __send_internal_ctrl_data(self,port_name,data):
		ret = None
		if not isinstance(data,bytes):
			data = bytes(data,'utf-8')
		
		if self._event_loop_thread:
			self._event_loop_thread.send_msg((data,port_name,True))
			ret = True
			
		return ret
	def send_file(self,port_name,file_name):
		ret = encode_err = None
		if self.get_sub_args(port_name,'handle') is None:
			return None
		if self.get_sub_args(port_name,'quit') is True:
			return None
		if not self._event_loop_thread:
			return None
		
		with open(file_name,'rb') as f:
			data = f.read(1024)
			while data:
				self._event_loop_thread.send_msg((data,port_name,None))
				data = f.read(1024)
			ret = True
			
		return ret
	def zmodem_io_getc(self,data_len,timeout=0.2):
		ch = b''
		if self.get_sub_args(self.__zmodem_port_name,'handle') is None:
			return b''
		if self.__zmodem_recv_deque:
			return self.__zmodem_recv_deque.popleft()
		elif timeout <= 0.001:
			return b''
			
		timeout_cnt = timeout//0.02
		while timeout_cnt > 0:
			if self.__zmodem_recv_deque:
				ch = self.__zmodem_recv_deque.popleft()
				break
			timeout_cnt -= 1
			time.sleep(0.02)
		return ch
	def zmodem_io_putc(self,data,timeout=0):
		ser_handle = self.get_sub_args(self.__zmodem_port_name,'handle')
		if ser_handle:
			return ser_handle.write(data)
		return -1
	def zmodem_send_thread(self, *args):
		try:
			print(args)
			self.__zmodem_port_name = args[0]
			file_path = args[1]
			if self.__zmodem_recv_deque:
				self.__zmodem_recv_deque.clear()
			cur_zmodem = ZMODEM(self.zmodem_io_getc, self.zmodem_io_putc)
			cur_zmodem.send(file_path, 30, 60, self.zmodem_info_callback)
		except Exception as e:
			print('zmodem send %s fail:%s'%(file_path,e))
			#print (traceback.print_exc())
		self.__zmodem_send_flag = False
		self.__zmodem_port_name = None
		print("zmodem send thread quit")
	def send_zmodem(self,port_name,file_path):
		ret = encode_err = None
		if self.get_sub_args(port_name,'handle') is None:
			return None
		if self.get_sub_args(port_name,'quit') is True:
			return None
		if not self._event_loop_thread:
			return None
		if self.__zmodem_send_flag is True:
			return None
		self.__zmodem_send_flag = True
		zmodem_thread = Thread(target=self.zmodem_send_thread,args=(port_name,file_path,))
		zmodem_thread.setDaemon(True)
		zmodem_thread.start()
		
		return ret
	def send_data(self,port_name,data,data_encoding):
		ret = encode_err = None
		if self.get_sub_args(port_name,'handle') is None:
			return None
		if self.get_sub_args(port_name,'quit') is True:
			return None
		if self.__zmodem_send_flag is True and self.__zmodem_port_name == port_name:
			return False
		if not isinstance(data,bytes):
			try:
				data = bytes(data,data_encoding if data_encoding else 'utf-8')
			except Exception as e:
				encode_err = True
				pass
		if not encode_err and self._event_loop_thread:
			self._event_loop_thread.send_msg((data,port_name,None))
			ret = True
			
		return ret
	

if __name__ == '__main__':
	import sys
	p = ports_ops()
	port_name = 'COM8'
	port_param = {'checkbit': 'None', 'baudrate': '115200', 'flowctrl': '', 'stopbit':'1', 'databit': '8'}
	if len(sys.argv) > 1:
		port_name = sys.argv[1]
	print ('sys.argv',sys.argv)
	def report_callback(port_name,ser,desc):
		print (port_name,desc)
	name,rate = p.open_port(port_name,report_callback,port_param)
	print (name,rate)
	p.start_port(name)
	import time
	start_time = time.time()
	while 1:
		try:
			send_str = input()#+'\r\n'
		except Exception as e:
			print ('break',e)
			break
		#send_str = send_str.decode('utf-8')
		print ('send_str',send_str)#+'\r\n'
		x = p.send_data(port_name,send_str,1)
		if None is x:
			print ('wait')
			time.sleep(1)
		
	time.sleep(0.5)
	p.stop_port(port_name)