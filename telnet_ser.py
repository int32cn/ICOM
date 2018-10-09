from threading import Thread
from select import select 
try:
	from queue import Queue
except:
	from Queue import Queue

from sock_ser import sock_ports_ops
from telnetlib import Telnet

class extend_Telnet(Telnet):
	block_read_time = 30
	def inWaiting(self):
		return  1 if self.sock_avail() else 0
	def read(self,rcv_len=1):
		sockets_fds = [self.sock]
		readable, writable, exceptional = select(sockets_fds, [], sockets_fds, extend_Telnet.block_read_time)
		if readable:
			return self.read_some()
		return b''
	def read_all(self):
		return self.read_very_eager()
	#def cancel_read(self):
	#	return self.sock.cancel_read()
		
class telnet_ports_ops(sock_ports_ops):
	def __init__(self):
		sock_ports_ops.__init__(self)
		self.__telnet = None
		self.__is_telnet = False
	def open_port(self,port_name,rd_callback=None,serial_settings=None):
		self._create_common_thread_and_Q()
		is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr,net_local_port = self._parse_port_name(port_name)
		
		if serial_settings is not None and 'log' in serial_settings and isinstance(serial_settings['log'],str):
			self.open_log_file(port_name,serial_settings['log'])
		#print (is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr)
		if net_type != 'telnet':
			self.__is_telnet = False
			return sock_ports_ops.open_port(self, port_name, rd_callback, serial_settings)
			
		self.__is_telnet = True
		
		self.__telnet = extend_Telnet(net_dst_addr,net_dst_port, timeout=10)
		read_thread = Thread(target=self.port_thread_read,args=(port_name,))
		read_thread.setDaemon(True)
		self.set_args(port_name, {'handle':self.__telnet,'name':port_name,'net':is_net_port,'type':net_type,'exception':0,'read_callback':rd_callback,'thread':read_thread,'quit':False})
		
		return (port_name,'')


if __name__ == '__main__':
	import sys
	import time
	p = telnet_ports_ops()
	port_name = 'telnet://192.168.1.50:0@192.168.1.50:3000'
	baudrate = None
	if len(sys.argv) > 1:
		port_name = sys.argv[1]
	if len(sys.argv) > 2:
		baudrate = int(sys.argv[2])
	def report_callback(port_name,ser,desc):
		print (desc)
	name,rate = p.open_port(port_name,report_callback,baudrate)
	print (name,rate)
	p.start_port(port_name)
	
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