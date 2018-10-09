#!/usr/bin/python
# -*- coding= utf-8 -*-

import asyncio
import struct
from socket import inet_aton,getfqdn,gethostname,gethostbyname_ex,AF_INET,SOCK_STREAM, SOL_IP, IP_DROP_MEMBERSHIP,IP_ADD_MEMBERSHIP,INADDR_ANY,IP_MULTICAST_TTL,IP_MULTICAST_LOOP

from as_event_loop import EventLoopThread, Event
from comm_work_data_proc import CommWorkDataPro

@asyncio.coroutine
def new_connection(host, port):
	loop = asyncio.get_event_loop()
	client_transport, client_proto = yield from \
		loop.create_connection(ClientProtocol, host, port)
	return client_transport, client_proto

class ClientProtocol(asyncio.Protocol):
	def connection_made(self, transport):
		print('ClientProtocol')
	def connection_lost(self, transport):
		print('connection_lost')
	def data_received(self, transport):
		print('connection_lost')
	def eof_received(self, transport):
		print('connection_lost')

class ServerProtocol(asyncio.Protocol):
	tcp_callback = None
	udp_callback = None
	connection_made_callback = None
	connection_lost_callback = None
	connection_eof_callback = None
	error_received_callback = None
	def connection_made(self, transport):
		self.transport = transport
		if self.connection_made_callback:
			self.connection_made_callback(transport)
		#self.client_task = asyncio.Task(new_connection(HOST, PORT))
		#self.client_task.add_done_callback(self.client_connect_done)
		#print('connection_made',transport)

	def client_connect_done(self, future):
		client_transport, client_proto = future.result()
		print('client_connect_done',client_transport, client_proto)
	
	def connection_lost(self, transport):
		if self.connection_lost_callback:
			self.connection_lost_callback(transport)
	
	def data_received(self, data):
		if ServerProtocol.tcp_callback:
			ServerProtocol.tcp_callback(self.transport,data)
		if data.startswith(b'ECHO'):
			self.transport.write(data[4:])
		
	def datagram_received(self, data, addr, args=None):
		if ServerProtocol.udp_callback:
			ServerProtocol.udp_callback(addr,self.transport,data)
		if data.startswith(b'ECHO'):
			self.transport.sendto(data[4:], addr)
	def error_received(self,_error):
		if self.error_received_callback:
			self.error_received_callback(self.transport,_error)
	def eof_received(self):
		if self.connection_eof_callback:
			self.connection_eof_callback(self.transport)

class srv_control(CommWorkDataPro):
	def __init__(self,event_loop_thread):
		super().__init__()
		self.__tcp_srv_info = {}
		self.__udp_srv_info = {}
		self.__srv_connections = {}
		self._event_loop_thread = event_loop_thread
		self._callback = {'tcp':None,'udp':None,'udp_cast':None,'tcp_err':None,'udp_err':None,'timer':None}
		ServerProtocol.tcp_callback = self._do_tcp_callback
		ServerProtocol.udp_callback = self._do_udp_callback
		ServerProtocol.connection_made_callback = self._do_connection_made
		ServerProtocol.connection_lost_callback = self._do_connection_lost
		ServerProtocol.connection_eof_callback = self._do_connection_eof
		ServerProtocol.error_received_callback = self._do_connection_error
		self.__srv_timers = {}
		self._event_loop_thread.set_callback("timer",self.timer_timeout_proc)
		
	@asyncio.coroutine
	def _add_tcp_server_task(self,srv_name, host, port):
		srv = yield from self._event_loop_thread.loop.create_server(ServerProtocol, host, port)
		self.__tcp_srv_info[srv_name]['srv'] = srv
	@asyncio.coroutine
	def _add_udp_server_task(self,srv_name, host, port):
		srv = yield from self._event_loop_thread.loop.create_datagram_endpoint(ServerProtocol, local_addr=(host, port))
		self.__udp_srv_info[srv_name]['srv'] = srv[0]
	@asyncio.coroutine
	def _add_multicast_server_task(self,srv_name, host, port, multicast_ip):
		srv = yield from self._event_loop_thread.loop.create_datagram_endpoint(ServerProtocol, local_addr=(host, port))
		self.__udp_srv_info[srv_name]['srv'] = srv[0]
		if not isinstance(multicast_ip,str):
			multicast_ip = multicast_ip.decode()
		srv_sock = srv[0]._sock
		mreq = struct.pack('4sl',inet_aton(multicast_ip),int(INADDR_ANY))
		srv_sock.setsockopt(SOL_IP, IP_MULTICAST_TTL, 2)
		srv_sock.setsockopt(SOL_IP, IP_MULTICAST_LOOP, 0)
		srv_sock.setsockopt(SOL_IP, IP_ADD_MEMBERSHIP, mreq)
			
	def add_tcp_server(self, srv_name, host, port):
		if srv_name in self.__tcp_srv_info:
			return None
		self.__tcp_srv_info[srv_name] = {'host':host, 'port':port, 'srv':None}
		self._event_loop_thread.add_task(self._add_tcp_server_task(srv_name, host, port))
	
	def add_udp_server(self, srv_name, host, port):
		if srv_name in self.__udp_srv_info:
			return None
		self.__udp_srv_info[srv_name] = {'host':host, 'port':port, 'srv':None}
		self._event_loop_thread.add_task(self._add_udp_server_task(srv_name, host, port))
	
	def add_multicast_server(self, srv_name, host, port, multicast_ip):
		if srv_name in self.__udp_srv_info:
			return None
		self.__udp_srv_info[srv_name] = {'host':host, 'port':port, 'srv':None}
		self._event_loop_thread.add_task(self._add_multicast_server_task(srv_name, host, port, multicast_ip))
	
	def start_server(self,srv_type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
		srv_name = '%s-%s:%d'%(srv_type,host,port)
		print ('add server',srv_name)
		if 'tcp' == srv_type:
			self.add_tcp_server(srv_name,host,port)
		elif 'udp' == srv_type:
			self.add_udp_server(srv_name,host,port)
		else:
			self.add_udp_server(srv_name,host,port)
			
		return srv_name
	def stop_server(self,srv_type='tcp',host='0.0.0.0',port=3000,multicast_ip=None):
		srv_name = '%s-%s:%d'%(srv_type,host,port)
		self.del_server(srv_name)
		
	def _del_server(self, _srv_info, srv_name):
		if srv_name in _srv_info and hasattr(_srv_info[srv_name]['srv'],'close'):
			print ('del',srv_name)
			self._event_loop_thread.call_later_safe(_srv_info[srv_name]['srv'].close)
			return True
		return False
	
	def _do_tcp_callback(self,transport,data):
		if 'tcp' in self._callback:
			self._callback['tcp'](transport._sock.getpeername(),transport,data)
			
	def _do_udp_callback(self,addr,transport,data):
		if 'udp' in self._callback:
			self._callback['udp'](addr,transport,data)
	def _do_error_callback(self,transport,_error):
		if transport._sock.type == SOCK_STREAM:
			if 'tcp_err' in self._callback:
				pear_name = transport._sock.getpeername()
				self._callback['tcp_err']((pear_name[0],pear_name[1]),transport,_error)
		elif 'udp_err' in self._callback:
			sock_name = transport._sock.getsockname()
			self._callback['udp_err']((sock_name[0],sock_name[1]),transport,_error)
	def _do_connection_made(self,transport):
		if transport._sock.type == SOCK_STREAM:
			pear_name = transport._sock.getpeername()
			self.__srv_connections["tcp(%s:%d)"%(pear_name[0],pear_name[1])] = transport
		else:
			sock_name = transport._sock.getsockname()
			self.__srv_connections["udp(%s:%d)"%(sock_name[0],sock_name[1])] = transport
		
	def _do_connection_lost(self,transport):
		print ('lost',transport)
	def _do_connection_error(self,transport,_error):
		self._do_error_callback(transport,_error)
	def _do_connection_eof(self,transport):
		print ('eof',transport._sock.type,transport._sock.getsockname(),transport._sock.getpeername())
		for pear_name,trans in self.__srv_connections.items():
			if trans == transport:
				del self.__srv_connections[pear_name]
				break
	def register_function(self,server,req,callback_function):
		pass
	
	def del_tcp_server(self, srv_name):
		return self._del_server(self.__tcp_srv_info, srv_name)
	def del_udp_server(self, srv_name):
		return self._del_server(self.__udp_srv_info, srv_name)
		
	def del_server(self, srv_name=None):
		del_tcp = self.del_tcp_server(srv_name)
		del_udp = self.del_udp_server(srv_name)
		return del_tcp,del_udp
		
	def get_inet_aton(self,addr_str):
		addr = inet_aton(addr_str)
		#print ('addr',addr)
		if isinstance(addr[0],int):
			return (addr[0] << 24) + (addr[1] << 16) + (addr[2]<<8) + addr[3]
		else:
			return (ord(addr[0]) << 24) + (ord(addr[1]) << 16) + (ord(addr[2])<<8) + ord(addr[3])
	def get_inet_ntoa(self,addr_uint):
		return '%d.%d.%d.%d'%((addr_uint>>24)&0xff, (addr_uint>>16)&0xff, (addr_uint>>8)&0xff, addr_uint&0xff)
		
	def get_own_addr_hash_list(self):
		myname = getfqdn(gethostname())
		ipList = gethostbyname_ex(myname)
		print (myname,'iplist:',ipList)
		#print (self._srv_s.getsockname())
		addr_int_list = []
		for addr in ipList[2]:
			addr_int_list.append(self.get_inet_aton(addr))
		print (addr_int_list)
		return addr_int_list
		
	def run(self):
		pass
	def stop(self):
		try:
			for _task in asyncio.Task.all_tasks(self._event_loop_thread.loop):
				_task.cancel()
		except Exception as e:
			print ('as select cancel task err:%s'%e)
			pass
		try:
			self._event_loop_thread.stop()
		except Exception as e:
			print ('as select stop err:%s'%e)
			pass
		print ('as select stop ok')
	def do_send_udp_cast(self,msg,host='224.0.0.119',port=30000):
		return None
	@asyncio.coroutine
	def send_tcp_data(self,transport,send_data):
		return transport.write(send_data)
	@asyncio.coroutine
	def send_udp_data(self,transport,send_data,pear_str):
		pear_list = pear_str.split(":")
		pear_addr = (pear_list[0],int(pear_list[1]))
		return transport.sendto(send_data,pear_addr)
	def send_data_done(self,*abc):
		print("send done",abc)
	def send_data(self,cur_dev,real_send_bytes,mode=None):
		ret = None
		if cur_dev.startswith('tcp'):
			for pear_name,trans in self.__srv_connections.items():
				if pear_name == cur_dev:
					self._event_loop_thread.add_task(self.send_tcp_data(trans,real_send_bytes))
					ret = True
					break
		else:
			for pear_name,trans in self.__srv_connections.items():
				if pear_name.startswith('udp'):
					ret_coro = self._event_loop_thread.add_task(self.send_udp_data(trans,real_send_bytes,cur_dev[4:-1]))
					#ret_coro.add_done_callback(self.send_data_done)
					ret = True
					break
		return ret
	
@asyncio.coroutine
def test(v):
	while True:
		print("running",v)
		yield from asyncio.sleep(1)

if __name__ == '__main__':
	import time
	event = Event()
	event_loop_thread = EventLoopThread(event)
	event_loop_thread.setDaemon(True)
	event_loop_thread.start()
	
	srv_ctrl = srv_control(event_loop_thread)
	event.wait() # Let the loop's thread signal us, rather than sleeping
	
	timer_t = event_loop_thread.add_task(test(1)) # This is a real task
	def callback(pear,srv_info,msg_data):
		print ('<==TCP [%s:%s]' %(pear,msg_data))
	def udp_callback(pear,srv_info,msg_data):
		print ('<==UDP [%s:%s]' %(pear,msg_data))

	srv_ctrl.set_callback('tcp',callback)
	srv_ctrl.set_callback('udp',udp_callback)
	
	srv_ctrl.add_tcp_server('t2000', '192.168.1.50',3000)
	srv_ctrl.add_udp_server('u2000', '192.168.1.50',3000)
	srv_ctrl.add_multicast_server('m2000', '192.168.1.50',30000,'224.0.0.119')
	
	srv = None
	while True:
		x = input('>>')
		if x == 'Q':
			break
		elif x == 'A':
			srv_ctrl.add_tcp_server('t5000', '192.168.1.50',5000)
			srv_ctrl.add_udp_server('u5000', '192.168.1.50',5000)
		elif x == 'AT':
			srv_ctrl.start_timer(1,1)
		elif x == 'RT':
			srv_ctrl.stop_timer(1)
		elif x == 'DU':
			srv_ctrl.del_server('u2000')
			print ('del srver u2000')
			event_loop_thread.cancel_task(timer_t)
		elif x == 'DT':
			srv_ctrl.del_server('t2000')
			print ('del srver t2000')
		else:
			print ('put',x)
			#send_msg_to_Q(event_loop_thread.msg_Q,x)
			event_loop_thread.send_msg(x)
			print ('put',x,'ok')
			#b.add_task(send_msg_to_Q(b.msg_Q,x))
	
	print (asyncio.Task.all_tasks(event_loop_thread.loop))
	for _task in asyncio.Task.all_tasks(event_loop_thread.loop):
		_task.cancel()
	time.sleep(1)
	print(asyncio.Task.all_tasks(event_loop_thread.loop))
	event_loop_thread.stop()