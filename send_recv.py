#!/usr/bin/python
# -*- coding= utf-8 -*-

import threading
import socket

class socket_manager():
	def __init__(self,logger=None,host='0.0.0.0',port=30000,group='224.0.0.119'):
		self._be_multicast = False
		self._multicast_group = group
		self._multicast_port = port
		address = (host,port)
		self._cli_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self._srv_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self._srv_s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		
		self._srv_s.bind(address)
		if group is not None:
			self._be_multicast = True
			self._srv_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
			self._srv_s.setsockopt(socket.IPPROTO_IP,
									socket.IP_ADD_MEMBERSHIP,
									socket.inet_aton(group) + socket.inet_aton('0.0.0.0'))
			self._cli_s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
			self._cli_s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 0)
			#self._cli_s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton("192.168.1.7"))
			self._cli_s.setsockopt(socket.IPPROTO_IP,
									socket.IP_ADD_MEMBERSHIP,
									socket.inet_aton(group) + socket.inet_aton('0.0.0.0'))
		#self._srv_s.setblocking(0)
		
		self._srv_callback = None
		self._thead = None
		self._logger = logger
		self._stop   = False
		self._addr_atol = lambda x:int(repr(x).replace('.','').replace(':','').replace("'",''))
	
	def __socket_recv_run(self,s):
		while self._stop is False:  
			data, addr = self._srv_s.recvfrom(2048)  
			if not data:  
				self._logger.warning( "client has exist"  )
				continue
			self._logger.debug( "received: data %d bytes from %s\n", len(data), addr)
			
			if self._srv_callback is not None:
				self._srv_callback(self._addr_atol(addr[0]),data)
				
		if self._be_multicast is True:
			self._srv_s.setsockopt(socket.IPPROTO_IP,
								socket.IP_DROP_MEMBERSHIP,
								socket.inet_aton(self._multicast_group) + socket.inet_aton('0.0.0.0'))
		self._srv_s.close()
		self._srv_s = None
		
	def start_run(self,callback):
		self._srv_callback = callback
		self._thead = threading.Thread(target=self.__socket_recv_run,args = (1,), name = 'thread-socket')
		self._thead.setDaemon(True)
		self._thead.start()
		
	def stop_run(self):
		self._stop = True
		
	def do_send(self,msg,host='224.0.0.119',port=30000):
		address = (host,port)
		if self._be_multicast is True:
			address = (self._multicast_group,self._multicast_port)
		#self._logger.debug( "send multicast data %d bytes to %s\n", len(msg), address[0])
		return self._cli_s.sendto(msg, address)
		
	def get_inet_aton(self,addr_str):
		addr = socket.inet_aton(addr_str)
		return (ord(addr[0]) << 24) + (ord(addr[1]) << 16) + (ord(addr[2])<<8) + ord(addr[3])
		
	def get_inet_ntoa(self,addr_uint):
		return '%d.%d.%d.%d'%((addr_uint>>24)&0xff, (addr_uint>>16)&0xff, (addr_uint>>8)&0xff, addr_uint&0xff)
		
	def get_own_addr_hash_list(self):
		myname = socket.getfqdn(socket.gethostname())
		ipList = socket.gethostbyname_ex(myname)
		print (myname,ipList)
		#print (self._srv_s.getsockname())
		addr_int_list = []
		for addr in ipList[2]:
			addr_int_list.append(self.get_inet_aton(addr))
		print (addr_int_list)
		return addr_int_list
		
	def __finalize__(self):
		if self._srv_s is not None:
			self._srv_s.close()
			self._srv_s = None
		if self._cli_s is not None:
			self._cli_s.close()
			self._cli_s = None
			