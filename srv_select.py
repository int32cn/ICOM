#!/usr/bin/python
# -*- coding= utf-8 -*-

from select import select 
from socket import socket,inet_aton,getfqdn,gethostname,gethostbyname_ex,AF_INET, SOCK_STREAM, SOCK_DGRAM, SOL_SOCKET,SO_REUSEADDR,SOL_IP, IP_DROP_MEMBERSHIP,IP_ADD_MEMBERSHIP,INADDR_ANY,IP_MULTICAST_TTL,IP_MULTICAST_LOOP
from threading import Thread,Condition
try:
	from queue import Queue,Empty
except:
	from Queue import Queue,Empty

import struct

class  tcp_srv:
	def __init__(self):
		#sockets from which we except to read 
		self.inputs = []
		#tcp connected client sockets
		self.tcp_clients = []
		#udp Outgoing message queues (socket:Queue) 
		self.udp_message_queue = None
		#tcp connected clients Outgoing message queues (socket:Queue)
		self.tcp_clients_message_queues = {}
		self.tcp_server = []
		self.udp_server = []
		self.cast_server = []
		
		self.__callback_dict = {}
		self.__server_info = {}
		self.__tcp_clients_info = {}
		#A optional parameter for select is TIMEOUT 
		self.timeout = 3.0
		self.client_timeout = 1.0
		self.__tcp_callback = None
		self.__tcp_err_callback = None
		self.__udp_err_callback = None
		self.__udp_callback = None
		self.__multicast_callback = None
		self.__thread_id = None
		self.__client_thread_id = None
		
		self._client_con_sig = Condition()
		self.__quit = False
		self.__client_quit = False
	def start_server(self,sock_type='tcp',host='0.0.0.0',port=10086,multicast_ip=None):
		#create a socket 
		__is_stream_sock = False
		for server, srv_info in  self.__server_info.items():
			if srv_info['sock_type'] == sock_type and srv_info['port'] == port and srv_info['host'] == host and srv_info['multicast_ip'] == multicast_ip:
				srv_info['req_stop'] = False
				return server
		if sock_type == 'tcp':
			server = socket(AF_INET,SOCK_STREAM)
			__is_stream_sock = True
		else:
			server = socket(AF_INET,SOCK_DGRAM)
			__is_stream_sock = False
			if self.udp_message_queue is None:
				self.udp_message_queue = Queue()
		
		#set option reused 
		server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		print ('start srv:',sock_type,host,port,multicast_ip)
		if not isinstance(host,str):
			host = host.decode()
		
		if __is_stream_sock is False:
			if multicast_ip is not None:
				if not isinstance(multicast_ip,str):
					multicast_ip = multicast_ip.decode()
				mreq = struct.pack('4sl',inet_aton(multicast_ip),int(INADDR_ANY))
				server.setsockopt(SOL_IP, IP_MULTICAST_TTL, 2)
				server.setsockopt(SOL_IP, IP_MULTICAST_LOOP, 0)
				server.setsockopt(SOL_IP, IP_ADD_MEMBERSHIP, mreq)
				self.cast_server.append(server)
			else:
				self.udp_server.append(server)
		else:
			self.tcp_server.append(server)
		
		server.setblocking(False)
		server.bind((host,port))
		if __is_stream_sock is True:
			server.listen(36)
		
		self.__server_info.setdefault(server,{'sock_type':sock_type,'host':host,'port':port,'methods':{},'multicast_ip':multicast_ip,'req_stop':False})
		self.inputs.append(server)
		
		return server
		
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
	
	def do_send_udp_cast(self,msg,host='224.0.0.119',port=30000):
		for server, srv_info in  self.__server_info.items():
			if srv_info['sock_type'] != 'tcp' and srv_info['multicast_ip'] is not None and srv_info['req_stop'] is False:
				address = (srv_info['multicast_ip'],srv_info['port'])
				self.udp_message_queue.put((server,address,msg))
				return 0
		
		return None
	def send_data(self,cur_dev,real_send_str,mode=None):
		ret = None
		if cur_dev.startswith('udp'):
			if self.udp_server:
				addr = cur_dev[4:-1].split(':')
				if len(addr) == 2 and addr[1].isdigit():
					pear = (addr[0],int(addr[1]))
					self.udp_message_queue.put((self.udp_server[0],pear,real_send_str))
					ret = 0
		elif cur_dev.startswith('tcp'):
			#print ('send',cur_dev,real_send_str)
			self._client_con_sig.acquire()
			for client_sock,client_info in self.__tcp_clients_info.items():
				#print (client_info['address'])
				client_dev = "tcp(%s:%d)"%(client_info['address'][0],client_info['address'][1])
				if client_dev == cur_dev and client_sock in self.tcp_clients_message_queues:
					self.tcp_clients_message_queues[client_sock].put(real_send_str)
					ret = 0
					break
			self._client_con_sig.release()
		return ret
		
	def stop_server(self,sock_type='tcp',host='0.0.0.0',port=10086,multicast_ip=None):
		for server, srv_info in  self.__server_info.items():
			if srv_info['sock_type'] == sock_type and srv_info['port'] == port and srv_info['host'] == host and srv_info['multicast_ip'] == multicast_ip:
				srv_info['req_stop'] = True
		print ('stop srv:',sock_type,host,port,multicast_ip)
		#print ('self.__server_info:',self.__server_info)
		if len(self.inputs) == 0:
			print ('stop server thread')
			self.stop()
	def set_callback(self,type='tcp',callback=None):
		if type == 'tcp':
			self.__tcp_callback = callback
		elif type == 'udp_cast':
			self.__multicast_callback = callback
		elif type == 'tcp_err':
			self.__tcp_err_callback = callback
		elif type == 'udp_err':
			self.__udp_err_callback = callback
		else:
			self.__udp_callback = callback
		
	def register_function(self,server,req,callback_function):
		if server in self.__server_info:
			srv_info = self.__server_info[server]
			if not isinstance(req,bytes):
				req = req.encode()
			srv_info['methods'].setdefault(req,callback_function)
			
		return None
		
	def run_client_manager(self):
		self.__client_thread_id = Thread(target=self._client_routine,args=())
		self.__client_thread_id.setDaemon(True)
		self.__client_thread_id.start()
	def run(self):
		if len(self.inputs) == 0:
			return
		if self.__thread_id is not None and not self.__thread_id.isAlive():
			self.__quit = True
			self.__thread_id.join()
			self.__thread_id = None
		if self.__thread_id is None:
			self.__quit = False
			self.__thread_id = Thread(target=self.routine,args=())
			self.__thread_id.start()
		if self.__client_thread_id is None:
			self.__client_quit = False
			self.run_client_manager()
		
	def stop(self):
		self.__quit = True
		self.__client_quit = True
		if self.__thread_id is not None and self.__thread_id.isAlive():
			self.__thread_id.join()
			self.__thread_id = None
	
	def __remove_client_connection(self, fd):
		self._rm_client_connection(fd)
		try:
			fd.close()
		except Exception as e:
			print ('Exception in close/remove connection:%s'%e)
			pass
	def __remove_server(self, s):
		if s in self.inputs:
			self.inputs.remove(s)
		if s in self.tcp_server:
			self.tcp_server.remove(s)
		if s in self.udp_server:
			self.udp_server.remove(s)
		if s in self.cast_server:
			self.cast_server.remove(s)
		try:
			s.close()
		except Exception as e:
			print ('Exception in close s:%s'%e)
			pass
		
	def __check_req_stop_server(self):
		#print ('__server_info',self.__server_info)
		need_del_server = [server_sock for server_sock in self.__server_info.keys() if self.__server_info[server_sock]['req_stop'] == True]
		#print ('need_del_server',need_del_server)
		for server_sock in  need_del_server:
			multicast_ip = self.__server_info[server_sock]['multicast_ip']
			if multicast_ip is not None and self.__server_info[server_sock]['sock_type'].startswith('udp'):
				mreq = struct.pack('4sl',inet_aton(multicast_ip),INADDR_ANY)
				server_sock.setsockopt(SOL_IP, IP_DROP_MEMBERSHIP, mreq)
			self.__remove_server(server_sock)
			del self.__server_info[server_sock]
		#print ('new___server_info',self.__server_info)
		return len(self.inputs)
		
	def _add_client_connection(self,server_sock,client_sock,client_addr):
		self._client_con_sig.acquire()
		self.tcp_clients.append(client_sock)
		if client_sock not in self.__tcp_clients_info:
			self.__tcp_clients_info.setdefault(client_sock,{'active':True,'parent':server_sock,'address':client_addr})
		self._client_con_sig.notifyAll()
		self._client_con_sig.release()
	def _rm_client_connection(self,client_sock):
		self._client_con_sig.acquire()
		if client_sock in self.tcp_clients:
			self.tcp_clients.remove(client_sock)
		if client_sock in self.__tcp_clients_info:
			del self.__tcp_clients_info[client_sock]
		self._client_con_sig.release()
	def _client_routine(self,args=None):
		while self.__client_quit is False:
			tcp_clients_sets = []
			self._client_con_sig.acquire()
			tcp_clients_sets = self.tcp_clients
			self._client_con_sig.release()
			
			if not self.tcp_clients:
				print ('tcp_clients_sets none')
				self._client_con_sig.acquire()
				self._client_con_sig.wait()
				self._client_con_sig.release()
				continue
			
			readable , writable , exceptional = select(tcp_clients_sets, [], tcp_clients_sets, self.client_timeout)
			#print ('tcp_clients',tcp_clients_sets)
			# When timeout reached , select return three empty lists
			
			for s in exceptional: 
				print (" exception condition on ", s.getpeername() )
				#stop listening for input on the connection 
				self.__remove_client_connection(s)
			for s in readable :
				try:
					__fx = s.fileno()
				except Exceptions as e:
					print (" get fileno err %s"%e)
					self.__remove_client_connection(s)
					pass
					continue
				
				skip_close = False
				try:
					pear = s.getpeername()
					data = s.recv(2048)
					if data :
						#print (" received %s from %s" %(data ,pear) )
						if s not in self.tcp_clients_message_queues:
							self.tcp_clients_message_queues[s] = Queue()
						
						if self.__tcp_callback is not None:
							self.__tcp_callback(pear,self.__callback_dict,data)
						
						if data.startswith(b'ECHO') or data.startswith(b'echo'):
							self.tcp_clients_message_queues[s].put(data[4:])
						else:
							self.tcp_clients_message_queues[s].put(b'ACK%d\n'%len(data))
					elif skip_close is False: 
						#Interpret empty result as closed connection 
						print ("  closing ", pear )
						if self.__tcp_err_callback is not None:
							self.__tcp_err_callback(pear,self.__callback_dict,'close')
						self.__remove_client_connection(s)
				except Exception as e:
					print ('Exception in recv %s, do close'%e)
					if self.__tcp_err_callback is not None and pear is not None:
						self.__tcp_err_callback(pear,self.__callback_dict,'close')
					self.__remove_client_connection(s)
					pass
					
			if tcp_clients_sets:
				_readable , _writable , _exceptional = select([], tcp_clients_sets, [], 0.001)
				for s in _writable:
					if s not in self.tcp_clients_message_queues:
						continue
					tcp_queue_empty = False
					#try send udp ack msg
					while tcp_queue_empty is False:
						try:
							send_msg = self.tcp_clients_message_queues[s].get_nowait() 
						except Empty: 
							#print (" queue empty", s.getpeername() )
							tcp_queue_empty = True
							pass
						except Exception as e:
							print (" queue err:%s in key%s\n"%(e,s) )
							tcp_queue_empty = True
							pass
						else:
							#print (" sending %s to %s" %(send_msg,str(s)) )
							#for req,callback_function in self.__tcp_clients[s]['methods'].items():
							#	if next_msg.startswith(req):
							#		callback_function(pear,self.__callback_dict,next_msg)
							s.send(send_msg)
		else:
			print ('srv_select client thread quit')
		
	def routine(self,args=None):
		while self.inputs and self.__quit is False:
			if 0 == self.__check_req_stop_server():
				break
			readable , writable , exceptional = select(self.inputs, [], self.inputs, self.timeout)
			#print (readable , writable , exceptional)
			# When timeout reached , select return three empty lists 
			
			for s in readable :
				if s in self.tcp_server:
					# A "readable" socket is ready to accept a connection 
					try:
						connection, client_address = s.accept()
						#print ("    connection from %s to %s\n"%(str(client_address),connection.getsockname()))
						connection.setblocking(0)
						self._add_client_connection(s,connection,client_address)
					except Exception as e:
						print ('Exception in accept %s'%e)
						pass
				elif s in self.udp_server or s in self.cast_server:
					try:
						next_msg, pear = s.recvfrom(4096)
						if next_msg:
							#print ("    connection %s from %s to %s\n"% (str(next_msg),str(pear),s.getsockname()))
							
							if self.__server_info[s]['multicast_ip'] is not None and self.__multicast_callback is not None:
								self.__multicast_callback(pear,self.__callback_dict,next_msg)
							elif self.__udp_callback is not None:
								self.__udp_callback(pear,self.__callback_dict,next_msg)
								
							for req,callback_function in self.__server_info[s]['methods'].items():
								if next_msg.startswith(req):
									callback_function(pear,self.__callback_dict,next_msg)
							
							if next_msg.startswith(b'ECHO') or next_msg.startswith(b'echo'):
								self.udp_message_queue.put((s,pear,next_msg[4:]))
							elif self.__server_info[s]['multicast_ip'] is None:
								self.udp_message_queue.put((s,pear,b'ACK%d\n'%len(next_msg)))
						else:
							print ('udp msg none', pear)
					except Exception as e:
						print ('Exception in udp recvfrom %s'%e)
						#e.errno == socket.errno.EWOULDBLOCK:
						pass
				else:
					print ('srv_select this should not runed')
			
			udp_queue_empty = False
			#try send udp ack msg
			while udp_queue_empty is False:
				try:
					server_sock,pear,send_msg = self.udp_message_queue.get_nowait()
				except Empty:
					udp_queue_empty = True
					pass
				except Exception as e:
					print ('get udp msg exception:%s'%e)
					udp_queue_empty = True
					pass
				else:
					if server_sock in self.udp_server or server_sock in self.cast_server:
						try:
							server_sock.sendto(send_msg,0,pear)
						except Exception as e:
							print ('srv_select sendto err:%s'%e)
							pass
			
		else:
			print ('srv_select routine thread quit')
	
	def __del__(self):
		for s in self.tcp_server:
			s.close()
		for s in self.udp_server:
			s.close()
		for s in self.cast_server:
			s.close()
		for s in self.tcp_clients:
			s.close()
		for s,Q in self.tcp_clients_message_queues.items():
			del Q
		
if '__main__' == __name__:
	srv = tcp_srv()
	def callback(pear,srv_info,msg_data):
		print ('<==TCP [%s:%s]' %(pear,msg_data))
	def udp_callback(pear,srv_info,msg_data):
		print ('<==UDP [%s:%s]' %(pear,msg_data))
	#srv1 = srv.start_server('udp','0.0.0.0',10086)
	srv2 = srv.start_server('tcp','0.0.0.0',10086)
	srv3 = srv.start_server('udp','0.0.0.0',10086,'224.0.0.119')
	srv.set_callback('tcp',callback)
	srv.set_callback('udp',udp_callback)
	def show_cb_msg(a,b,c):
		print('UDP',a,b,c)
	def show_cb_msg2(a,b,c):
		print('TCP',a,b,c)
	#srv.register_function(srv1,'GET',show_cb_msg)
	#srv.register_function(srv2,'GET',show_cb_msg2)
	srv.register_function(srv3,'GET',show_cb_msg2)
	srv.run()
	while 1:
		try:
			send_str = input()
		except:
			break
	srv.stop()
	