#!/usr/bin/python
# -*- coding= utf-8 -*-

import ctypes as ct
from struct_manage import *
import encrypt_data

class user_manager():
	def __init__(self,logger=None):
		self._user_group = {}
		self._user_list = {}
		self._admin_key = 0
		self._vice_admin_key = 0
		self._vice2_admin_key = 0
		self._logger = logger
		
	def receive_cast(self,cast_content):
		self._logger.info (cast_content)
		
	def get_groups_num(self):
		return len(self._user_group)
		
	def get_groups(self):
		return self._user_group
		
	def get_user_num(self):
		return len(self._user_list)
	
	def get_user(self,userKey=None):
		#self._logger.info('get_user:%s\n'%self._user_list)
		if userKey is None:
			return self._user_list
		elif userKey in self._user_list:
			return self._user_list[userKey]
		else:
			return None
		
	def set_admin_user(self,admin_key):
		self._admin_key = admin_key
	def set_vice_admin_user(self,_vice_admin_key):
		self._vice_admin_key = _vice_admin_key
	def set_vice2_admin_user(self,_vice2_admin_key):
		self._vice2_admin_key = _vice2_admin_key
		
	def get_admin_user_key(self):
		return self._admin_key
	def get_vice_admin_user_key(self):
		return self._vice_admin_key
	def get_vice2_admin_user_key(self):
		return self._vice2_admin_key
		
	def update_user(self,user_key,_user_info):
		self._logger.info('update_user:%s->%s\n'%(user_key,_user_info))
		if user_key not in self._user_list:
			_new_user_info    = USER_INFO()
			_new_user_info.NickName = _user_info.NickName
			_new_user_info.UdpPort  = _user_info.UdpPort
			_new_user_info.Addr     = _user_info.Addr
			_new_user_info.Status   = _user_info.Status
			self._user_list.setdefault(user_key,_new_user_info)
		else:
			self._user_list[user_key].NickName = _user_info.NickName
			self._user_list[user_key].UdpPort  = _user_info.UdpPort
			self._user_list[user_key].Addr     = _user_info.Addr
			self._user_list[user_key].Status   = _user_info.Status
			
	def remove_user(self,user_key,user_info):
		self._logger.info('remove_user:%s->%s\n'%(user_key,user_info))
		if user_key in self._user_list:
			del self._user_list[user_key]
		
class multicast_manager():
	_MAC_PACKET_SIZE = 1450
	
	def __init__(self,logger=None):
		self._logger = logger
		self._send_msg_header = MULTICAST_HEADER()
		self._msg_header_len  = ct.sizeof(self._send_msg_header)
		self._send_msg = None
		self._recv_msg = None
		self._begin_tag  = EMPTY_TAG(TAG_ID.TAG_MSG_BEGIN)
		self._end_tag  = EMPTY_TAG(TAG_ID.TAG_MSG_END)
		self.__send    = self._dummy_send
		self._send_seq = 0
		self._version_tag = VERSION_INFO()
		self.__message_processer = self._dummy_msg_processer
		self._logger.debug ('multicast init')
		self._user_addr_atol = lambda x:int(repr(x).replace('.','').replace(':','').replace("'",''))
		self._key_info_pu = None
		self._key_info_pr = None
		
	def _dummy_msg_processer(self,msg_header,tag):
		self._logger.warning('_dummy PROC: %s %s'%(msg_header, tag))
	def set_msg_processer(self,__message_processer):
		self.__message_processer = __message_processer
		
	def set_key_info(self,pu,pr):
		self._key_info_pu = pu
		self._key_info_pr = pr
	def load_key_info_from_path(self,data_path):
		__pu,__pr = encrypt_data.load_pem_data_common(data_path)
		self.set_key_info(__pu,__pr)
		del __pu
		del __pr
	
	def _dummy_send(self,_msg):
		msg_header = stream2struct(_msg,MULTICAST_HEADER)
		self._logger.debug('SEND: %s %s len:%d\n'%(msg_header,type(_msg),ct.sizeof(_msg)))
		#i = 0
		#for ch in _msg:
		#	print('%d [%x]\n'%(i,_msg[i]))
		#	i += 1
		#self.multicast_receive(_msg)
	def set_send_function(self,_send):
		self.__send = _send
		
	def _set_send_msg_header(self, msg_id):
		self._send_msg_header.ID  = msg_id
		self._send_msg_header.Seq = self._send_seq
		self._send_seq += 1
		
	def multicast_receive(self,addr,_msg_str):
		try:
			_dec_msg_str = encrypt_data.hash_decrypt_data_common(_msg_str,len(_msg_str),self._key_info_pr)
		except Exception as e:
			print ('decryptd err:%s\n'%e)
			self._logger.error('decryptd err:%s\n'%e)
			pass
			return _msg_str
		total_len,_msg = bytes_to_ctypes_array(_dec_msg_str)
		skip_len = ct.sizeof(MULTICAST_HEADER)
		if total_len < skip_len:
			self._logger.error('RECV: %d too short,drop\n'%total_len)
			return _msg_str
		msg_header = stream2struct(_msg,MULTICAST_HEADER)
		if msg_header.DataLen + skip_len != total_len:
			self._logger.error('RECV: msg length error (DataLen:%d,TotalLen:%d),drop\n'%(msg_header.DataLen,total_len))
			return _msg_str
		#TODO, checksum here,need drop checksum error data
		
		new_msg_str_list = []
		msg_header.SrcIP = addr
		#msg_header.DstIP = self._user_addr_atol(addr[1])
		self._logger.debug('RECV: %s skip_len:%d\n'%(msg_header,skip_len))
		Tag = get_next_tag(_msg, skip_len)
		ret_str = self.__message_processer(msg_header,self._begin_tag)
		if ret_str is not None:
			new_msg_str_list.append(ret_str)
		while Tag is not None:
			#print ('RECV: skip_len:%d, Tag:0x%x,Len:%d\n'%(skip_len,Tag.Tag,Tag.Len))
			tag_struct = get_tag_struct(Tag.Tag)
			if tag_struct is not None: #skip unknown structure
				self._logger.info(tag_struct)
				tag_content = get_tag_msg(_msg,skip_len,tag_struct)
				ret_str = self.__message_processer(msg_header,tag_content)
				if ret_str is not None:
					new_msg_str_list.append(ret_str)
			else:
				self._logger.warning('unknown Tag:0x%x Len:%d\n'%(Tag.Tag,Tag.Len))
			skip_len += ct.sizeof(MSG_TAG) + Tag.Len
			Tag = get_next_tag(_msg, skip_len)
		ret_str = self.__message_processer(msg_header,self._end_tag)
		if ret_str is not None:
			new_msg_str_list.append(ret_str)
		if len(new_msg_str_list) > 0:
			return ''.join(new_msg_str_list)
		return None
		
	def set_verion_info(self,ver,description):
		self._version_tag.Version = ver
		if type(description) == type(self._version_tag.Description):
			self._version_tag.Description = description
		else:
			self._version_tag.Description = description.encode()
			
	def multicast_login(self,nick_name,udp_port,status):
		self._logger.debug ("Login: %s %d Status:%d\n"%(repr(nick_name),udp_port,status))
		self._set_send_msg_header(MSG_ID.ID_LOGIN)
		user_info = USER_INFO()
		user_info.NickName = nick_name
		user_info.Addr     = 0
		user_info.UdpPort  = udp_port
		user_info.Status   = status
		p_data = struct2stream(join_header_and_body(self._send_msg_header, user_info, self._version_tag))
		en_d = encrypt_data.hash_encrypt_data_common(p_data,len(p_data),self._key_info_pu)
		self.__send(en_d)
		
	def multicast_logoff(self,nick_name):
		self._logger.debug ('Logoff: %s\n'%repr(nick_name))
		self._set_send_msg_header(MSG_ID.ID_LOGOFF)
		user_info = USER_INFO()
		user_info.NickName = nick_name
		user_info.Addr     = 0
		p_data = struct2stream(join_header_and_body(self._send_msg_header, user_info))
		en_d = encrypt_data.hash_encrypt_data_common(p_data,len(p_data),self._key_info_pu)
		self.__send(en_d)
		
	def multicast_userlist(self,user_list_info,admin_index,vice_admin_index):
		#self._logger.debug ('Userlist: %s\n'%repr(user_list_info))
		total_user_num = len(user_list_info)
		total_packet_size = self._MAC_PACKET_SIZE // 256 * 256
		one_packet_user_num = (total_packet_size - ct.sizeof(USER_LIST)) / ct.sizeof(USER_INFO)
		self._set_send_msg_header(MSG_ID.ID_AUTH_USER_LIST)
		print (total_user_num,one_packet_user_num)
		one_packet_user_num = int(float(one_packet_user_num))
		user_info_list = []
		user_list      = USER_LIST()
		user_list.UserCount      = total_user_num
		user_list.TotalSections  = int(total_user_num / one_packet_user_num)
		user_list.CurrentSection = 0
		user_list.AdminIndex     = admin_index
		user_list.SecondIndex    = vice_admin_index
		user_info_list.append(user_list)
		
		packet_user_count = 0
		for user_key,user_value in user_list_info.items():
			user_info = USER_INFO()
			user_info.NickName = user_value.NickName
			user_info.Addr     = user_value.Addr
			user_info.Status   = user_value.Status
			user_info.UdpPort  = user_value.UdpPort
			user_info_list.append(user_info)
			packet_user_count += 1
			#send one packed user info, and then clear the list, reset CurrentSectionIndex
			if packet_user_count % one_packet_user_num == 0:
				p_data = struct2stream(join_header_and_body(self._send_msg_header, user_info_list))
				en_d = encrypt_data.hash_encrypt_data_common(p_data,len(p_data),self._key_info_pu)
				self.__send(en_d)
				user_info_list = []
				user_list.CurrentSection += 1
				user_info_list.append(user_list)
		#left part user info send
		if packet_user_count % one_packet_user_num > 0:
			p_data = struct2stream(join_header_and_body(self._send_msg_header, user_info_list))
			en_d = encrypt_data.hash_encrypt_data_common(p_data,len(p_data),self._key_info_pu)
			self.__send(en_d)
		
	def multicast_contest_reply(self,admin_type):
		self._logger.debug ('Contest: %s'%repr(admin_type))
		self._set_send_msg_header(MSG_ID.ID_ADMIN_CONTEST_REPLY)
		admin_contest_info = ADMIN_CONTEST()
		admin_contest_info.AdminType = admin_type
		p_data = struct2stream(join_header_and_body(self._send_msg_header, admin_contest_info))
		en_d = encrypt_data.hash_encrypt_data_common(p_data,len(p_data),self._key_info_pu)
		self.__send(en_d)

