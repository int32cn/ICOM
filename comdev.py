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
TCHAR = ctypes.c_short
PCWSTR = ctypes.POINTER(TCHAR)
HWND = ctypes.c_uint
DWORD = ctypes.c_ulong
PDWORD = ctypes.POINTER(DWORD)
ULONG = ctypes.c_ulong
ULONG_PTR = ctypes.POINTER(ULONG)
#~ PBYTE = ctypes.c_char_p
PBYTE = ctypes.c_void_p

class GUID(ctypes.Structure):
    _fields_ = [
        ('Data1', ctypes.c_ulong),
        ('Data2', ctypes.c_ushort),
        ('Data3', ctypes.c_ushort),
        ('Data4', ctypes.c_ubyte*8),
    ]
    def __str__(self):
        return "{%08x-%04x-%04x-%s-%s}" % (
            self.Data1,
            self.Data2,
            self.Data3,
            ''.join(["%02x" % d for d in self.Data4[:2]]),
            ''.join(["%02x" % d for d in self.Data4[2:]]),
        )

class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('ClassGuid', GUID),
        ('DevInst', DWORD),
        ('Reserved', ULONG_PTR),
    ]
    def __str__(self):
        return "ClassGuid:%s DevInst:%s" % (self.ClassGuid, self.DevInst)
PSP_DEVINFO_DATA = ctypes.POINTER(SP_DEVINFO_DATA)

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', DWORD),
        ('InterfaceClassGuid', GUID),
        ('Flags', DWORD),
        ('Reserved', ULONG_PTR),
    ]
    def __str__(self):
        return "InterfaceClassGuid:%s Flags:%s" % (self.InterfaceClassGuid, self.Flags)
PSP_DEVICE_INTERFACE_DATA = ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)

PSP_DEVICE_INTERFACE_DETAIL_DATA = ctypes.c_void_p

SetupDiDestroyDeviceInfoList = ctypes.windll.setupapi.SetupDiDestroyDeviceInfoList
SetupDiDestroyDeviceInfoList.argtypes = [HDEVINFO]
SetupDiDestroyDeviceInfoList.restype = BOOL

SetupDiOpenDevRegKey = ctypes.windll.setupapi.SetupDiOpenDevRegKey
SetupDiGetClassDevs = ctypes.windll.setupapi.SetupDiGetClassDevsW
SetupDiGetClassDevs.argtypes = [ctypes.POINTER(GUID), PCTSTR, HWND, DWORD]
SetupDiGetClassDevs.restype = ValidHandle #HDEVINFO
 
#LONG WINAPI RegOpenKeyEx(
#  _In_     HKEY    hKey,
#  _In_opt_ LPCTSTR lpSubKey,
#  _In_     DWORD   ulOptions,
#  _In_     REGSAM  samDesired,
#  _Out_    PHKEY   phkResult
#);
RegOpenKeyEx = ctypes.windll.Advapi32.RegOpenKeyExW
RegQueryValueEx = ctypes.windll.Advapi32.RegQueryValueExW
RegEnumValue = ctypes.windll.Advapi32.RegEnumValueW
RegCloseKey = ctypes.windll.Advapi32.RegCloseKey

SetupDiEnumDeviceInterfaces = ctypes.windll.setupapi.SetupDiEnumDeviceInterfaces
SetupDiEnumDeviceInterfaces.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, ctypes.POINTER(GUID), DWORD, PSP_DEVICE_INTERFACE_DATA]
SetupDiEnumDeviceInterfaces.restype = BOOL

SetupDiGetDeviceInterfaceDetail = ctypes.windll.setupapi.SetupDiGetDeviceInterfaceDetailW
SetupDiGetDeviceInterfaceDetail.argtypes = [HDEVINFO, PSP_DEVICE_INTERFACE_DATA, PSP_DEVICE_INTERFACE_DETAIL_DATA, DWORD, PDWORD, PSP_DEVINFO_DATA]
SetupDiGetDeviceInterfaceDetail.restype = BOOL

SetupDiGetDeviceRegistryProperty = ctypes.windll.setupapi.SetupDiGetDeviceRegistryPropertyW
SetupDiGetDeviceRegistryProperty.argtypes = [HDEVINFO, PSP_DEVINFO_DATA, DWORD, PDWORD, PBYTE, DWORD, PDWORD]
SetupDiGetDeviceRegistryProperty.restype = BOOL

#GUID_DEVINTERFACE_PORT = GUID(0x4d36e972L, 0xe325, 0x11ce,
#    (ctypes.c_ubyte*8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18))
#{4d36e972-e325-11ce-bfc1-08002be10318}

#--------------------------------------------
#System-Defined Device Setup Classes Available to Vendors
#https://msdn.microsoft.com/en-us/library/ff553426%28v=vs.85%29.aspx
#Ports (COM & LPT ports)
#    Class = Ports
#    ClassGuid = {4d36e978-e325-11ce-bfc1-08002be10318}
#    This class includes serial and parallel port devices. See also the MultiportSerial class.
GUID_DEVCLASS_PORTS = GUID(0x4D36E978, 0xE325, 0x11CE,
        (ctypes.c_ubyte*8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18))
#--------------------------------------------


#--------------------------------------------
#The GUID_DEVINTERFACE_USB_DEVICE device interface class is defined for USB devices that are attached to a USB hub.
#Attribute	Setting
#Identifier
#GUID_DEVINTERFACE_USB_DEVICE
#Class GUID
#{A5DCBF10-6530-11D2-901F-00C04FB951ED}
GUID_DEVINTERFACE_USB_DEVICE = GUID(0xA5DCBF10, 0x6530,0x11D2, 
        (ctypes.c_ubyte*8)(0x90, 0x1F, 0x00,0xC0, 0x4F, 0xB9, 0x51, 0xED))
#-------------------------------------------

#https://msdn.microsoft.com/en-us/library/windows/hardware/ff545821%28v=vs.85%29.aspx
#The GUID_DEVINTERFACE_COMPORT device interface class is defined for COM ports.
#Attribute	Setting
#Identifier
#GUID_DEVINTERFACE_COMPORT
#Class GUID
#{86E0D1E0-8089-11D0-9CE4-08003E301F73}
GUID_DEVINTERFACE_COMPORT = GUID(0x86e0d1e0, 0x8089, 0x11d0,
    (ctypes.c_ubyte*8)(0x9c, 0xe4, 0x08, 0x00, 0x3e, 0x30, 0x1f, 0x73))

#https://msdn.microsoft.com/en-us/library/windows/hardware/ff545922%28v=vs.85%29.aspx
#Class GUID     {CAC88484-7515-4C03-82E6-71A87ABAC361}
GUID_DEVINTERFACE_NET = GUID(0xCAC88484, 0x7515, 0x4C03,
    (ctypes.c_ubyte*8)(0x82, 0xe6, 0x71, 0xA8, 0x7A, 0xBA, 0xC3, 0x61))

#https://msdn.microsoft.com/en-us/library/windows/hardware/ff545892%28v=vs.85%29.aspx
#Class GUID  {2C7089AA-2E0E-11D1-B114-00C04FC2AAE4}
GUID_DEVINTERFACE_MODEM = GUID(0x2C7089AA, 0x2E0E, 0x11D1,
    (ctypes.c_ubyte*8)(0xB1, 0x14, 0x00, 0xC0, 0x4F, 0xC2, 0xAA, 0xE4))

class_groups = {
	'NET': ctypes.byref(GUID_DEVINTERFACE_NET),
	'COM': ctypes.byref(GUID_DEVINTERFACE_COMPORT),#microsoft 
	'COM2': ctypes.byref(GUID_DEVCLASS_PORTS),
	'USB': ctypes.byref(GUID_DEVINTERFACE_USB_DEVICE),
	'MODEM':ctypes.byref(GUID_DEVINTERFACE_MODEM)
}

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
		new_buf = ctypes.create_unicode_buffer(u'\0' * 1024)
		buf_name_dict.setdefault(buf_name,new_buf)
		return new_buf

def comportsReg(guid_class_id,available_only=True,_debug=None):
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

def comports(guid_class_id,available_only=True,_debug=None):
    """This generator scans the device registry for com ports and yields port, desc, hwid.
       If available_only is true only return currently existing ports."""
    flags = DWORD()
    flags.value = DIGCF_DEVICEINTERFACE
    if available_only:
        flags.value |= DIGCF_PRESENT
    if guid_class_id in class_groups:
        guid_class = class_groups[guid_class_id]
    else:
        guid_class = class_groups['COM']
    g_hdi = SetupDiGetClassDevs(guid_class, (PCTSTR)(NULL), (HWND)(NULL), flags);
    if _debug is not None:
        print ('type:%s'%guid_class_id)
    #~ for i in range(256):
    for dwIndex in range(256):
        did = SP_DEVICE_INTERFACE_DATA()
        did.cbSize = ctypes.sizeof(did)
        dwIdx = DWORD()
        dwIdx.value = dwIndex
        if not SetupDiEnumDeviceInterfaces(
            g_hdi,
            None,
            guid_class,
            dwIdx,
            ctypes.byref(did)
        ):
            if ctypes.GetLastError() != ERROR_NO_MORE_ITEMS:
                print ('setup%d'%dwIndex,ctypes.WinError()) #raise ctypes.WinError()
                continue
            if _debug is not None:
                print ('setup%d'%dwIndex,ctypes.WinError())
                
            break
        
        dwNeeded = DWORD()
        dwNeeded.value= 0
        # get the size
        if not SetupDiGetDeviceInterfaceDetail(
            g_hdi,
            ctypes.byref(did),
            None, 0, ctypes.byref(dwNeeded),
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                print ('size%d'%dwIndex, ctypes.WinError())
                continue#raise ctypes.WinError()
            #else:
            #    print ('size%d'%dwIndex, ctypes.WinError(), dwNeeded.value)
        # allocate buffer
        class SP_DEVICE_INTERFACE_DETAIL_DATA_A(ctypes.Structure):
            _fields_ = [
                ('cbSize', DWORD),
                ('DevicePath', CHAR*(dwNeeded.value - ctypes.sizeof(DWORD))),
            ]
            def __str__(self):
                return "DevicePath:%s" % (self.DevicePath,)
        idd = SP_DEVICE_INTERFACE_DETAIL_DATA_A()
        idd.cbSize = 6
        devinfo = SP_DEVINFO_DATA()
        devinfo.cbSize = ctypes.sizeof(devinfo)
        
        if not SetupDiGetDeviceInterfaceDetail(
            g_hdi,
            ctypes.byref(did),
            ctypes.byref(idd), dwNeeded, None,
            ctypes.byref(devinfo)
        ):
            print ('detail%d'%dwIndex,ctypes.WinError())
            continue#raise ctypes.WinError()
        
        # hardware ID
        
        szHardwareID = get_com_buffer('szHardwareID')
        if not SetupDiGetDeviceRegistryProperty(
            g_hdi,
            ctypes.byref(devinfo),
            SPDRP_HARDWAREID,
            None,
            ctypes.byref(szHardwareID), ctypes.sizeof(szHardwareID) - 1,
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                print ('hardwareId%d'%dwIndex,ctypes.WinError())
                continue#raise ctypes.WinError()
            else:
                print ('hardwareId%d'%dwIndex,ctypes.WinError())
        # friendly name
        if _debug is not None:
            print ('szHardwareID',szHardwareID.value)
        szDesc = get_com_buffer('szDesc')
        if not SetupDiGetDeviceRegistryProperty(
            g_hdi,
            ctypes.byref(devinfo),
            0,
            None,
            ctypes.byref(szDesc), ctypes.sizeof(szDesc) - 1,
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            if ctypes.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                print ('szDesc%d'%dwIndex,ctypes.WinError() )
                continue#raise ctypes.WinError()
            else:
                print ('szDesc%d'%dwIndex,ctypes.WinError())
        if _debug is not None:
            print ('szDesc',szDesc.value)
        port_name_from_reg = ''
        if guid_class_id != 'NET':
            hDeviceKey = SetupDiOpenDevRegKey(g_hdi, ctypes.byref(devinfo), DICS_FLAG_GLOBAL, 0, DIREG_DEV, KEY_QUERY_VALUE);
            dwType = DWORD(0)
            dwSize = DWORD(255)
            c_portName = ctypes.c_buffer(b'\0', 60)
            c_portName.value = b"PortName"
            szPortName = get_com_buffer('szPortName')
            ret = RegQueryValueEx(hDeviceKey, ctypes.byref(c_portName), NULL, ctypes.byref(dwType), ctypes.byref(szPortName), ctypes.byref(dwSize))
            if 0 == ret and (dwType.value == REG_EXPAND_SZ or dwType.value == REG_SZ) and len(szPortName.value) > 0:
                port_name_from_reg = szPortName.value
            if _debug is not None:
                print ('modem',ret,szPortName,port_name_from_reg)
        szFriendlyName = get_com_buffer('szFriendlyName')
        if not SetupDiGetDeviceRegistryProperty(
            g_hdi,
            ctypes.byref(devinfo),
            SPDRP_FRIENDLYNAME,
            None,
            ctypes.byref(szFriendlyName), ctypes.sizeof(szFriendlyName) - 1,
            None
        ):
            # Ignore ERROR_INSUFFICIENT_BUFFER
            last_err = ctypes.GetLastError()
            if last_err == ERROR_INVALID_DATA:
                print ('friendlyName null')
                szFriendlyName.value = szDesc.value
            elif last_err != ERROR_INSUFFICIENT_BUFFER:
                print ('friendlyName',ctypes.WinError() )
                continue#raise ctypes.WinError()
            else:
                print ('friendlyName',ctypes.WinError() )
        if _debug is not None:
            print ('FriendlyName%d'%dwIndex,szFriendlyName.value,'szDesc',szDesc.value)
        if guid_class_id != 'NET' and len(port_name_from_reg) > 0:
            try:
                comindex = szFriendlyName.value.find(port_name_from_reg)
                if comindex < 0:
                    szFriendlyName.value += b' '+port_name_from_reg
            except Exception as e:
                print ('exception in parse szFriendlyName:%s'%e)
                pass
        yield szFriendlyName.value, szHardwareID.value, did.InterfaceClassGuid
    
    SetupDiDestroyDeviceInfoList(g_hdi)


if __name__ == '__main__':
    for desc, hwid, GUID in comports('COM',True,True):
        print ("%s (%s) %s" % (desc, hwid, GUID) )
        try:
            import serial
            #print " "*10, serial.Serial(port) #test open
        except:
            print ('open fail', port)
    for desc, hwid, GUID in comportsReg('COM2',True,True):
        print ("COMREG %s (%s) %s" % (desc, hwid, GUID) )
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
    
    