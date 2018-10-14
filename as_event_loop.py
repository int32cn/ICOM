#!/usr/bin/python
# -*- coding= utf-8 -*-

import asyncio
from concurrent.futures import Future
import functools
from threading import Thread, current_thread, Event

class EventLoopThread(Thread):
	def __init__(self, start_event,msg_proc=None):
		Thread.__init__(self)
		self.loop = None
		self.tid = None
		self.event = start_event
		self.msg_Q = None
		self.__srv_timers = {}
		self.__msg_callback = None
		self.__callback = {'msg':None,'timer':None}
		if msg_proc:
			self.__process_msg = msg_proc
		else:
			self.__process_msg = self.process_msg
	def run(self):
		self.loop = asyncio.new_event_loop()
		asyncio.set_event_loop(self.loop)
		self.tid = current_thread()
		self.msg_Q = asyncio.Queue()
		msg_task = self.loop.create_task(self.__process_msg())
		self.loop.call_soon(self.event.set)
		try:
			self.loop.run_until_complete(msg_task)
		except Exception as e:
			print ('msg task %s'%e)
			self.loop.stop()
			pass
		print ('run complete')
	def stop(self):
		self.loop.call_soon_threadsafe(self.loop.stop)
	
	def add_task(self, coro):
		"""this method should return a task object, that I
		  can cancel, not a handle"""
		def _async_add(func, fut):
			try:
				ret = func()
				fut.set_result(ret)
			except Exception as e:
				fut.set_exception(e)
		

		if current_thread() == self.tid:
			print("run self thread", coro);
			return asyncio.create_task(coro) # We can call directly if we're not going between threads.
		else:
			# We're in a non-event loop thread so we use a Future
			# to get the task from the event loop thread once
			# it's ready.
			f = functools.partial(asyncio.create_task, coro)
			fut = Future()
			#print("run other thread", coro);
			self.loop.call_soon_threadsafe(_async_add, f, fut)
			return fut.result()
	
	def call_later_safe(self,callback,*para):
		if current_thread() == self.tid:
			self.loop.call_soon(callback, *para)
		else:
			self.loop.call_soon_threadsafe(callback, *para)
		
	@asyncio.coroutine
	def process_msg(self):
		while True:
			msg = yield from self.msg_Q.get()
			#print('msg=====',msg)
			
			if self.__callback['msg']:
				self.__callback['msg'](msg)
			self.msg_Q.task_done()
			if msg == 'QUIT':
				break;
	
	def send_msg(self,*msg):
		if self.isAlive():
			return self.add_task(self.msg_Q.put(*msg))
		return None
	def cancel_task(self, task):
		self.loop.call_soon_threadsafe(task.cancel)
	
	def set_callback(self,type,callback=None):
		if callback and type in self.__callback:
			self.__callback[type] = callback
	def timer_timeout_proc(self,timer_len):
		if self.__callback['timer']:
			for timer_id in self.__srv_timers:
				if self.__srv_timers[timer_id] is not None: 
					self.__callback['timer'](timer_id,timer_len)
	@asyncio.coroutine
	def __timer_task_coro(self,timer_len):
		if timer_len <= 0:
			return
		while True:
			yield from asyncio.sleep(timer_len)
			if self.timer_timeout_proc:
				self.timer_timeout_proc(timer_len)
	def start_timer(self,timer_id,timer_len):
		if timer_id not in self.__srv_timers or self.__srv_timers[timer_id] is None:
			self.__srv_timers[timer_id] = self.add_task(self.__timer_task_coro(timer_len))
		return
	def modify_timer(self,timer_id,timer_len):
		if timer_id in self.__srv_timers and self.__srv_timers[timer_id] is not None:
			timer_task_coro = self.__srv_timers[timer_id]
			self.__srv_timers[timer_id] = None
			self.cancel_task(timer_task_coro)
			self.__srv_timers[timer_id] = self.add_task(self.__timer_task_coro(timer_len))
		return
	def stop_timer(self,timer_id):
		if timer_id in self.__srv_timers and self.__srv_timers[timer_id] is not None:
			timer_task_coro = self.__srv_timers[timer_id]
			self.__srv_timers[timer_id] = None
			self.cancel_task(timer_task_coro)
			if 'timer' in self.__callback and self.__callback['timer']:
				self.__callback['timer'](timer_id,{},0)#timer_length is 0 means timer stoped
		return

@asyncio.coroutine
def test(v):
	while True:
		print("running",v)
		yield from asyncio.sleep(v)

@asyncio.coroutine
def test2(v):
	while True:
		print("running21",v)
		yield 
		yield from asyncio.sleep(v)
		print("running22",v)
		yield 
		yield from asyncio.sleep(v)

if __name__ == '__main__':
	event = Event()
	event_loop_thread = EventLoopThread(event)
	event_loop_thread.setDaemon(True)
	event_loop_thread.start()
	
	event.wait() # Let the loop's thread signal us, rather than sleeping
	def msg_callback(msg):
		print("get: %s"%msg)
	event_loop_thread.set_callback('msg',msg_callback)
	timer_t = event_loop_thread.add_task(test(3)) # This is a real task
	timer_t2 = event_loop_thread.add_task(test2(1))
	
	srv = None
	while True:
		x = input('>>')
		if x == 'Q':
			break
		else:
			print ('put',x)
			#send_msg_to_Q(event_loop_thread.msg_Q,x)
			event_loop_thread.send_msg(x)
			print ('put',x,'ok')
			#event_loop_thread.add_task(send_msg_to_Q(b.msg_Q,x))
	
	print (asyncio.Task.all_tasks(event_loop_thread.loop))
	for _task in asyncio.Task.all_tasks(event_loop_thread.loop):
		_task.cancel()
	#time.sleep(1)
	print(asyncio.Task.all_tasks(event_loop_thread.loop))
	event_loop_thread.stop()