#!/usr/bin/python
# -*- coding= utf-8 -*-

from struct_manage import *
try:
	import tkinter as Tkinter
	from tkinter import ttk
except:
	import Tkinter
	import ttk

import binascii

ui = None
N=Tkinter.N
S=Tkinter.S
E=Tkinter.E
W=Tkinter.W

class ENVELOPE_ENUM():
	ENVELOPE_PROACTIVE               = 0xD0
	ENVELOPE_PPDOWN                  = 0xD1
	ENVELOPE_CBDOWN                  = 0xD2
	ENVELOPE_MENUSEL                 = 0xD3
	ENVELOPE_CALLCRTL                = 0xD4
	ENVELOPE_SMSCRTL                 = 0xD5
	ENVELOPE_EVENTDOWN               = 0xD6
	ENVELOPE_TIMEEXP                 = 0xD7
	ENVELOPE_RFU                     = 0xD8
	ENVELOPE_USSDDOWN                = 0xD9
	ENVELOPE_MMSTRANSTATUS           = 0xDA
	ENVELOPE_MMSNOTIFY               = 0xDB

class STK_CMD_ENUM():
	STK_NOCMDDATA                        = 0x00
	STK_REFRESH                          = 0x01
	STK_MORETIME                         = 0x02
	STK_POLLINTERVAL                     = 0x03
	STK_POLLINGOFF                       = 0x04
	STK_SETUPEVENTLIST                   = 0x05
	STK_SETUPCALL                        = 0x10
	STK_SENDSS                           = 0x11
	STK_SENDUSSD                         = 0x12
	STK_SENDSMS                          = 0x13
	STK_SENDDTMF                         = 0x14
	STK_LAUNCHBROWSER                    = 0x15
	STK_PLAYTONE                         = 0x20
	STK_DISPLAYTET                       = 0x21
	STK_GETINKEY                         = 0x22
	STK_GETINPUT                         = 0x23
	STK_SELECTITEM                       = 0x24
	STK_SETUPMENU                        = 0x25
	STK_PROVIDELOCALINFO                 = 0x26
	STK_TIMERMANAGEMENT                  = 0x27
	STK_SETUPIDLETEXT                    = 0x28
	STK_PERFORMCARDAPDU                  = 0x30
	STK_POWERONCARD                      = 0x31
	STK_POWEROFFCARD                     = 0x32
	STK_GETREADERSTATUS                  = 0x33
	STK_RUNATCOMMAND                     = 0x34
	STK_LANGUAGENOTIFICATION             = 0x35
	STK_OPENCHANNEL                      = 0x40
	STK_CLOSECHANNEL                     = 0x41
	STK_RECEIVEDATA                      = 0x42
	STK_SENDDATA                         = 0x43
	STK_GETCHANNELSTATUS                 = 0x44
	STK_SERVICESEARCH                    = 0x45
	STK_GETSERVICEINFO                   = 0x46
	STK_DECLARESERVICE                   = 0x47
	STK_SETFRAMES                        = 0x50
	STK_GETFRAMESSTATUS                  = 0x51

class STK_DATA_TAG():
	CMD_DETAILS_TAG                 = 0x01
	DEVICE_IDENTITY_TAG             = 0x02
	RESULT_TAG                      = 0x03
	DURATION_TAG                    = 0x04
	ALPHA_IDENTIFIER_TAG            = 0x05
	ADDRESS_TAG                     = 0x06
	CAP_CFG_PARA_TAG                = 0x07
	SUBADDRESS_TAG                  = 0x08
	SS_STRING_TAG                   = 0x09
	USSD_STRING_TAG                 = 0x0A
	SMS_TPDU_TAG                    = 0x0B
	CELL_BROADCAST_PAGE_TAG         = 0x0C
	TEXT_STRING_TAG                 = 0x0D
	TONE_TAG                        = 0x0E
	ITEM_TAG                        = 0x0F
	ITEM_IDENTIFIER_TAG             = 0x10
	RESPONSE_LENGTH_TAG             = 0x11
	FILE_LIST_TAG                   = 0x12
	LOCATION_INFORMATION_TAG        = 0x13
	IMEI_TAG                        = 0x14
	HELP_REQUEST_TAG                = 0x15
	NET_MEASUREMENT_RESULTS_TAG     = 0x16
	DEFAULT_TEXT_TAG                = 0x17
	MS_NEXTACTION_INDICATOR_TAG     = 0x18
	EVENT_LIST_TAG                  = 0x19
	CAUSE_TAG                       = 0x1A
	LOCATION_STATUS_TAG             = 0x1B
	TRANSACTION_IDENTIFIER_TAG      = 0x1C
	BCCH_CHANNEL_LIST_TAG           = 0x1D
	ICON_IDENTIFIER_TAG             = 0x1E
	ITEM_ICONID_LIST_TAG            = 0x1F
	CARD_READER_STATUS_TAG          = 0x20
	CARD_ATR_TAG                    = 0x21
	C_APDU_TAG                      = 0x22
	R_APDU_TAG                      = 0x23
	TIMER_IDENTIFIER_TAG            = 0x24
	TIMER_VALUE_TAG                 = 0x25
	DATETIME_AND_TIMEZONE_TAG       = 0x26
	CALL_CONTROL_REQACTION_TAG      = 0x27
	AT_COMMAND_TAG                  = 0x28
	AT_RESPONSE_TAG                 = 0x29
	BC_REPEAT_INDICATOR_TAG         = 0x2A
	IMMEDIATE_RESPONSE_TAG          = 0x2B
	DTMF_STRING_TAG                 = 0x2C
	LANGUAGE_TAG                    = 0x2D
	TIMING_ADVANCE_TAG              = 0x2E
	AID_TAG                         = 0x2F
	BROWSER_IDENTITY_TAG            = 0x30
	URL_TAG                         = 0x31
	BEARER_TAG                      = 0x32
	PROVISIONING_REFFILE_TAG        = 0x33
	BROWSER_TERMINATION_CAUSE_TAG   = 0x34
	BEARER_DESCRIPTION_TAG          = 0x35
	CHANNEL_DATA_TAG                = 0x36
	CHANNEL_DATA_LENGTH_TAG         = 0x37
	CHANNEL_STATUS_TAG              = 0x38
	BUFFER_SIZE_TAG                 = 0x39
	CARD_READER_IDENTIFIER_TAG      = 0x3A
	RFU_3B                          = 0x3B
	TERMINAL_TRAN_LEVEL_TAG         = 0x3C
	RFU_3D                          = 0x3D
	OTHER_ADDR_TAG                  = 0x3E
	ACCESS_TECHNOLOGY_TAG           = 0x3F
	DISPLAY_PARAMETERS_TAG          = 0x40
	SERVICE_RECORD_TAG              = 0x41
	DEVICE_FILTER_TAG               = 0x42
	SERVICE_SEARCH_TAG              = 0x43
	ATTRIBUTE_INFORMATION_TAG       = 0x44
	SERVICE_AVAILABILITY_TAG        = 0x45
	ESN_TAG                         = 0x46
	NETWORK_ACCESS_NAME_TAG         = 0x47
	CDMA_SMS_TPDU                   = 0x48
	REMOTE_ENTITY_ADDRESS_TAG       = 0x49
	I_WLAN_ID_TAG                   = 0x4A
	I_WLAN_ACCESS_STATUS_TAG        = 0x4B
	RFU_4C                          = 0x4C
	RFU_4D                          = 0x4D
	RFU_4E                          = 0x4E
	RFU_4F                          = 0x4F
	TEXT_ATTRIBUTE_TAG              = 0x50
	ITEM_TEXT_ATTRIBUTE_LIST_TAG    = 0x51
	PDP_CONTEXT_ACTIVATION_PAR_TAG  = 0x52
	RFU_53                          = 0x53
	RFU_54                          = 0x54
	CSG_CELL_SELEC_STATUS_TAG       = 0x55
	CSG_ID_TAG                      = 0x56
	HNB_NAME_TAG                    = 0x57
	RFU_58                          = 0x58
	RFU_59                          = 0x59
	RFU_5A                          = 0x5A
	RFU_5B                          = 0x5B
	RFU_5C                          = 0x5C
	RFU_5D                          = 0x5D
	RFU_5E                          = 0x5E
	RFU_5F                          = 0x5F
	RFU_60                          = 0x60
	RFU_61                          = 0x61
	IMEISV_TAG                      = 0x62
	BATTERY_STATE_TAG               = 0x63
	BROWSING_STATUS_TAG             = 0x64
	NETWORK_SEARCH_MODE_TAG         = 0x65
	FRAME_LAYOUT_TAG                = 0x66
	FRAMES_INFORMATION_TAG          = 0x67
	FRAME_IDENTIFIER_TAG            = 0x68
	UTRAN_MEASUREMENT_TAG           = 0x69
	MMS_REFERENCE_TAG               = 0x6A
	MMS_IDENTIFIER_TAG              = 0x6B
	MMS_TRANSFER_STATUS_TAG         = 0x6C
	MEID_TAG                        = 0x6D
	MMS_CONTENT_ID_TAG              = 0x6E
	MMS_NOTIFICATION_TAG            = 0x6F
	LAST_ENVELOPE_TAG               = 0x70
	RFU_62                          = 0x71
	PLMNWACT_LIST_TAG               = 0x72
	ROUTING_AREA_INFO_TAG           = 0x73
	ATTACH_TYPE_TAG                 = 0x74
	REJETION_CAUSE_CODE_TAG         = 0x75
	GEOGRAPH_LOCAL_PARA_TAG         = 0x76
	GAD_SHAPES_TAG                  = 0x77
	NMEA_SENTENCE_TAG               = 0x78
	PLMN_LIST_TAG                   = 0x79
	RFU_7A                          = 0x7A
	RFU_7B                          = 0x7B
	EPSPDN_ACTIVE_PARA_TAG          = 0x7C
	TRACKING_AREA_ID_TAG            = 0x7D
	CSG_ID_LIST_TAG                 = 0x7E

def find_ID_in_class(id,class_name):
	id_name = ''
	for n,v in class_name.__dict__.items():
		if v == id:
			#print (n,v)
			id_name = n
			break
	return id_name

class T_CMD_DETAILS_TAG(ct.Structure):
	_pack_      = 1
	_fields_    = [
		('TL',				MSG_TAG_BYTE),
		('number',			ct.c_uint8),
		('type',			ct.c_uint8),
		('qual',			ct.c_uint8),
	]
	def __init__(self,tag_id):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(tag_id,ct.sizeof(EMPTY_TAG_BYTE))
	def __repr__(self):
		return '%s num:0x%02x, type:0x%02x, qual:0x%02x'%(self.TL,self.number,self.type,self.qual)

class T_TRAN_LEVEL_TAG(ct.Structure):
	_pack_      = 1
	_fields_    = [
		('TL',				MSG_TAG_BYTE),
		('protocal',		ct.c_uint8),
		('portH',			ct.c_uint8),
		('portL',			ct.c_uint8),
	]
	def __init__(self,tag_id):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(tag_id,ct.sizeof(EMPTY_TAG_BYTE))
	def __repr__(self):
		return '%s num:0x%02x, protocal:0x%02x, port:0x%02x'%(self.TL,self.protocal,(self.portH<<8)+self.portL)

class T_OTHER_ADDR_TAG(ct.Structure):
	_pack_      = 1
	_fields_    = [
		('TL',				MSG_TAG_BYTE),
		('type',		    ct.c_uint8),
		('Addr',			ct.c_uint8*4),
	]
	def __init__(self,tag_id):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(tag_id,ct.sizeof(EMPTY_TAG_BYTE))
	def __repr__(self):
		return '%s type:0x%02x, addr:0x%02x'%(self.TL,self.type,self.Addr[0])

class T_NETWORK_ACCESS_NAME_TAG(ct.Structure):
	_pack_      = 1
	_fields_    = [
		('TL',				MSG_TAG_BYTE),
		('Len',				ct.c_uint8),
		('Apn',				ct.c_uint8*1),
	]
	def __init__(self,tag_id):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(tag_id,ct.sizeof(EMPTY_TAG_BYTE))
	def __repr__(self):
		return '%s ApnLen:0x%02x, Apn0:0x%02x'%(self.TL,self.Len,self.Apn[0])
	
def __message_processer(level,msg_header,tag_content,tag_content_bytes):
	#print (level,msg_header,tag_content_bytes,tag_content)
	tag_name = find_ID_in_class(tag_content.TL.Tag&0x7F,STK_DATA_TAG)
	tag_cmd_name = None
	tag_cmd_qual = None
	if tag_content.TL.Tag&0x7F == STK_DATA_TAG.CMD_DETAILS_TAG:
		tag_cmd_name = find_ID_in_class(tag_content.type,STK_CMD_ENUM)
		if tag_content.type == STK_CMD_ENUM.STK_OPENCHANNEL:
			if tag_content.qual & 0x04 == 0x04:
				tag_cmd_qual = 'backgroud-link'
			elif tag_content.qual & 0x01 == 0x01:
				tag_cmd_qual = 'immediate-link'
			else:
				tag_cmd_qual = 'ondemand-link'
	elif tag_content.TL.Tag&0x7F == STK_DATA_TAG.TERMINAL_TRAN_LEVEL_TAG:
		if tag_content.protocal == 0x01:
			tag_cmd_name = 'UDP client,remote'
		elif tag_content.protocal == 0x02:
			tag_cmd_name = 'TCP client,remote'
		elif tag_content.protocal == 0x03:
			tag_cmd_name = 'TCP server'
		elif tag_content.protocal == 0x04:
			tag_cmd_name = 'UDP client,local'
		elif tag_content.protocal == 0x05:
			tag_cmd_name = 'TCP client,local'
		elif tag_content.protocal == 0x06:
			tag_cmd_name = 'direct'
		tag_cmd_qual = 'PORT:%d'%((tag_content.portH<<8)+tag_content.portL)
	elif tag_content.TL.Tag&0x7F == STK_DATA_TAG.OTHER_ADDR_TAG:
		if tag_content.type == 0x21:#ipv4
			tag_cmd_name = 'IPV4'
			tag_cmd_qual = '%d.%d.%d.%d'%(tag_content.Addr[0], tag_content.Addr[1], tag_content.Addr[2],tag_content.Addr[3])
		elif tag_content.type == 0x57:
			tag_cmd_name = 'IPV6'
		else:
			tag_cmd_name = 'IPxx'
	elif tag_content.TL.Tag&0x7F == STK_DATA_TAG.NETWORK_ACCESS_NAME_TAG:
		tag_cmd_name = tag_content_bytes[1:1+tag_content.Len]
		if not isinstance(tag_cmd_name,str):
			tag_cmd_name = tag_cmd_name.decode('utf-8')
		
	if ui is not None:
		tag_value = bytes_to_hex(tag_content_bytes) # tag_content_bytes.encode('Hex')
		if tag_cmd_qual is not None:
			ui.gui_add_tlv(level, '%s( %s %s )'%(tag_name,tag_cmd_name,tag_cmd_qual), tag_content.TL, tag_value, True)
		elif tag_cmd_name is not None:
			ui.gui_add_tlv(level, '%s( %s )'%(tag_name,tag_cmd_name), tag_content.TL, tag_value, True)
		else:
			ui.gui_add_tlv(level, '%s'%tag_name, tag_content.TL, tag_value, True)
	else:
		print ('ui none\n')
def __x_message_processer(level,msg_header,tag_TL, tag_content_bytes):
	content_len = len(tag_content_bytes)
	edit_able = True
	tag_name = None
	if level < 1:
		tag_name = find_ID_in_class(tag_TL.Tag,ENVELOPE_ENUM)
	else:
		tag_name = find_ID_in_class(tag_TL.Tag&0x7F,STK_DATA_TAG)
	
	#总的信封level 0，里面还是TLV结构
	if level < 1:
		#SIM STK里面长度0x81表示，实际长度大于x80，实际长度看下一个字
		if tag_name != '' and 0x81 == tag_TL.Len:
			if isinstance(tag_content_bytes[1],str):
				tag_TL.Len = ord(tag_content_bytes[0])
			else:
				tag_TL.Len = tag_content_bytes[0]
			tag_content_bytes = tag_content_bytes[1:]
		
		if msg_header.Tag == tag_TL.Tag and msg_header.Len == tag_TL.Len and content_len > ct.sizeof(MSG_TAG_BYTE):
			if isinstance(tag_content_bytes[1],str):
				tag_len_next = ord(tag_content_bytes[1]) #python 2.x
			else:
				tag_len_next = tag_content_bytes[1]  #python 3.x
				
			if tag_len_next + ct.sizeof(MSG_TAG_BYTE) <=  content_len:
				edit_able = False
	if ui is not None:
		tag_value = bytes_to_hex(tag_content_bytes) #tag_content_bytes.encode('Hex')
		ui.gui_add_tlv(level, tag_name, tag_TL, tag_value, edit_able)
	if edit_able is False:
		TLV_ParseAll(tag_content_bytes,level+1)
	
def TLV_ParseAll(_dec_msg_bytes,level):
	new_msg_str_list = []
	total_len,_msg = bytes_to_ctypes_array(_dec_msg_bytes)
	TL_len = ct.sizeof(MSG_TAG_BYTE)
	msg_header = stream2struct(_msg,MSG_TAG_BYTE)
	skip_len = 0
	Tag = get_next_tag_byte(_msg, 0)
	while Tag is not None:
		#print ('RECV: skip_len:%d, Tag:0x%x,Len:%d\n'%(skip_len,Tag.Tag,Tag.Len))
		tag_struct = get_tag_struct(Tag.Tag)
		if tag_struct is not None: #skip unknown structure
			tag_content = get_tag_msg(_msg,skip_len,tag_struct)
			__message_processer(level,msg_header,tag_content,_msg[skip_len+TL_len:skip_len+TL_len+Tag.Len])
		else:
			__x_message_processer(level,msg_header,Tag,_msg[skip_len+TL_len:skip_len+TL_len+Tag.Len])
		skip_len += TL_len + Tag.Len
		Tag = get_next_tag_byte(_msg, skip_len)
		
	return
	
def TLV_getFisrtTag(_dec_msg_bytes):
	total_len,_msg = bytes_to_ctypes_array(_dec_msg_bytes)
	Tag = get_next_tag_byte(_msg, 0)
	return Tag

def hex_to_str(hex_str): # '30313233' -> '\x30\x31\x32\x33' / '0123'
	_len = len(hex_str)
	if _len & 0x01 != 0:
		raise ValueError('Hex Length Error(Odd Length)')
	
	str_list = []
	i = 0;
	while i < _len:
		chr_code = int(hex_str[i:i+2],16)
		str_list.append(chr(chr_code))
		i += 2
	return "".join(str_list)
	
def hex_to_bytes(hex_str): # '30313233' -> b'\x30\x31\x32\x33'
	_len = len(hex_str)
	if _len & 0x01 != 0:
		raise ValueError('Hex Length Error(Odd Length)')
	xbytes = binascii.unhexlify(hex_str)
	
	return xbytes #hex_str.decode('Hex')

def str_to_bytes(in_str): # '30313233' -> b'\x30\x31\x32\x33'
	if not isinstance(in_str,str):
		raise ValueError('should input str type,not %s'%type(in_str))
	
	if not isinstance(in_str,bytes):
		xbytes = in_str.encode('utf-8')
	
	return xbytes #hex_str.decode('Hex')

def str_to_hex(in_str):
	if not isinstance(in_str,str):
		raise ValueError('should input str type,not %s'%type(in_str))
		
	hex_list = []
	for one_chr in in_str:
		#print ('in_str,one_chr',in_str,one_chr)
		chr_code = ord(one_chr)
		if chr_code <= 0xff:
			hex_list.append('%02X'%chr_code)
		else:
			hex_list.append('%04X'%chr_code)
		
	return "".join(hex_list)
	
def bytes_to_hex(in_bytes):
	if isinstance(in_bytes,str): #python 2.x
		return in_bytes.encode('Hex')
	if not isinstance(in_bytes,bytes):
		raise ValueError('should input bytes type,not %s'%type(in_bytes))
	
	hex_list = []
	for one_byte in in_bytes:
		hex_list.append('%02X'%one_byte)
	
	return "".join(hex_list)
	
class TLV_GUI():
	_INT_MAX = (0x7f,0x7fff,0x7fffff,0x7fffffff,0x7fffffffff,0x7fffffffffff,0x7fffffffffffff)
	def __init__(self,root=None,default_hex_data_val=None,default_cmd_description_val=None):
		self.root = root
		if self.root is None:
			self.root = Tkinter.Tk()
		self.__input_tag_err = False
		self.__input_data_err = False
		self.__data = Tkinter.StringVar(self.root)
		self.__description_widget = None
		self.__tips = Tkinter.StringVar(self.root)
		self.__init_hex_data_set = False
		self.__description_text = None
		self.__extern_hex_data_val = default_hex_data_val
		self.__extern_description_val = default_cmd_description_val
		if default_hex_data_val is not None:
			self.__data.set(default_hex_data_val.get())
			self.__init_hex_data_set = True
		else:
			self.__data.set('D0308103014003820281820500350702020405051F023902058E47080761706E2D6C74653C030208AE3E0521D30101039000')
		if self.__extern_description_val is not None:
			self.__description_text = default_cmd_description_val.get()
		self._MIN_TLV_COUNT = 8
		self._MAX_TLV_COUNT = self._MIN_TLV_COUNT
		self.__frameTLV = None
		self.__AT_Prefix = None
		self.__AT_data_quotation = None
		self.__tip_var = []
		self.__tag_var = []
		self.__len_var = []
		self.__val_var = []
		self.__tag_used = []
		self.__display_sel_var = []
		self.__display_sel_old = []
		self.__row_mask      = 1024
		self.__none_int_mask = 512
		self.__sign_mask     = 256
		self.__real_val_mask = 0xff
		self.__tlv_widget = []
		s = ttk.Style(self.root)
		s.configure('ErrInput.TEntry',
					#background='#8080FF',
					foreground='#EE0000',
					#highlightthickness='20'
					#font=('Helvetica', 10, 'normal')
					)
		s.configure('Tips.TEntry',
					#background='#8080FF',
					border=0,highlightthickness=0,relief='flat',
					takefocus=0
					#font=('Helvetica', 10, 'normal')
					)
	def gui_init(self):
		frmLoop = ttk.Frame(self.root,border=0)
		self.__frameTLV = frmLoop
		self.root.rowconfigure(2, weight=1)
		self.root.columnconfigure(1, weight=1)
		self.root.columnconfigure(2, weight=1)
		self.root.columnconfigure(3, weight=1)
		self.root.columnconfigure(4, weight=1)
		frmLoop.columnconfigure(4, weight=1)
		discription_text = Tkinter.Text(self.root, width=80, height=4)
		entry_hex = ttk.Label(self.root, text='HEX', width=4)
		data_etry = ttk.Entry(self.root, textvariable=self.__data,width=80,font=('Helvetica',10,'normal'))
		data_fmt = ttk.Button(self.root, text='#', width=1)
		de_b = ttk.Button(self.root, text='Decode', width=8)
		en_b = ttk.Button(self.root, text='Encode', width=8)
		data_fmt.bind('<Button-1>',self._fmt_change)
		en_b.bind('<Button-1>',self._encode_click)
		de_b.bind('<Button-1>',self._decode_click)
		self.__description_widget = discription_text
		discription_text.grid(row=0,column=0,columnspan=6,sticky=E+W)
		entry_hex.grid(row=1,column=0,sticky=E+W)
		data_etry.grid(row=1,column=1,columnspan=4,sticky=E+W)
		data_fmt.grid(row=1,column=5,sticky=E+W)
		de_b.grid(row=2,column=1,sticky=N+S)
		en_b.grid(row=2,column=2,sticky=N+S)
		if self.__init_hex_data_set is True:
			set_b = ttk.Button(self.root, text='Save Cmd', width=8)
			set_b.bind('<Button-1>',self._extern_val_set)
			set_b.grid(row=2,column=3,sticky=N+S)
		tip_Tag = ttk.Label(frmLoop, text='Tag', width=5)
		tip_Len = ttk.Label(frmLoop, text='Len', width=5)
		tip_Val = ttk.Label(frmLoop, text='Val', width=5)
		tip_tips= ttk.Label(frmLoop, textvariable=self.__tips)
		ckb_hex = ttk.Label(frmLoop, text='hex', width=5)
		ckb_str = ttk.Label(frmLoop, text='str', width=5)
		ckb_i8  = ttk.Label(frmLoop, text='int8', width=5)
		ckb_u8  = ttk.Label(frmLoop, text='uint8', width=5)
		ckb_i16 = ttk.Label(frmLoop, text='int16', width=5)
		ckb_u16 = ttk.Label(frmLoop, text='uint16', width=5)
		ckb_i32 = ttk.Label(frmLoop, text='int32', width=5)
		ckb_u32 = ttk.Label(frmLoop, text='uint32', width=5)
		tip_Tag.grid(row=1,column=1,sticky=S+N)
		tip_Len.grid(row=1,column=2,sticky=S+N)
		tip_Val.grid(row=1,column=3,sticky=S+N)
		tip_tips.grid(row=1,column=4,sticky=E+W)
		ckb_hex.grid(row=1,column=5,sticky=S+N)
		ckb_str.grid(row=1,column=6,sticky=S+N)
		ckb_i8.grid(row=1,column=7,sticky=S+N)
		ckb_u8.grid(row=1,column=8,sticky=S+N)
		ckb_i16.grid(row=1,column=9,sticky=S+N)
		ckb_u16.grid(row=1,column=10,sticky=S+N)
		ckb_i32.grid(row=1,column=11,sticky=S+N)
		ckb_u32.grid(row=1,column=12,sticky=S+N)
		
		if self.__description_text is not None:
			self.__description_widget.insert(Tkinter.END, self.__description_text)
		elif self.__init_hex_data_set is True:
			self.__description_widget.insert(Tkinter.END, 'Please insert command description here...')
		for i in range(0,self._MIN_TLV_COUNT):
			self._add_tlv_table(i)
		frmLoop.grid(row=3,column=0,rowspan=2,columnspan=3,sticky=E+W+S+N)
		
	def _add_tlv_table(self,_row):
		frmLoop = self.__frameTLV
		i = _row
		row_base = 2
		sign_val = self.__sign_mask
		none_int_val = self.__none_int_mask
		if frmLoop is not None:
			self.__tip_var.append(Tkinter.StringVar(self.root))
			self.__tag_var.append(Tkinter.StringVar(self.root))
			self.__len_var.append(Tkinter.StringVar(self.root))
			self.__val_var.append(Tkinter.StringVar(self.root))
			self.__display_sel_var.append(Tkinter.IntVar(self.root))
			self.__display_sel_old.append(i*self.__row_mask+self.__none_int_mask+1)
			self.__display_sel_var[i].set(self.__display_sel_old[i])
			self.__tag_used.append(0)
			self.__tlv_widget.append(None)
			
			tip_etry = ttk.Entry(frmLoop, textvariable=self.__tip_var[i],width=50,state='readonly',style='Tips.TEntry')
			tag_etry = ttk.Entry(frmLoop, textvariable=self.__tag_var[i],width=4)
			len_etry = ttk.Entry(frmLoop, textvariable=self.__len_var[i],width=4,state='readonly')
			val_etry = ttk.Entry(frmLoop, textvariable=self.__val_var[i],width=52)
			tag_etry.bind('<KeyRelease>',lambda event,_row=i:self._input_tag_validate(event,_row))
			val_etry.bind('<KeyRelease>',lambda event,_row=i:self._value_input_validate(event,_row))
			self.__tlv_widget[i] = (tag_etry,len_etry,val_etry)
			cur_row_val = i*self.__row_mask
			ckb_hex = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+none_int_val+1)
			ckb_str = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+none_int_val+2)
			ckb_i8  = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+sign_val+8)
			ckb_u8  = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+8)
			ckb_i16 = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+sign_val+16)
			ckb_u16 = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+16)
			ckb_i32 = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+sign_val+32)
			ckb_u32 = ttk.Radiobutton(frmLoop, text='', variable=self.__display_sel_var[i], value=cur_row_val+32)
			tip_etry.grid(row=i+row_base,column=0,sticky=W+E)
			tag_etry.grid(row=i+row_base,column=1,sticky=W+E)
			len_etry.grid(row=i+row_base,column=2,sticky=W+E)
			val_etry.grid(row=i+row_base,column=3,columnspan=2,sticky=E+W+S+N)
			ckb_hex.bind('<Button-1>',self._show_type_click)
			ckb_str.bind('<Button-1>',self._show_type_click)
			ckb_i8.bind('<Button-1>',self._show_type_click)
			ckb_u8.bind('<Button-1>',self._show_type_click)
			ckb_i16.bind('<Button-1>',self._show_type_click)
			ckb_u16.bind('<Button-1>',self._show_type_click)
			ckb_i32.bind('<Button-1>',self._show_type_click)
			ckb_u32.bind('<Button-1>',self._show_type_click)
			ckb_hex.grid(row=i+row_base,column=5,sticky=S+N)
			ckb_str.grid(row=i+row_base,column=6,sticky=S+N)
			ckb_i8.grid(row=i+row_base,column=7,sticky=S+N)
			ckb_u8.grid(row=i+row_base,column=8,sticky=S+N)
			ckb_i16.grid(row=i+row_base,column=9,sticky=S+N)
			ckb_u16.grid(row=i+row_base,column=10,sticky=S+N)
			ckb_i32.grid(row=i+row_base,column=11,sticky=S+N)
			ckb_u32.grid(row=i+row_base,column=12,sticky=S+N)
	def _change_display_val_to_hex(self,cur_display_val,cur_display_type):
		none_int_val = cur_display_type & self.__none_int_mask
		sign_val     = cur_display_type & self.__sign_mask
		type_val     = cur_display_type & self.__real_val_mask
		if none_int_val > 0:
			#print ('strType:%d,type:%d'%(none_int_val,type_val))
			if type_val == 1:
				cur_hex = cur_display_val.replace(' ','').replace('.','').replace(',','')
				return bytes_to_hex(hex_to_bytes(cur_hex)) #cur_hex.decode('Hex').encode('Hex')
			else:
				return str_to_hex(cur_display_val) #cur_display_val.encode('Hex')
		else:
			print ('sign:%d type:%d\n'%(sign_val,type_val))
			int_bytes    = type_val // 8
			str_list     = cur_display_val.replace('L','').split()
			i = 0
			i_list = [int(i) for i in str_list]
			u_list = []
			u_list_hex = []
			max_val = self._INT_MAX[int_bytes - 1]
			max_uint_val = (max_val+1)*2
			for i in i_list:
				new_int = i
				if sign_val > 0 and i < 0:
					new_int = i+max_uint_val
					
				if new_int > max_uint_val or new_int < 0:
					raise ValueError('value:%d outof rang:[0-%d]\n'%(new_int,max_uint_val))
				u_list.append(new_int)
			
			#print('i_list:%s\n'%i_list)
			#print('u_list:%s\n'%u_list)
			if int_bytes == 2:
				u_list_hex = ['%04x'%i for i in u_list]
			elif int_bytes == 4:
				u_list_hex = ['%08x'%i for i in u_list]
			else: #default to one byte
				u_list_hex = ['%02x'%i for i in u_list]
			
			return ''.join(u_list_hex)
			
	def _change_display_val(self,cur_display_val,cur_display_type,new_display_type):
		print (cur_display_val,cur_display_type,new_display_type)
		cur_hex = ''
		cur_hex = self._change_display_val_to_hex(cur_display_val,cur_display_type)
		print ('cur_hex:%s\n'%cur_hex)
		cur_hex_len = len(cur_hex)
		none_int_val = new_display_type & self.__none_int_mask
		sign_val     = new_display_type & self.__sign_mask
		type_val     = new_display_type & self.__real_val_mask
		if none_int_val > 0:
			print ('not int%d\n'%new_display_type)
			if type_val == 1: #hex
				return cur_hex
			else:
				return hex_to_str(cur_hex) #cur_hex.decode('Hex')
		else:
			int_bytes    = type_val // 8
			hex_bytes    = int_bytes * 2
			print ('int bytes%d\n'%int_bytes)
			if cur_hex_len % hex_bytes != 0:
				raise ValueError('Length Error (%d not times of bytes %d)'%(cur_hex_len,hex_bytes))
				return None
			u_list = []
			i = 0
			while i < cur_hex_len:
				u_list.append(int(cur_hex[i:i+hex_bytes],16))
				i += hex_bytes
			
			if sign_val > 0:
				max_val = self._INT_MAX[int_bytes - 1]
				max_minus_val = (max_val+1)*2
				print ('signed int max:%d\n'%max_val)
				i_list = []
				for i in u_list:
					if i > max_val:
						i_list.append(i-max_minus_val)
					else:
						i_list.append(i)
			else:
				i_list = u_list
			return ' '.join([repr(i) for i in i_list])
			
	def _calc_tag_val_length(self):
		if self.__input_data_err is True or self.__input_tag_err is True:
			return
		tag_count      = len(self.__val_var)
		tag_header_len = ct.sizeof(MSG_TAG_BYTE)
		total_len      = 0
		for i in range(1,tag_count):
			tag_val = self.__tag_var[i].get()
			len_val = self.__len_var[i].get()
			if tag_val != '' and len_val != '':
				total_len += tag_header_len + int(len_val,16)
			else:
				break
		if len(self.__len_var[0].get()) > 0:
			self.__len_var[0].set('0x%02x'%total_len)
	def _input_tag_validate(self,event,cur_row):
		if cur_row < len(self.__val_var):
			cur_display_val = event.widget.get()
			cur_sel = self.__display_sel_var[cur_row].get() % self.__row_mask
			try:
				tag_val =  int(cur_display_val,16)
				if event.widget['style'] != 'TEntry':
					event.widget.configure(style='TEntry')
				if len(cur_display_val) >= 2 and not cur_display_val.startswith('0x'):
					self.__tag_var[cur_row].set('0x%0x'%tag_val)
				self.__input_tag_err = False
				self._calc_tag_val_length()
			except Exception as e:
				self.__input_tag_err = True
				if event.widget['style'] != 'ErrInput.TEntry':
					event.widget.configure(style='ErrInput.TEntry')
				pass
	def _value_input_validate(self,event,cur_row):
		if cur_row < len(self.__val_var):
			cur_display_val = event.widget.get()
			cur_sel = self.__display_sel_var[cur_row].get() % self.__row_mask
			try:
				cur_hex = self._change_display_val_to_hex(cur_display_val,cur_sel)
				cur_str_len = len(cur_hex)//2
				#print (cur_display_val,cur_hex,cur_str_len,event.widget['style'])
				if event.widget['style'] != 'TEntry':
					event.widget.configure(style='TEntry')
				self.__len_var[cur_row].set('0x%02x'%cur_str_len)
				self.__input_data_err = False
				self._calc_tag_val_length()
			except Exception as e:
				print ('Input data validate error:%s\n'%e)
				self.__input_data_err = True
				if event.widget['style'] != 'ErrInput.TEntry':
					event.widget.configure(style='ErrInput.TEntry')
				pass
	def _extern_val_set(self,event):
		if self.__init_hex_data_set is True:
			if self.__extern_hex_data_val is not None:
				cmd_data = self.__data.get()
				self.__extern_hex_data_val.set(cmd_data)
			if self.__extern_description_val is not None:
				description = self.__description_widget.get(0.0, Tkinter.END)
				self.__extern_description_val.set(description)
	def _show_type_click(self,event):
		cur_val = event.widget['value']
		cur_row = cur_val // self.__row_mask
		cur_sel = cur_val % self.__row_mask
		if cur_row < len(self.__val_var):
			old_sel = self.__display_sel_old[cur_row] % self.__row_mask
			cur_display_val = self.__val_var[cur_row].get()
			try:
				display_val = self._change_display_val(cur_display_val,old_sel,cur_sel)
				self.__val_var[cur_row].set(display_val)
				self.__display_sel_old[cur_row] = cur_val
			except Exception as e:
				print ('chang val ERR:%s\n'%e)
				self.__tips.set('Error:%s'%e)
				print (cur_val,self.__display_sel_var[cur_row].get())
				#self.__display_sel_var[cur_row].set(self.__display_sel_old[cur_row])
				return 'break'
		
	def _encode_click(self,event=None):
		if self.__input_data_err is True or self.__input_tag_err is True:
			self.__tips.set('Encode Error:Tag or Data Err')
			return
		total_len = 0
		tag0_tag_val = self.__tag_var[0].get()
		tag0_len_val = self.__len_var[0].get()
		if len(tag0_tag_val) <= 0 or len(tag0_len_val) <= 0:
			self.__tips.set('Encode Error:Tag0 or Data0 Err')
			return
		tag_len    = int(tag0_len_val,16)
		total_len += ct.sizeof(MSG_TAG_BYTE) + tag_len
		buffer     = (ct.c_byte * total_len)()
		offset     = 0
		header_len = ct.sizeof(MSG_TAG_BYTE)
		for i in range(0,self._MAX_TLV_COUNT):
			tag_val = self.__tag_var[i].get()
			if len(tag_val) > 0:
				tag_int = int(tag_val,16)
				tag_len = int(self.__len_var[i].get(),16)
				_tlv_header = MSG_TAG_BYTE(tag_int,tag_len+header_len)
				ct.memmove(ct.addressof(buffer)+offset,	ct.byref(_tlv_header),	header_len)
				offset += header_len
				if 0 == i: #the first content is that all of the left tlvs
					continue
				cur_display_val = self.__val_var[i].get()
				cur_sel = self.__display_sel_var[i].get() % self.__row_mask
				#cur_val = self._change_display_val_to_hex(cur_display_val,cur_sel).decode('Hex')
				cur_val = self._change_display_val_to_hex(cur_display_val,cur_sel)
				cur_val = hex_to_bytes(cur_val)
				
				val_length,val_data = bytes_to_ctypes_array(cur_val)
				ct.memmove(ct.addressof(buffer)+offset,	ct.byref(val_data),	val_length)
				offset += tag_len
				print ('tag:%s,offset:%s\n'%(_tlv_header,offset))
		str_hex = bytes_to_hex(struct2stream(buffer))   #struct2stream(buffer).encode('HEX')
		self.__data.set(str_hex)
		self.__tips.set('Encode Successful')
	def _fmt_change(self,event):
		raw_data = self.__data.get()
		#print (self.__AT_Prefix,self.__AT_data_quotation,raw_data)
		if self.__AT_Prefix is not None:
			if raw_data.upper().startswith(self.__AT_Prefix.upper()):
				raw_data = raw_data.swapcase()
			elif self.__AT_data_quotation is not None:
				raw_data = '%s=%s%s%s'%(self.__AT_Prefix,self.__AT_data_quotation,raw_data,self.__AT_data_quotation)
			else:
				raw_data = '%s=%s'%(self.__AT_Prefix,raw_data)
		else:
			raw_data = raw_data.swapcase()
		self.__data.set(raw_data)
	def _decode_click(self,event=None):
		try:
			raw_data = self.__data.get()
			
			if raw_data.startswith('AT') or raw_data.startswith('at'):
				data_offset = raw_data.find('=')
				if data_offset > 0:
					self.__AT_Prefix = raw_data[0:data_offset]
					if raw_data[data_offset+1] == '"' or raw_data[data_offset+1] == "'":
						self.__AT_data_quotation = raw_data[data_offset+1]
						raw_data = raw_data[data_offset+2:]
					else:
						raw_data = raw_data[data_offset+1:]
			#print (self.__AT_Prefix,self.__AT_data_quotation,raw_data)
			raw_data = raw_data.replace(' ','').replace(',','').replace('0x','').replace('"','')
			data = hex_to_bytes(raw_data)
			self.gui_clear_all_tlv()
			TLV_ParseAll(data,0)
		except Exception as e:
			print ('Decode Error:%s\n'%e)
			self.__tips.set('Decode Error:%s'%e)
			pass
	def gui_clear_all_tlv(self):
		for _row in range(0,self._MAX_TLV_COUNT):
			self.__tag_used[_row] = 0
			self.__tip_var[_row].set('')
			self.__tag_var[_row].set('')
			self.__len_var[_row].set('')
			self.__val_var[_row].set('')
		
	def gui_add_tlv(self,level,tag_name,Tag,tag_content,edit_able=True,displayType=None):
		found = -1
		for i in range(0,self._MAX_TLV_COUNT):
			if self.__tag_used[i] == 0:
				found = i
				break
		
		if found < 0:
			self._add_tlv_table(self._MAX_TLV_COUNT)
			found = self._MAX_TLV_COUNT
			self._MAX_TLV_COUNT += 1
		_row = found
		self.__tag_used[_row] = 1
		self.__display_sel_old[_row] = _row*self.__row_mask+self.__none_int_mask+1
		self.__display_sel_var[_row].set(self.__display_sel_old[_row])
		self.__tip_var[_row].set('%s'%tag_name)
		self.__tag_var[_row].set('0x%02x'%Tag.Tag)
		self.__len_var[_row].set('0x%02x'%Tag.Len)
		self.__val_var[_row].set(tag_content)
		if edit_able is False:
			for _tlv_widget in self.__tlv_widget[_row]:
				if _tlv_widget['state'] != 'readonly':
					_tlv_widget.configure(state='readonly')
		else:
			for _tlv_widget in self.__tlv_widget[_row]:
				if _tlv_widget['state'] != 'normal':
					_tlv_widget.configure(state='normal')
	def gui_run(self):
		self.root.mainloop()

def register_stk_tlv_struct():
	register_tag_struct(STK_DATA_TAG.CMD_DETAILS_TAG,T_CMD_DETAILS_TAG)
	register_tag_struct(STK_DATA_TAG.CMD_DETAILS_TAG|0x80,T_CMD_DETAILS_TAG)
	register_tag_struct(STK_DATA_TAG.TERMINAL_TRAN_LEVEL_TAG,T_TRAN_LEVEL_TAG)
	register_tag_struct(STK_DATA_TAG.TERMINAL_TRAN_LEVEL_TAG|0x80,T_TRAN_LEVEL_TAG)
	register_tag_struct(STK_DATA_TAG.OTHER_ADDR_TAG,T_OTHER_ADDR_TAG)
	register_tag_struct(STK_DATA_TAG.OTHER_ADDR_TAG|0x80,T_OTHER_ADDR_TAG)
	register_tag_struct(STK_DATA_TAG.NETWORK_ACCESS_NAME_TAG,T_NETWORK_ACCESS_NAME_TAG)
	register_tag_struct(STK_DATA_TAG.NETWORK_ACCESS_NAME_TAG|0x80,T_NETWORK_ACCESS_NAME_TAG)

def set_tlv_gui_obj(_ui):
	global ui
	ui = _ui
	
if __name__ == '__main__':
	register_stk_tlv_struct()
	root = Tkinter.Tk()
	ui = TLV_GUI(root,Tkinter.StringVar(root),Tkinter.StringVar(root))
	#buf = hex_to_bytes("D0308103014003820281820500350702020405051F023902058E47080761706E2D6C74653C030208AE3E0521D30101039000")
	#TLV_ParseAll(buf)
	ui.gui_init()
	ui.gui_run()
	