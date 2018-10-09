#!/usr/bin/python
# -*- coding= utf-8 -*-

from icom_ctrl_msg_id import *


class flow_ctrl():
	SYNC_MSG_TIMER_ID = 1
	DEFAULT_SYNC_MSG_TIMER_LEN = 1
	in_flow_ctrl_state = False
	current_timer_len = 1
	pftimer_func = None
	timer_running = False
	pfflowctrl_func = None
	GUI_STATE_INIT = 30
	GUI_STATE_FOCUS = 40
	GUI_STATE_ZOOMED = 35
	GUI_STATE_NORMAL = 30
	GUI_STATE_ICON = 10
	GUI_STATE_HIDE = 9
	GUI_STATE_OTHER = 8
	HOLD_DIVIDE = 4
	def __init__(self,tid=None):
		self.__gui_state = flow_ctrl.GUI_STATE_NORMAL
		self.__hold_rate = flow_ctrl.GUI_STATE_NORMAL
		self.__ctrl_min_rate = self.__hold_rate*(flow_ctrl.HOLD_DIVIDE+1)//flow_ctrl.HOLD_DIVIDE if self.__hold_rate > 16 else self.__hold_rate *2
		self.__last_ctrl_time_slips = 10
		self.__last_flow_ctrl = flow_ctrl.HOLD_DIVIDE
		self.pingpong_thresthold = self.__hold_rate//flow_ctrl.HOLD_DIVIDE
		self.current_msg_rate = 0
		self.real_data_msg_rate = 0
		self.history_msg_rate = 0
		self.sync_msg_count = 0
		self.__sync_msg_resize_count = 0
		self.in_flow_ctrl_state = False
		self.current_timer_len = flow_ctrl.DEFAULT_SYNC_MSG_TIMER_LEN
		self.__speed_too_high_step = 100
		self.__flow_ctrl_send = 0
		self.__flow_ctrl_cnf = 0
		self.__flow_ctrl_enable = False
		self.__tid = tid
		flow_ctrl.SYNC_MSG_TIMER_ID = ICOM_TIMER.ID_FLOW_CTRL
	def set_gui_state(self,ui_state):
		if ui_state > 0 and ui_state != self.__gui_state:
			self.__gui_state = ui_state
			self.__hold_rate = ui_state
			self.__ctrl_min_rate = self.__hold_rate*(flow_ctrl.HOLD_DIVIDE+1)//flow_ctrl.HOLD_DIVIDE if self.__hold_rate > 16 else self.__hold_rate *2
			self.pingpong_thresthold = self.__hold_rate//flow_ctrl.HOLD_DIVIDE
	def set_enable(self, enable):
		self.__flow_ctrl_enable = True if enable else False
	def set_timer_req_function(self,pftimer_func):
		self.pftimer_func = pftimer_func
	def set_flow_ctrl_req_function(self,pfflowctrl_func):
		self.pfflowctrl_func = pfflowctrl_func
	def send_flow_ctrl_req(self,ctrl_msg_count):
		if self.pfflowctrl_func and self.__flow_ctrl_enable is True:
			self.__flow_ctrl_send += 1
			self.pfflowctrl_func('FLOW-CTRL',ctrl_msg_count)
	def start_flow_ctrl_timer(self):
		if self.pftimer_func and self.__flow_ctrl_enable is True:
			flow_ctrl.timer_running = True
			self.pftimer_func('START-TIMER',flow_ctrl.SYNC_MSG_TIMER_ID,self.current_timer_len)
	def modify_flow_ctrl_timer(self,timer_len):
		if flow_ctrl.timer_running is True and self.pftimer_func:
			self.current_timer_len = timer_len
			self.pftimer_func('MODIFY-TIMER',flow_ctrl.SYNC_MSG_TIMER_ID,self.current_timer_len)
	def stop_flow_ctrl_timer(self):
		if self.pftimer_func and self.__flow_ctrl_enable is True:
			flow_ctrl.timer_running = False
			self.pftimer_func('STOP-TIMER',flow_ctrl.SYNC_MSG_TIMER_ID)
		self.current_timer_len = flow_ctrl.DEFAULT_SYNC_MSG_TIMER_LEN
	def start_ctrl(self,port_name):
		if flow_ctrl.timer_running is False and self.__flow_ctrl_enable is True:
			self.start_flow_ctrl_timer()
	def stop_ctrl(self,port_name):
		if 'PORTS-ALL-CLOSE' == port_name and self.__flow_ctrl_enable is True:
			if flow_ctrl.timer_running is True:
				self.stop_flow_ctrl_timer()
				self.__flow_ctrl_cnf = self.__flow_ctrl_send = 0
	def get_flow_ctrl_info(self):
		return (self.in_flow_ctrl_state,self.current_msg_rate,self.real_data_msg_rate,self.sync_msg_count,self.current_timer_len if flow_ctrl.timer_running else 0)
	def process_flow_ctrl(self,msg_int_type, msg_int_param1, msg_int_param2, msg_int_param3, msg_int_param4):
		need_continue_process = True
		if ICOM_CTRL_MSG.ID_PROC_DATA_MSG == msg_int_type:
			self.sync_msg_count += 1
			self.__sync_msg_resize_count += msg_int_param1
			if self.__flow_ctrl_enable is False:
				pass
			elif flow_ctrl.timer_running is False and self.sync_msg_count >= self.__ctrl_min_rate * flow_ctrl.HOLD_DIVIDE:
				self.start_flow_ctrl_timer()
				self.sync_msg_count = 0
				self.__sync_msg_resize_count = 0
			elif self.in_flow_ctrl_state is True or self.sync_msg_count <= self.__ctrl_min_rate:
				pass
			elif self.current_timer_len >= 2:
				self.modify_flow_ctrl_timer(1)
				self.current_timer_len = 1
			elif self.sync_msg_count > self.__hold_rate * 10:
				new_flow_ctrl = self.sync_msg_count * self.__speed_too_high_step * flow_ctrl.HOLD_DIVIDE//self.__hold_rate
				if new_flow_ctrl >= self.__last_flow_ctrl + self.__speed_too_high_step and self.__flow_ctrl_cnf >= self.__flow_ctrl_send:
					self.send_flow_ctrl_req(new_flow_ctrl)
					self.__last_flow_ctrl = new_flow_ctrl
					if self.__speed_too_high_step < 10240:
						self.__speed_too_high_step *= 2
				
				if self.sync_msg_count % new_flow_ctrl != 0:
					need_continue_process = False
				print ('ID:%d,hispeed:%d,%d,%d,%s, %d,%d'%(self.__tid,self.__speed_too_high_step,self.sync_msg_count,new_flow_ctrl,need_continue_process,msg_int_param1,msg_int_param2))
		elif ICOM_CTRL_MSG.ID_SEND_DATA_CNF_OK == msg_int_type:
			self.sync_msg_count += 1
			self.__sync_msg_resize_count += msg_int_param1
		elif ICOM_CTRL_MSG.ID_FORCE_SYNC_MSG == msg_int_type:
			self.sync_msg_count += 1
			self.__sync_msg_resize_count += msg_int_param1
		elif ICOM_CTRL_MSG.ID_FLOW_CTRL_CNF == msg_int_type:
			self.__flow_ctrl_cnf += 1
			self.in_flow_ctrl_state = True if msg_int_param1 > flow_ctrl.HOLD_DIVIDE else False
			if self.__flow_ctrl_cnf >= self.__flow_ctrl_send >= 1000:
				self.__flow_ctrl_cnf = self.__flow_ctrl_send = 0
		elif ICOM_CTRL_MSG.ID_TIMER_TIMEOUT == msg_int_type:
			if isinstance(msg_int_param2,int) and msg_int_param2 > 0:
				self.current_timer_len = msg_int_param2
				flow_ctrl.timer_running = True
			else:#timer stoped
				self.current_timer_len = flow_ctrl.DEFAULT_SYNC_MSG_TIMER_LEN
				self.__last_flow_ctrl = flow_ctrl.HOLD_DIVIDE
				self.send_flow_ctrl_req(0)
			self.current_msg_rate  = (self.sync_msg_count + self.current_timer_len//2) // self.current_timer_len
			self.history_msg_rate = (self.history_msg_rate  * 8 + self.current_msg_rate*2) // 10
			self.real_data_msg_rate = (self.__sync_msg_resize_count//flow_ctrl.HOLD_DIVIDE + self.current_timer_len//2) // self.current_timer_len
			self.__last_ctrl_time_slips += self.current_timer_len
			
			need_continue_process = True if (self.sync_msg_count > 0 or self.history_msg_rate > 0) else False
			
			if self.__flow_ctrl_enable is False:
				pass
			elif self.__last_ctrl_time_slips > 5 and self.__flow_ctrl_cnf >= self.__flow_ctrl_send:
				do_flow_ctrl = False
				new_flow_ctrl = self.__sync_msg_resize_count//(self.current_timer_len*self.__hold_rate)
				#print ('ID:%d rate cur:%d his:%d rel:%d new:%d lst:%d'%(self.__tid, self.current_msg_rate,self.history_msg_rate,self.real_data_msg_rate,new_flow_ctrl,self.__last_flow_ctrl))
				if new_flow_ctrl != self.__last_flow_ctrl:
					if self.in_flow_ctrl_state is True:
						if not (self.__hold_rate - self.pingpong_thresthold < self.current_msg_rate < self.__hold_rate + self.pingpong_thresthold):
							do_flow_ctrl = True
					elif self.current_msg_rate > (self.__ctrl_min_rate + self.pingpong_thresthold) and self.history_msg_rate >= self.__ctrl_min_rate:
						do_flow_ctrl = True
						
					if do_flow_ctrl is True:
						print ('ID:%d rate cur:%d his:%d rel:%d cnt:%d t:%d h:%d,lctrl:%d,nctrl:%d(%s)'%(self.__tid,self.current_msg_rate,self.history_msg_rate,self.real_data_msg_rate,self.sync_msg_count,
								self.current_timer_len,self.__hold_rate,self.__last_flow_ctrl,new_flow_ctrl,do_flow_ctrl))
						self.__last_flow_ctrl = new_flow_ctrl
						self.send_flow_ctrl_req(new_flow_ctrl)
						self.__last_ctrl_time_slips = 0
			
			if self.__flow_ctrl_enable is False or flow_ctrl.timer_running is False:
				pass
			elif self.current_msg_rate <= 2 and self.history_msg_rate <= 3:#add timer length
				self.__speed_too_high_step = 100
				#reset timer length
				if self.current_timer_len < 8:
					if self.sync_msg_count <= 1:
						self.modify_flow_ctrl_timer(self.current_timer_len + self.current_timer_len)
					elif self.current_timer_len >= 5:
						self.modify_flow_ctrl_timer(self.current_timer_len + 2)
					else:
						self.modify_flow_ctrl_timer(self.current_timer_len + 1)
			elif self.current_timer_len > 1:#minus timer length
				if self.current_msg_rate > 8:
					self.modify_flow_ctrl_timer((self.current_timer_len + 3) // 4)
				else:
					self.modify_flow_ctrl_timer((self.current_timer_len + 1) // 2)
			
			self.sync_msg_count = 0
			self.__sync_msg_resize_count = 0
		else:
			self.sync_msg_count += 1
		
		return need_continue_process
