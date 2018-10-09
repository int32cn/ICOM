#!/usr/bin/python
# -*- coding= utf-8 -*-
import ctypes as ct

class MULTICAST_HEADER(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('ID',          ct.c_uint),
		('CRC32',       ct.c_uint),
		('SrcIP',		ct.c_uint),
		('DstIP',		ct.c_uint),
		('Seq',			ct.c_uint),
		('DataLen',     ct.c_uint)
	]
	def __repr__(self):
		return '<ID:0x%x Src:0x%x Dst:0x%x Seq:0x%x len:%d>'%(self.ID, self.SrcIP, self.DstIP, self.Seq, self.DataLen)

class MSG_ID(object):
	ID_LOGIN  				= 0x01
	ID_LOGOFF 				= 0x02
	ID_CONTEST_ADMIN  		= 0x03
	ID_ADMIN_CONTEST_REPLY  = 0x04
	ID_AUTH_USER_LIST 		= 0x11
	ID_AUTH_CONTEST_START 	= 0x12

class USER_STATUS():
	STATUS_OFFLINE              = 0x00
	STATUS_ONLINE               = 0x01

class TAG_ID(object):
	TAG_MSG_BEGIN				= 0x1000
	TAG_USER_INFO            	= 0x1001
	TAG_USER_LIST				= 0x1002
	TAG_ADMIN_CONTEST			= 0x1003
	TAG_VERSION					= 0x1004
	TAG_KEY_INFO				= 0x1005
	TAG_MSG_END				    = 0x1fff

__g_tag_table = []

def register_tag_struct(tag_id_in, struct_name):
	for tag_id, tag_struct in __g_tag_table:
		if tag_id == tag_id_in:
			return None
	__g_tag_table.append((tag_id_in, struct_name))
	return tag_id_in

def get_tag_struct(tag_id_in):
	#tag_id -> tag_structure, tag_msg_end, no need here
	tag_table = (
		(TAG_ID.TAG_USER_INFO,		USER_INFO),
		(TAG_ID.TAG_USER_LIST,		USER_LIST),
		(TAG_ID.TAG_ADMIN_CONTEST,	ADMIN_CONTEST),
		(TAG_ID.TAG_VERSION,		VERSION_INFO)
		)
	tag_structure = None
	for tag_id, tag_struct in tag_table:
		if tag_id == tag_id_in:
			tag_structure = tag_struct
			break
	for tag_id, tag_struct in __g_tag_table:
		if tag_id == tag_id_in:
			tag_structure = tag_struct
			break
	return tag_structure

class MSG_TAG_BYTE(ct.Structure):
	_pack_      = 1
	_fields_    = [
		('Tag',				ct.c_uint8),
		('Len',				ct.c_uint8),
	]
	def __init__(self,Tag,Len):
		ct.Structure.__init__(self)
		self.Tag = Tag
		self.Len = Len - ct.sizeof(MSG_TAG_BYTE)
	def __repr__(self):
		return 'Tag:0x%02x Len:0x%02x'%(self.Tag,self.Len)

class MSG_TAG(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('Tag',				ct.c_uint16),
		('Len',				ct.c_uint16),
	]
	def __init__(self,Tag,Len):
		ct.Structure.__init__(self)
		self.Tag = Tag
		self.Len = Len - ct.sizeof(MSG_TAG)
	def __repr__(self):
		return 'Tag:0x%x Len:%d'%(self.Tag,self.Len)

class USER_INFO(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
		('NickName',		ct.c_char * 17),
		('Status',			ct.c_uint8),
		('UdpPort',			ct.c_uint16),
		('Addr',			ct.c_uint),
	]
	def __init__(self):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(TAG_ID.TAG_USER_INFO,ct.sizeof(USER_INFO))
	def __repr__(self):
		return '<%s NickName:%s Addr:0x%x,UdpPort:%d,Status:%d>'%(self.TL,self.NickName,self.Addr,self.UdpPort,self.Status)

class VERSION_INFO(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
		('Version',			ct.c_uint32),
		('Description',		ct.c_char * 64),
	]
	def __init__(self):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(TAG_ID.TAG_VERSION,ct.sizeof(VERSION_INFO))
	def __repr__(self):
		return '<%s Version:%d Description:%s>'%(self.TL,self.Version,self.Description)

class KEY_INFO(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
		('Data',			ct.c_char * 64),
	]
	def __init__(self):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(TAG_ID.TAG_KEY_INFO,ct.sizeof(KEY_INFO))
	def __repr__(self):
		return '<%s Version:%d Description:%s>'%(self.TL,self.Version,self.Description)

class EMPTY_TAG(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
	]
	def __init__(self,tag_id):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(tag_id,ct.sizeof(EMPTY_TAG))
	def __repr__(self):
		return 'EMPTY_TAG %s'%self.TL

class USER_LIST(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
		('UserCount',		ct.c_uint),
		('TotalSections',	ct.c_uint),
		('CurrentSection', ct.c_uint),
		('AdminIndex',		ct.c_uint),
		('SecondIndex',		ct.c_uint),
	]
	def __init__(self):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(TAG_ID.TAG_USER_LIST,ct.sizeof(USER_LIST))
	def __repr__(self):
		return '%s,UserCount:%d Admin:(%d,%d)'%(self.TL,self.UserCount,self.AdminIndex,self.SecondIndex)

class ADMIN_CONTEST(ct.Structure):
	_pack_      = 4
	_fields_    = [
		('TL',				MSG_TAG),
		('AdminType',		ct.c_uint)
	]
	def __init__(self):
		ct.Structure.__init__(self)
		self.TL = MSG_TAG(TAG_ID.TAG_ADMIN_CONTEST,ct.sizeof(ADMIN_CONTEST))
	def __repr__(self):
		return '%s AdminType:%d'%(self.TL,self.AdminType)

def struct2stream(s):
	length  = ct.sizeof(s)
	p       = ct.cast(ct.pointer(s), ct.POINTER(ct.c_char * length))
	return p.contents.raw

def stream2struct(string, stype):
	if not issubclass(stype, ct.Structure):
		raise ValueError('The type of the struct is not a ctypes.Structure')
	length      = ct.sizeof(stype)
	#length_src  = len(string)
	stream      = (ct.c_char * length)()
	#if length_src < length:
	#	raise ValueError('The type of the struct is short of stype')
	#stream.raw  = string[0:length]
	#p           = ct.cast(stream, ct.POINTER(stype))
	p           = ct.cast(ct.addressof(string), ct.POINTER(stype))
	return p.contents

def bytes_to_ctypes_array(in_str):
	length      = len(in_str)
	if not isinstance(in_str, bytes):
		length = length * 2 #python 3.x unicode str
	stream      = (ct.c_char * length)()
	stream.raw  = in_str
	#p           = ct.cast(stream, ct.POINTER(stype))
	return length,stream
	
def join_header_and_body(header,*TLV_tags):
	header_len = ct.sizeof(header)
	total_len  = header_len
	tags_group = []
	if 1 == len(TLV_tags) and type(TLV_tags[0]) == type([]):
		TLV_tags = TLV_tags[0]
	for one_TLV_tag in TLV_tags:
		#print ('O:%s\n'%one_TLV_tag)
		tag_len   = ct.sizeof(one_TLV_tag)
		total_len  += tag_len
		tags_group.append((tag_len,one_TLV_tag))
		
	#allocate hotal message buffer and copy msg header
	buffer         = (ct.c_byte * total_len)()
	header.DataLen = total_len - header_len
	ct.memmove(ct.addressof(buffer),	ct.byref(header),	header_len)
	
	#copy all message TLV tag bodys
	for tag_len,tag_TLV in tags_group:
		#print('JOIN H:%d,TA:%d,type:%s T:0x%x,L:%d\n'%(header_len,tag_len,type(tag_TLV),tag_TLV.TL.Tag,tag_TLV.TL.Len))
		ct.memmove(ct.addressof(buffer)+header_len,	ct.byref(tag_TLV), tag_len)
		header_len += tag_len
		
	return buffer
	
def get_tag_msg(_msg,skip_len,tag_type):
	#print ('SKIP:%d\n'%skip_len)
	if skip_len + ct.sizeof(tag_type) <= ct.sizeof(_msg):
		p           = ct.cast(ct.addressof(_msg) + skip_len, ct.POINTER(tag_type))
		return p.contents
	return None
	
def get_next_tag(_msg, skip_len):
	if skip_len + ct.sizeof(MSG_TAG) < ct.sizeof(_msg):
		p           = ct.cast(ct.addressof(_msg) + skip_len, ct.POINTER(MSG_TAG))
		return p.contents
	
	return None
	
def get_next_tag_byte(_msg, skip_len):
	if skip_len + ct.sizeof(MSG_TAG_BYTE) <= ct.sizeof(_msg):
		p           = ct.cast(ct.addressof(_msg) + skip_len, ct.POINTER(MSG_TAG_BYTE))
		return p.contents
	
	return None

