#!/usr/bin/python
# -*- coding= utf-8 -*-

import asyncio

class CommWorkDataPro():
	def __init__(self):
		self._event_loop_thread = None
		self._callback = {"timer":None}
		self._local_echo = False
		self._show_timestamp = False
		self._flow_ctrl_count = 0
		self._auto_send = False
		self._cmd_list = []
		self._time_interval = 0.08
	def set_callback(self,type,callback=None):
		if type and callback and type in self._callback:
			self._callback[type] = callback
	def set_cmd_list(self,cmd_list,time_interval_ms,auto_send,_encoding="utf-8"):
		if isinstance(cmd_list,list) and cmd_list:
			self._cmd_list = cmd_list
			for cmd_idx,cmd_ctx in enumerate(cmd_list):
				real_send_bytes = cmd_ctx['text']
				self._cmd_list[cmd_idx]['text'] = real_send_bytes
		if time_interval_ms > 0:
			self._time_interval = time_interval_ms / 1000.0
		else:
			self._time_interval = self.__time_interval_default
		self._auto_send = True if auto_send else False
	def auto_send_from_cmd_list(self,port_name,cmd_idx,new_cmd_data=None):
		_encoding="utf-8"
		if cmd_idx < len(self._cmd_list) and 'text' in self._cmd_list[cmd_idx]:
			if new_cmd_data is not None:
				real_send_bytes = bytes(new_cmd_data,_encoding)
				self._cmd_list[cmd_idx]['text'] = real_send_bytes
			to_send_data = self._cmd_list[cmd_idx]['text']
			return self.send_data(port_name,to_send_data,0)
		return None
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
	def set_flow_ctrl(self,ctrl_count):
		self._flow_ctrl_count = ctrl_count
	def timer_timeout_proc(self,timer_id,timer_len):
		if 'timer' in self._callback and self._callback['timer']:
			self._callback['timer'](timer_id, timer_len)
	def start_timer(self,timer_id,timer_len):
		return self._event_loop_thread.start_timer(timer_id,timer_len)
	def modify_timer(self,timer_id,timer_len):
		return self._event_loop_thread.modify_timer(timer_id,timer_len)
	def stop_timer(self,timer_id):
		return self._event_loop_thread.stop_timer(timer_id)
		

if __name__ == '__main__':
	print ('')