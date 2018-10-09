import shlex, subprocess
import threading
import time
import ctypes
import os
from select import *
#import commands

class dos_ops:
	def __init__(self):
		self.__subp_args = {}
		self.__ringbuffer_len = 8192
		self.__read_callback = None
		self.__thread = None
		self.__thread_args = {}
	def port_thread(self,h,xargs={}):
			thread_quit = False
			while thread_quit is not True:
				for key_name, subp in self.__subp_args.items():
					#print 'i',key_name,subp['handle'],h,xargs
					subp_handle = subp['handle']
					#if subp_handle.poll() is None:
					#	print 'continue'
					#	continue
					
					try:
						in_len = 100 
						for in_data in iter(subp_handle.stdout.readline, b''):
							#in_data = subp_handle.stdout.readline()
							self.port_readcallback(key_name, subp, (in_data,''))
							
					except:
						print ('error hanppens')
						pass
					#print 'q',self.__thread_args['quit']
					if self.__thread_args.has_key('quit') and self.__thread_args['quit'] is True:
						#subp_handle.close()
						print ('thread quit','=='*20)
						thread_quit = True
						break
			else:
				print ('quit')
			
			self.__thread = None
	def port_readcallback(self,port_name,ser_handle,data):
		#if len(data) > 0:
		#	print 'IN<<', data[0],data[1]
		if self.__subp_args.has_key(port_name):
			if None is not self.__subp_args[port_name]['read_callback']:
				desc = data[0]
				try:
					desc = data[0].decode('gbk')
				except:
					print ('unkown codec',data[0])
				try:
					self.__subp_args[port_name]['read_callback'](port_name,ser_handle,desc)
				except Exception as e:
					print ('dos callback err ',e)
					pass
	def start_port(self,port_name,command_line,rd_callback=None):
		#print ser.getSupportedBaudrates()
		self.__subp_args[port_name] = {'w':0,'r':0,'name':port_name,'read_callback':rd_callback}
		exe_args = shlex.split(command_line)
		print ('args',exe_args)
		t = subprocess.Popen(exe_args, executable=None, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, creationflags=0)
		print ('t',t)
		t.daemon = True
		self.__subp_args[port_name].setdefault('handle',t)
		
		self.__thread_args.setdefault('quit',False)
		print ('t arg',self.__thread_args)
		if self.__thread is None:
			self.__thread = threading.Thread(target=self.port_thread,args=(1,self.__thread_args))
			self.__thread.daemon = True # thread dies with the program
			self.__thread.start() 
		
		#t.start()
		
	def stop_port(self,port_name):
		print (self.__thread)
		if self.__subp_args.has_key(port_name):
			#Popen.terminate()
			self.__thread_args['quit'] = True
			self.__subp_args[port_name]['handle'].terminate()
			print ('stop poll:',self.__subp_args[port_name]['handle'].poll())
		else:
			print ('stop fail',port_name,self.__subp_args)
	def __get_out_free_buffer_size(self,port_name):
		wptr = self.__subp_args[port_name]['w']
		rptr = self.__subp_args[port_name]['r']
		free_size = 0
		if rptr <= wptr:
			free_size = self.__ringbuffer_len - wptr + rptr
		else:
			free_size = rptr - wptr
		return free_size
	
	def __get_out_data(self,port_name):
		if self.__subp_args.has_key(port_name):
			wptr = self.__subp_args[port_name]['w']
			rptr = self.__subp_args[port_name]['r']
			#print 'w,r',wptr,rptr
			if rptr == wptr:
				ret = ('',0)
			elif rptr < wptr:
				ret = (self.__subp_args[port_name].pop(rptr,''),wptr-rptr)
				self.__subp_args[port_name]['r'] = (rptr+1) % self.__ringbuffer_len
			else:
				ret = (self.__subp_args[port_name].pop(rptr,''),self.__ringbuffer_len + wptr - rptr)
				self.__subp_args[port_name]['r'] = (rptr+1) % self.__ringbuffer_len
			#print '-->w,r',wptr,rptr
			return ret
		else:
			return ('',0)
		
	def send_data(self,port_name,data,format):
		if self.__subp_args.has_key(port_name):
			#free_size = self.__get_out_free_buffer_size(port_name)
			#if free_size > 0:
			#	wptr = self.__subp_args[port_name]['w']
			#	self.__subp_args[port_name].setdefault(wptr,data)
			#	self.__subp_args[port_name]['w'] = (wptr + 1)% self.__ringbuffer_len
				
			#out_data,out_len = self.__get_out_data(port_name)
			#if out_len > 0:
			#print 'OUT>>',out_data
			out_data = data
			free_size = len(out_data)
			try:
				self.__subp_args[port_name]['handle'].stdin.write(out_data)
				return free_size
			except:
				print ('error send data',out_data)
				return None
		else:
			print (self.__subp_args)
			return None

if __name__ == '__main__':
	import sys
	port_name = 'dos'
	program_name = "cmd.exe"
	if len(sys.argv) > 1:
		program_name = sys.argv[1]
	p = dos_ops()
	def read_report(port_name,ser_handle,desc):
		print (desc)
	p.start_port(port_name, program_name, read_report)
	start_time = time.time()
	count = 1
	while 1:
		count += 1
		try:
			send_str = raw_input()
		except:
			break
		x = p.send_data(port_name, send_str+'\r\n', 1)
		if None is x:
			print ('wait')
			time.sleep(1)
		
	time.sleep(0.2)
	p.stop_port(port_name)