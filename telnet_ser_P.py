#from threading import Thread
#from Queue import Queue
from sock_ser import sock_ports_ops
from multiprocessing import Process,Queue

class telnet_ports_ops(sock_ports_ops):
	def __init__(self):
		sock_ports_ops.__init__(self)
		self.__telnet_thread_id = None
		self.__telnet = None
	def telnet_process_sock(self,xargs):
		exception_times = 0
		timeout = 3
		print ('process start',self,xargs)
		need_quit = False
		telnet_port_name = None
		while 1:print('do')
		args_all = self.get_args()
		print ('process start2')
		for port_name,val in args_all.items():
			if port_name.upper().startswith('TELNET://'):
				telnet_port_name = port_name
		print ('process start3',self.__telnet,telnet_port_name)
		while 1:print('do')
		while self.__telnet is not None and need_quit is False and telnet_port_name is not None:
			try:
				print ('process start in')
				out_data,out_len = self.get_out_data(telnet_port_name)
				print ('process out_data',out_data)
				if out_len > 0:
					self.__telnet.write(out_data)
				print ('process startx',out_len)
				r = self.__telnet.read_very_eager()
				print ('process startr',r)
				if r:
					self.port_readcallback(telnet_port_name, self.__telnet, r)
				
				exception_times = 0
			except Exception as e:
				exception_times += 1
				self.error_callback(telnet_port_name, None, 'unknown Excpetion %s'%e)
				print ('error hanppens in ser %s'%e)
				need_quit = True
				pass
			
			if exception_times > 2:
				print ('exception_times cause quit')
				break
				
			port_name_args = self.get_args(telnet_port_name)
			if port_name_args is None:
				print ('%s port_name_args is None cause quit'%telnet_port_name)
				need_quit = True
				break
			elif 'quit' in port_name_args and port_name_args['quit'] is True:
				print ('%s port_name_args["quit"] cause quit'%telnet_port_name)
				need_quit = True
				break
		
		self.__telnet_thread_id = None
	def do_abcd(self,a):
		while 1:
			print ('run',a)
	def start_port(self,port_name,rd_callback=None,serial_settings=None):
		is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr,net_local_port = self._parse_port_name(port_name)
		
		#print (is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr)
		#if net_type != 'telnet':
		#	return sock_ports_ops.start_port(self, port_name, rd_callback, serial_settings)
		t = Process(target=self.do_abcd,args=(123,))
		from telnetlib import Telnet
		#self.__telnet = Telnet(net_dst_addr,net_dst_port, timeout=8)
		#self.set_args(port_name, {'Q':Queue(),'net':is_net_port,'read_callback':rd_callback,'quit':False})
		print ('begin start process')
		#t = Process(target=self.do_abcd,args=(123,))
		#t.setDaemon(True)
		self.__telnet_thread_id = t
		print ('begin run process')
		t.start()
		print ('have process run')
		#self.send_notify()
		return (port_name,'')
	

if __name__ == '__main__':
	import sys
	import time
	p = telnet_ports_ops()
	port_name = 'telnet://10.146.95.1@10.146.95.1:23'
	baudrate = None
	if len(sys.argv) > 1:
		port_name = sys.argv[1]
	if len(sys.argv) > 2:
		baudrate = int(sys.argv[2])
	def report_callback(port_name,ser,desc):
		print (desc)
	name,rate = p.start_port(port_name,report_callback,baudrate)
	print (name,rate)
	start_time = time.time()
	while 1:
		try:
			send_str = raw_input()
		except:
			break
		send_str = send_str.decode('utf-8')
		x = p.send_data(port_name,send_str+'\r',1)
		if None is x:
			print ('wait')
			time.sleep(1)
		
	time.sleep(0.5)
	p.stop_port(port_name)