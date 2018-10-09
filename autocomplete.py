try:
	import tkinter as Tkinter
	from tkinter import ttk
except:
	import Tkinter
	import ttk

class AutocomplteInput():
	def bind_auto_key_event(self):
		self.bind('<KeyRelease>', self.handle_keyrelease)
		self.bind('<KeyPress>', self.handle_keypress)
		self._completion_list = []
		self._snd_completion_list = []
		self._third_completion_list = []
		self._input_hex_mode = False
	def set_completion_list(self, completion_list):
		"""Use our completion list as our drop down selection menu, arrows move through menu."""
		self._completion_list = completion_list #sorted(completion_list, key=str.lower) # Work with a sorted list
		self._hits = []
		self._hit_index = 0
		self.position = 0
		#self['values'] = self._completion_list  # Setup our popup menu
	def set_snd_completion_list(self, completion_list):
		self._snd_completion_list = completion_list
		
	def set_third_completion_list(self, completion_list):
		self._third_completion_list = completion_list
		
	def set_input_hex_mode(self,hexMode=None,sep_char=r' '):
		"""set to hex input mode"""
		self._input_hex_mode = hexMode
		self._hex_mode_sep_char = sep_char
		
	def autocomplete(self, delta=0):
		"""autocomplete the Combobox, delta may be 0/1/-1 to cycle through possible hits"""
		#print 'auto preest',self.selection_present()
		if self._input_hex_mode is True:
			return
		if 0 == delta and self.selection_present():
			return
		if self.selection_present():
			total_val = self.get().lower()
			select_str =  self.selection_get()
			current_val_len = len(total_val) - len(select_str)
			current_val = total_val[0:current_val_len]
			self.delete(current_val_len, Tkinter.END) # need to delete selection
		else:
			current_val = self.get().lower()
			current_val_len = len(current_val)
		
		# collect hits
		#print 'get',current_val,current_val_len
		_hits = []
		_be_hits = False
		for element in self._completion_list:
			if element.lower().startswith(current_val): # Match case insensitively
				_hits.append(element)
				_be_hits = True
		if _be_hits is False:
			for element in self._snd_completion_list:
				if element.lower().startswith(current_val): # Match case insensitively
					_hits.append(element)
					_be_hits = True
					if delta >=0 and len(_hits) > delta:
						break
		if _be_hits is False:
			for element in self._third_completion_list:
				if element.lower().startswith(current_val): # Match case insensitively
					_hits.append(element)
					_be_hits = True
					if delta >=0 and len(_hits) > delta:
						break
		# if we have a new hit list, keep this in mind
		if _hits != self._hits:
			self._hit_index = 0
			self._hits=_hits
		# only allow cycling if we are in a known hit list
		if _hits == self._hits and self._hits:
			self._hit_index = (self._hit_index + delta + len(self._hits)) % len(self._hits)
		# now finally perform the auto completion
		if self._hits:
			self.insert(current_val_len,self._hits[self._hit_index][current_val_len:])
			self.select_range(current_val_len,Tkinter.END)
	
	def handle_keypress(self, event):
		"""event handler for the keypress event on this widget"""
		#print 'p',self.get(),len(event.keysym),len(event.char),'C:',event.char
		steps = 0
		if len(event.keysym) == 1 and len(event.char) == 1 and self.selection_present():
			select_str =  self.selection_get()
			steps = 1
			if event.char.lower() == select_str[0].lower():
				steps = 2
				select_start_idx = len(self.get()) - len(select_str)
				self.selection_clear()
				#letter case difference
				if event.char != select_str[0]:
					self.delete(select_start_idx,select_start_idx+1)
					self.insert(select_start_idx,event.char)
				self.select_range(select_start_idx+1,Tkinter.END)
				return 'break'
		#print ('steps',steps,event.keysym)
	def __check_be_hex_mode_valid_char(self,char_chr):
		if char_chr >= '0' and char_chr <= '9':
			return True
		if char_chr >= 'A' and char_chr <= 'F':
			return True
		if char_chr >= 'a' and char_chr <= 'f':
			return True
		return False
	def __check_be_hex_mode_input(self,event):
		string_input = self.get()
		string_output = ''
		count = 0
		char_index = 0
		cur_insert = self.index(Tkinter.INSERT)
		for _ChrCode in string_input:
			char_index += 1
			if self._hex_mode_sep_char == _ChrCode:
				count = 0
				string_output += _ChrCode
			elif self.__check_be_hex_mode_valid_char(_ChrCode) is True:
				count += 1
				if count > 4:
					count = 0
					string_output += self._hex_mode_sep_char
					if char_index == cur_insert:
						cur_insert += 1
				string_output += _ChrCode
		self.set(string_output)
		self.icursor(cur_insert)
	def handle_keyrelease(self, event):
		"""event handler for the keyrelease event on this widget"""
		if self._input_hex_mode is True:
			self.__check_be_hex_mode_input(event)
			return
		if len(event.keysym) == 1 or event.keysym == 'Shift_L' or event.char in ['.',r'/','=',",",'"']:
			self.autocomplete(0)

class AutocompleteEntry(Tkinter.Entry,AutocomplteInput):
	def test(self):
		print ('test AutocompleteEntry')

class AutocompleteCombobox(ttk.Combobox,AutocomplteInput):
	def test(self):
		print ('test AutocompleteCombobox')
	def bind_auto_key_event(self):
		self.__cur_show_history_idx = 0
		AutocomplteInput.bind_auto_key_event(self);
		self.bind('<Up>', self.handle_keyUp)
	def handle_keyUp(self, event):
		_value_list = self['values']
		_value_list_len = len(_value_list)
		if _value_list_len > 0:
			self.__cur_show_history_idx = (self.__cur_show_history_idx + 1) % _value_list_len
			self.set(_value_list[self.__cur_show_history_idx])
		