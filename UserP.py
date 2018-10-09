#!/usr/bin/python
# -*- coding= utf-8 -*-

from user_cast import *
#import sched
from threading import Timer as threading_timer
import logging
from sys import stdout as sys_stdout

#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
#logging.basicConfig(level=logging.ERROR,
#                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#                datefmt='%a, %d %b %Y %H:%M:%S',
#                filename='myapp.log',
#                filemode='w')

stream_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%H:%M:%S',)
#file_formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)  

logger = logging.getLogger("UserP")
#file_handler = logging.FileHandler("mytest.log")
#file_handler.setLevel(logging.INFO)
#file_handler.setFormatter(file_formatter)
stream_handler = logging.StreamHandler(sys_stdout)
stream_handler.setLevel(logging.WARNING)
stream_handler.setFormatter(stream_formatter)  
#logger.addHandler(file_handler)  
logger.addHandler(stream_handler)


class UserManager():
	LOGIN_NONE = 0
	LOGIN_SEND = 1
	LOGIN_REPLY_GET = 2
	LOGIN_OK   = 3
	_T_primary_no_reply = 1000
	_T_vice_no_reply    = 2000
	_T_vice2_no_reply   = 3000
	_T_login   = 5000
	_T_admin_contest_max = 3000
	ADMIN_TYPE_NONE    = 0
	ADMIN_TYPE_PRIMARY = 1
	ADMIN_TYPE_VICE    = 2
	ADMIN_TYPE_VICE2    = 3
	
	def __init__(self,user_manager,multicast_manager,root=None):
		self._user_manager      = user_manager
		self._multicast_manager = multicast_manager
		self.__root             = root
		self._be_admin_type     = self.ADMIN_TYPE_NONE
		self._any_admin_alive   = False
		self._user_list_got     = False
		self._login_status      = self.LOGIN_NONE
		self._login_timer          = None
		self._not_inlist_login_timer = None
		self._admin_contest_timer  = None
		self._user_list_reply_timer = None
		self._admin_contest_ok     = False
		self._myself_in_list  = False
		#current user keylist,because of multi network card
		self._cur_user_id_list = []
		self._cur_version = 0
		self._cur_user_info    = USER_INFO()
		#set callback
		self._multicast_manager.set_msg_processer(self.receiv_msg_processer)
		
	def load_key_from_path(self,data_path):
		self._multicast_manager.load_key_info_from_path(data_path)
		
	def set_current_user(self,userKeyList,nickName,udp_port):
		self._cur_user_id_list = userKeyList
		if isinstance(nickName,str):
			self._cur_user_info.NickName = nickName.encode()
		else:
			self._cur_user_info.NickName = nickName
		self._cur_user_info.UdpPort = udp_port
		if len(self._cur_user_id_list) == 1: #only one netcard locally
			self._cur_user_info.Addr = self._cur_user_id_list[0]
		else:
			self._cur_user_info.Addr    = 0
		self._cur_user_info.Status  = USER_STATUS.STATUS_OFFLINE
		
	def set_current_verion(self,ver,description):
		self._cur_version = int(ver)
		self._multicast_manager.set_verion_info(self._cur_version,description)
		
	def _try_get_backup_vice_user_keylist(self,user_list,vice_key,vice2_key):
		vice_list = [vk for vk in user_list.keys() if vk not in self._cur_user_id_list]
		vice_backup = 0 #exclude current vice/vice2 key
		for vk in vice_list:
			if vk != vice_key and vk != vice2_key:
				vice_backup = vk
				break
		return vice_list,vice_backup
	
	def _check_set_vice_admin(self,user_list):
		vice_key = self._user_manager.get_vice_admin_user_key()
		vice2_key = self._user_manager.get_vice2_admin_user_key()
		user_count = self._user_manager.get_user_num()
		
		if user_count > 1:
			vice_keylist,bakup_vice = self._try_get_backup_vice_user_keylist(user_list,vice_key,vice2_key)
			vice_keylist_len  = len(vice_keylist)
			if vice_keylist_len > 1:
				if vice_key not in vice_keylist and vice2_key not in vice_keylist:
					vice_key = vice_keylist[0]
					vice2_key = vice_keylist[1]
				elif vice_key not in vice_keylist:
					#vice2 exsit,vice2 upgrate to vice
					vice_key = vice2_key
					vice2_key = bakup_vice
				elif vice2_key not in vice_keylist:
					#vice exsit, vice2 not exsit, select new one as vice2
					vice2_key = bakup_vice
			elif vice_keylist_len > 0 and vice_key not in vice_keylist:
				vice_key = vice_keylist[0]
				vice2_key = 0
		return vice_key,vice2_key
	
	def _get_current_user_seq(self):
		userKey_list = self._user_manager.get_user().keys()
		if self._cur_user_info.Addr not in userKey_list:
			return len(userKey_list)
		
		little_count = 0
		for userKey in userKey_list:
			if userKey < self._cur_user_info.Addr:
				little_count += 1
		return little_count #default the last one
		
	def _do_multicast_userlist(self):
		user_list = self._user_manager.get_user()
		vice_key,vice2_key = self._check_set_vice_admin(user_list)
		logger.debug ('multicast:%s vice_key:%d vice2_key:%d\n'%(user_list,vice_key,vice2_key))
		self._multicast_manager.multicast_userlist(user_list, vice_key, vice2_key)
	
	def login_timeout_noreply(self,args):
		self._login_timer = None
		logger.debug('login status:%d, admin_type:%d args:%s\n'%(self._login_status,self._be_admin_type,args))
		if self._login_status != self.LOGIN_OK and self._be_admin_type is not self.ADMIN_TYPE_PRIMARY:
			logger.warning ('first login,be admin now self:%s\n'%self._cur_user_id_list)
			self._be_admin_type = self.ADMIN_TYPE_PRIMARY
			#print ('own:%s,seq:%d\n'%(self._cur_user_info, self._get_current_user_seq()))
			self._do_multicast_userlist()
			self._user_list_got = True
			
	def reply_auth_userlist(self,args):
		logger.warning('reply_auth_userlist_timeout: args:%s, any_admin_alive:%d\n'%(args,self._any_admin_alive))
		self._user_list_reply_timer = None
		if self._any_admin_alive is False:
			self._do_multicast_userlist()
			
	def start_login(self,nick_name,status=False):
		self._login_status = self.LOGIN_SEND
		if isinstance(nick_name,str):
			self._cur_user_info.NickName = nick_name.encode()
		else:
			self._cur_user_info.NickName = nick_name
		if status:
			self._cur_user_info.Status  = USER_STATUS.STATUS_ONLINE
		else:
			self._cur_user_info.Status  = USER_STATUS.STATUS_OFFLINE
		if len(self._cur_user_id_list) > 0:
			self._user_manager.update_user(self._cur_user_id_list[0], self._cur_user_info)
		self._multicast_manager.multicast_login(self._cur_user_info.NickName, self._cur_user_info.UdpPort, self._cur_user_info.Status)
		if self.__root is not None:
			self._login_timer = self.__root.after(self._T_login, lambda args=(self.LOGIN_SEND,):self.login_timeout_noreply(args))
		else:
			self._login_timer = threading_timer(self._T_login/1000, self.login_timeout_noreply, (self.LOGIN_SEND,))
			self._login_timer.start()
	def not_inlist_relogin(self,args):
		self._not_inlist_login_timer = None
		if self._myself_in_list is False:
			logger.warning('myself not in auth list relogin timeout:%s\n'%args)
			self._multicast_manager.multicast_login(self._cur_user_info.NickName, self._cur_user_info.UdpPort, self._cur_user_info.Status)
		
	def start_logoff(self):
		if len(self._cur_user_id_list) > 0 and self._login_status != self.LOGIN_NONE:
			self._multicast_manager.multicast_logoff(self._cur_user_info.NickName)
		self._login_status      = self.LOGIN_NONE
		
	def get_login_status(self):
		return self._login_status
		
	def get_user_list(self):
		if self._user_list_got is True:
			return self._user_manager.get_user()
		return None
		
	def try_contest_admin(self,admin_type):
		logger.debug('try contest admin:%d, contest_ok:%d\n'%(admin_type,self._admin_contest_ok))
		self._admin_contest_timer = None
		if self._admin_contest_ok is False:
			self._user_manager.multicast_contest_reply(admin_type)
		
	def _get_admin_contest_time(self):
		contest_time = 10* self._get_current_user_seq() % (self._T_login - self._T_vice2_no_reply)
		return contest_time
		
	def receiv_msg_processer(self,msg_header,msg_TLV):
		logger.warning('PROC MSG_ID:0x%x %s Tag:0x%x\n'%(msg_header.ID,type(msg_TLV),msg_TLV.TL.Tag))
		ret_str_val = None
		if msg_header.ID == MSG_ID.ID_LOGIN:
			if msg_TLV.TL.Tag == TAG_ID.TAG_USER_INFO:
				msg_TLV.Addr = msg_header.SrcIP #auto fill addr
				self._user_manager.update_user(msg_TLV.Addr,msg_TLV)
			elif msg_TLV.TL.Tag == TAG_ID.TAG_MSG_END:
				reply_timer_ms = 0
				if self._be_admin_type == self.ADMIN_TYPE_PRIMARY:
					reply_timer_ms = (10 + self._get_current_user_seq()) % self._T_primary_no_reply
				elif self._be_admin_type == self.ADMIN_TYPE_VICE:
					#the primary admin may not alive(unnormal quit), and start timer to reply
					reply_timer_ms = (self._T_primary_no_reply + self._get_current_user_seq()) % self._T_vice_no_reply
				elif self._be_admin_type == self.ADMIN_TYPE_VICE2:
					#the primary and vice may both not alive(unnormal quit), and start timer to reply
					reply_timer_ms = (self._T_vice_no_reply + self._get_current_user_seq()) % self._T_vice2_no_reply
				else:
					reply_timer_ms = (self._T_vice2_no_reply + self._get_current_user_seq()) % self._T_login
				
				#start reply timer now
				if reply_timer_ms > 0 and self._user_list_reply_timer is None:
					self._any_admin_alive = False
					if self.__root is not None:
						self._user_list_reply_timer = self.__root.after(reply_timer_ms, lambda args=(reply_timer_ms,):self.reply_auth_userlist(args))
					else:
						self._user_list_reply_timer = threading_timer(reply_timer_ms/1000, self.reply_auth_userlist, (self.reply_timer_ms,))
						self._user_list_reply_timer.start()
			elif msg_TLV.TL.Tag == TAG_ID.TAG_VERSION:
				if msg_TLV.Version > self._cur_version:
					logger.warning('new version(%d) avalible from:0x%x, currunt version:%d'%(msg_TLV.Version,msg_header.SrcIP,self._cur_version))
					logger.warning('new version description:%s\n'%msg_TLV.Description)
					new_version_src_user = self._user_manager.get_user(msg_header.SrcIP)
					ret_str_val = 'New Version(%d) Avaliable from %s\nDescription:%s\n'%(msg_TLV.Version,new_version_src_user,msg_TLV.Description)
				else:
					logger.debug('peer version:%d, current version:%d\n'%(msg_TLV.Version,self._cur_version))
			elif msg_TLV.TL.Tag != TAG_ID.TAG_MSG_BEGIN:
				logger.warning('unknown Tag:0x%x Len:%d in ID_LOGIN\n'%(msg_TLV.TL.Tag,msg_TLV.TL.Len))
		elif msg_header.ID == MSG_ID.ID_LOGOFF:
			if msg_TLV.TL.Tag == TAG_ID.TAG_USER_INFO:
				#not remove myself, only for Loop test mode
				if msg_header.SrcIP not in self._cur_user_id_list:
					msg_TLV.Addr = msg_header.SrcIP #auto fill addr
					self._user_manager.remove_user(msg_TLV.Addr,msg_TLV)
				
				#check if admin/vice admin user logoff
				if msg_header.SrcIP == self._user_manager.get_admin_user_key():
					self._user_manager.set_admin_user(0)
				elif msg_header.SrcIP == self._user_manager.get_vice_admin_user_key():
					self._user_manager.set_vice_admin_user(0)
				elif msg_header.SrcIP == self._user_manager.get_vice2_admin_user_key():
					self._user_manager.set_vice2_admin_user(0)
				
				#auto upgrate admin type
				if self._be_admin_type == self.ADMIN_TYPE_VICE and 0 == self._user_manager.get_admin_user_key():
					self._be_admin_type = self.ADMIN_TYPE_PRIMARY
				elif self._be_admin_type == self.ADMIN_TYPE_VICE2 and 0 == self._user_manager.get_vice_admin_user_key():
					self._be_admin_type = self.ADMIN_TYPE_VICE
			elif msg_TLV.TL.Tag != TAG_ID.TAG_MSG_BEGIN and msg_TLV.TL.Tag != TAG_ID.TAG_MSG_END:
				logger.warning('unknown Tag:0x%x Len:%d in ID_LOGOFF\n'%(msg_TLV.TL.Tag,msg_TLV.TL.Len))
		elif msg_header.ID == MSG_ID.ID_AUTH_USER_LIST:
			self._any_admin_alive     = True
			self._user_list_got       = True
			if msg_TLV.TL.Tag == TAG_ID.TAG_USER_INFO:
				self._login_status = self.LOGIN_REPLY_GET
				if msg_TLV.Addr in self._cur_user_id_list:
					self._myself_in_list = True
					#update current(myself) Addr
					self._cur_user_info.Addr = msg_TLV.Addr
				elif 0 == msg_TLV.Addr:
					msg_TLV.Addr = msg_header.SrcIP #update the sender Addr
					
				self._user_manager.update_user(msg_TLV.Addr,msg_TLV)
			elif msg_TLV.TL.Tag == TAG_ID.TAG_USER_LIST:
				self._login_status = self.LOGIN_REPLY_GET
				self._user_manager.set_admin_user(msg_header.SrcIP)
				self._user_manager.set_vice_admin_user(msg_TLV.AdminIndex)
				self._user_manager.set_vice2_admin_user(msg_TLV.SecondIndex)
				if msg_TLV.UserCount < self._user_manager.get_user_num():
					logger.warning('UserCount Less than current: %d < %d\n'%(msg_TLV.UserCount,self._user_manager.get_user_num()))
				if msg_TLV.AdminIndex in self._cur_user_id_list:
					self._be_admin_type = self.ADMIN_TYPE_VICE
				elif msg_TLV.SecondIndex in self._cur_user_id_list:
					self._be_admin_type = self.ADMIN_TYPE_VICE2
				else:
					self._be_admin_type = self.ADMIN_TYPE_NONE
			elif msg_TLV.TL.Tag == TAG_ID.TAG_MSG_BEGIN:
				self._myself_in_list = False
			elif msg_TLV.TL.Tag == TAG_ID.TAG_MSG_END:
				if self._myself_in_list is True:
					self._login_status = self.LOGIN_OK
				else:
					logger.warning('myself(%s) is not in the auth userlist!'%self._cur_user_id_list)
					relogin_timer_ms = (10 + self._get_current_user_seq()) % self._T_login
					if self._not_inlist_login_timer is None:
						if self.__root is not None:
							self._not_inlist_login_timer = self.__root.after(relogin_timer_ms, lambda args=(relogin_timer_ms,):self.not_inlist_relogin(args))
						else:
							self._not_inlist_login_timer = threading_timer(relogin_timer_ms/1000, self.not_inlist_relogin, (self.relogin_timer_ms,))
							self._not_inlist_login_timer.start()
			elif msg_TLV.TL.Tag != TAG_ID.TAG_MSG_BEGIN and msg_TLV.TL.Tag != TAG_ID.TAG_MSG_END:
				logger.warning('unknown Tag:0x%x Len:%d in ID_AUTH_USER_LIST\n'%(msg_TLV.TL.Tag,msg_TLV.TL.Len))
		elif msg_header.ID == MSG_ID.ID_AUTH_CONTEST_START:
			#try contest admin
			if msg_TLV.TL.Tag == TAG_ID.TAG_ADMIN_CONTEST and self._admin_contest_timer is None:
				self._admin_contest_ok = False
				if self.__root is not None:
					self._admin_contest_timer = self.__root.after(self._get_admin_contest_time(), lambda args=(self.ADMIN_TYPE_VICE,):self.try_contest_admin(args))
				else:
					self._admin_contest_timer = threading_timer(self._get_admin_contest_time()/1000, self.try_contest_admin, (self.ADMIN_TYPE_VICE,))
					self._admin_contest_timer.start()
			else:
				logger.warning('unknown Tag:0x%x Len:%d in ID_AUTH_CONTEST_START\n'%(msg_TLV.TL.Tag,msg_TLV.TL.Len))
		elif msg_header.ID == MSG_ID.ID_ADMIN_CONTEST_REPLY:
			self._admin_contest_ok = True
		elif msg_TLV.TL.Tag != TAG_ID.TAG_MSG_BEGIN and msg_TLV.TL.Tag != TAG_ID.TAG_MSG_END:
			logger.warning('unknown Msg ID:0x%x Tag:0x%x Len:%d\n'%(msg_header.ID,msg_TLV.TL.Tag,msg_TLV.TL.Len))
		
		return ret_str_val
		
if __name__ == "__main__":
	#init sched module scheduler class
	#s = sched.scheduler(time.time,time.sleep)
	#set two schedule
	#s.enter(1,2,event_func,("Small event.",))
	#s.enter(2,1,event_func,("Big event.",))
	#s.run()
	#while True:
	#    time.sleep(100)
	import time
	from send_recv import *
	import getpass
	user_name = getpass.getuser()
	socket_u = socket_manager(logger)
	manager_u = user_manager(logger)
	manager_m = multicast_manager(logger)
	manager_m.set_send_function(socket_u.do_send)
	socket_u.start_run(manager_m.multicast_receive)
	
	user = UserManager(manager_u,manager_m)
	user_key_list = socket_u.get_own_addr_hash_list()
	user.set_current_user(user_key_list, user_name, 30000)
	user.start_login(user_name,True)
	while True:
		time.sleep(1)
		t = raw_input('Select: U: getUserList, C:getUserCount, M:getAdmin Q:quit\n')
		print ('GET INPUT [%s]\n'%t)
		if t == 'Q':
			user.start_logoff()
			socket_u.stop_run()
			break
		elif t == 'U':
			print (manager_u.get_user())
			print (user.get_user_list())
		elif t == 'C':
			print ('count:%d\n'%manager_u.get_user_num())
		elif t == 'M':
			print ('admin index:(%d,%d)\n'%(manager_u.get_admin_user_index(), manager_u.get_vice_admin_user_index()))
		