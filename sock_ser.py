from threading import Thread
from select import select 
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET,SO_REUSEADDR
try:
	from queue import Queue
except:
	from Queue import Queue
	
from ser import ports_ops

class extend_socket(socket):
	test_timeout = 0.001
	block_read_time = 10
	max_onetime_readlen = 2048
	def inWaiting(self):
		sockets_fds = [self]
		readable, writable, exceptional = select(sockets_fds, [], sockets_fds, extend_socket.test_timeout)
		return  2048 if readable else 0
	def writable(self):
		sockets_fds = [self]
		readable, writable, exceptional = select([], sockets_fds, sockets_fds, extend_socket.test_timeout)
		return  1 if writable else 0
	def write(self,buf):
		return self.send(buf)
	def read(self,rcv_len=None):
		sockets_fds = [self]
		readable, writable, exceptional = select(sockets_fds, [], sockets_fds, extend_socket.block_read_time)
		if readable:
			if self.family == SOCK_STREAM:
				rcv_data = self.recv(rcv_len if rcv_len else extend_socket.max_onetime_readlen)
				return rcv_data if rcv_data else None
			else:
				rcv_data = self.recv(extend_socket.max_onetime_readlen)
				return rcv_data if rcv_data else None
		return b''
	def read_all(self):
		if self.inWaiting():
			return self.recv(extend_socket.max_onetime_readlen)
		return b''
	
class sock_ports_ops(ports_ops):
	def __init__(self):
		ports_ops.__init__(self)
		self.__sock_thread_id = None
	
	def _parse_port_name(self,port_name):
		'''port_name format is local_addr@dst_addr:dst_port like "192.168.1.100@192.168.1:3000" '''
		is_net_port = True
		net_type = 'tcp'
		net_dst_addr = "192.168.1.1"
		net_dst_port = 3000
		net_local_addr = "192.168.1.100"
		net_local_port = 0
		
		if port_name.startswith(r'TELNET://')  or port_name.startswith(r'telnet://'):
			port_name = port_name[9:]
			net_type = 'telnet'
		elif port_name.startswith(r'tcp://')  or port_name.startswith(r'TCP://'):
			port_name = port_name[6:]
		elif port_name.startswith(r'udp://') or port_name.startswith(r'UDP://'):
			port_name = port_name[6:]
			net_type = 'udp'
			
		for ch in port_name:
			if ch != '.' and ch != ':' and ch != '@' and not ch.isdigit():
				is_net_port = False
				break
			
		if is_net_port is True:
			net_info = port_name.split('@')
			if len(net_info) == 2:
				net_local_addr = net_info[0]
				src_info = net_info[0].split(':')
				net_local_addr = src_info[0]
				if len(src_info) == 2:
					net_local_port = int(src_info[1])
				dst_info = net_info[1].split(':')
				if len(dst_info) == 2:
					net_dst_addr = dst_info[0]
					net_dst_port = int(dst_info[1])
				else:
					is_net_port = False
			else:
				is_net_port = False
			
		return (is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr,net_local_port)
		
	def open_port(self,port_name,rd_callback=None,serial_settings=None):
		#print ('sock_ser.start_port',port_name)
		self._create_common_thread_and_Q()
		
		is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr,net_local_port = self._parse_port_name(port_name)
		self.__is_sock_port = is_net_port
		if is_net_port is not True:
			return ports_ops.open_port(self, port_name, rd_callback, serial_settings)
		
		print ('sock_ser',is_net_port,net_type,net_dst_addr,net_dst_port,net_local_addr)
		
		if net_type == 'udp':
			ser = extend_socket(AF_INET,SOCK_DGRAM)
		else:
			ser = extend_socket(AF_INET,SOCK_STREAM)
		ser.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		ser.bind((net_local_addr,net_local_port))
		ser.settimeout(3)
		
		#if net_dst_addr.startswith('224'):
		#ser.setsockopt(SOL_IP, IP_ADD_MEMBERSHIP, (multicast_ip,multicast_port))
		ser.connect((net_dst_addr,net_dst_port))
		ser.setblocking(False) #set to noneblocking mode
		read_thread = Thread(target=self.port_thread_read,args=(port_name,))
		read_thread.setDaemon(True)
		self.set_args(port_name, {'handle':ser,'fd':ser,'name':port_name,'net':is_net_port,'type':net_type,'exception':0,'read_callback':rd_callback,'thread':read_thread,'quit':False})
		
		return (port_name,'')

if __name__ == '__main__':
	import sys
	import time
	p = sock_ports_ops()
	port_name = '10.146.95.1@10.146.95.1:10086'
	baudrate = None
	if len(sys.argv) > 1:
		port_name = sys.argv[1]
	if len(sys.argv) > 2:
		baudrate = int(sys.argv[2])
	def report_callback(port_name,ser,desc):
		print (desc)
	name,rate = p.open_port(port_name,report_callback,baudrate)
	p.start_port(port_name)
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