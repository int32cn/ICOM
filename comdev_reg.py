import ctypes
import ctypes.wintypes as wintypes
import win32con

def ValidHandle(value):
    if value == 0:
        raise ctypes.WinError()
    return value

HANDLE = wintypes.HANDLE
HKEY = wintypes.HANDLE
PHKEY = ctypes.POINTER(HKEY)
NULL = 0
HDEVINFO = ctypes.c_int
BOOL = ctypes.c_int
CHAR = ctypes.c_char
PCTSTR = ctypes.c_char_p
LPCTSTR = ctypes.c_char_p
TCHAR = ctypes.c_short
PCWSTR = ctypes.POINTER(TCHAR)
HWND = ctypes.c_uint
DWORD = ctypes.c_ulong
PDWORD = ctypes.POINTER(DWORD)
ULONG = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(ULONG)
#~ PBYTE = ctypes.c_char_p
PBYTE = ctypes.c_void_p

PSP_DEVICE_INTERFACE_DETAIL_DATA = ctypes.c_void_p

SetupDiDestroyDeviceInfoList = ctypes.windll.setupapi.SetupDiDestroyDeviceInfoList
SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
SetupDiDestroyDeviceInfoList.restype = ValidHandle

SetupDiOpenDevRegKey = ctypes.windll.setupapi.SetupDiOpenDevRegKey


#LONG WINAPI RegOpenKeyEx(
#  _In_     HKEY    hKey,
#  _In_opt_ LPCTSTR lpSubKey,
#  _In_     DWORD   ulOptions,
#  _In_     REGSAM  samDesired,
#  _Out_    PHKEY   phkResult
#);

RegQueryValueEx = ctypes.windll.Advapi32.RegQueryValueExW
RegOpenKeyEx = ctypes.windll.Advapi32.RegOpenKeyExW

RegEnumValue = ctypes.windll.Advapi32.RegEnumValueW
RegCloseKey = ctypes.windll.Advapi32.RegCloseKey


DIGCF_PRESENT = 2
DIGCF_DEVICEINTERFACE = 16
INVALID_HANDLE_VALUE = 0
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_INVALID_DATA = 13
SPDRP_HARDWAREID = 1
SPDRP_FRIENDLYNAME = 12
ERROR_NO_MORE_ITEMS = 259

KEY_QUERY_VALUE        = (0x0001)
KEY_SET_VALUE          = (0x0002)
DICS_FLAG_GLOBAL       =1
DIREG_DEV       	   =1
KEY_QUERY_VALUE        =1
REG_NONE               =     ( 0 )   # No value type
REG_SZ                 =     ( 1 )   # Unicode nul terminated string
REG_EXPAND_SZ          =     ( 2 )   # Unicode nul terminated string

buf_name_dict = {}

def get_com_buffer(buf_name):
	global buf_name_dict
	if buf_name in buf_name_dict:
		return buf_name_dict[buf_name]
	else:
		new_buf = ctypes.create_unicode_buffer(u'\0\0', 768)
		buf_name_dict.setdefault(buf_name,new_buf)
		return new_buf

def comports(guid_class_id,available_only=True,_debug=None):
	"""This generator scans the device registry for com ports and yields port, desc, hwid.
		If available_only is true only return currently existing ports."""
	flags = DWORD()
	flags.value = DIGCF_DEVICEINTERFACE
	data_Set = get_com_buffer('serialCommRegPath')
	szKeyName = get_com_buffer('regKeyName')
	szKeyValue = get_com_buffer('regKeyValue')
	
	data_Set.value = "HARDWARE\\DEVICEMAP\\SERIALCOMM\\"
	hKey = HKEY()
	dwIndex = DWORD()
	dwIndex.value = 0
	dwType = DWORD()
	dwNameLen = DWORD()
	dwPortNameLen = DWORD()
	dwNameLen.value = ctypes.sizeof(szKeyName)
	dwPortNameLen.value = ctypes.sizeof(szKeyValue)
	
	ret0 = RegOpenKeyEx((HKEY)(win32con.HKEY_LOCAL_MACHINE), ctypes.byref(data_Set), 0, win32con.KEY_READ, ctypes.byref(hKey))
	if ret0 != 0:
		print ('reg OpenKeyEx fail:%d'%ret0,ctypes.WinError())
		return '','','';
	
	while dwIndex.value < 8:
		dwNameLen.value = ctypes.sizeof(szKeyName)
		dwPortNameLen.value = ctypes.sizeof(szKeyValue)
		Status = RegEnumValue(hKey, dwIndex, ctypes.byref(szKeyName), ctypes.byref(dwNameLen), NULL, ctypes.byref(dwType), ctypes.byref(szKeyValue), ctypes.byref(dwPortNameLen))
		if Status == ERROR_NO_MORE_ITEMS:
			break
		if Status == 0 and u'COM' in szKeyValue.value.upper():
			print (dwIndex.value,Status,szKeyName.value,szKeyValue.value)
			yield szKeyValue.value, szKeyValue.value, szKeyValue.value
		
		dwIndex.value += 1
	
	RegCloseKey(hKey)


if __name__ == '__main__':
    for desc, hwid, GUID in comports('COM',True):
        print ("%s (%s) %s" % (desc, hwid, GUID) )
        try:
            import serial
            #print " "*10, serial.Serial(port) #test open
        except:
            print ('open fail', port)
    
    # list of all ports the system knows
    print ("-"*60)
    for desc, hwid, GUID in comports('NET',True):
        print ("%s (%s) {%s}" % (desc, hwid, GUID) )
    
    print("-"*30,"MODEM","-"*30)
    for desc, hwid, GUID in comports('MODEM',True):
        print ("%s (%s) {%s}" % (desc, hwid, GUID) )
    
    