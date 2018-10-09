from ctypes import *
import ctypes.wintypes as wintypes
from os import linesep

ERROR_BUFFER_OVERFLOW = 111
g_dll_handle = None

class IP_ADDRESS_STRING(Structure):
	_fields_ = [
		('String', c_char*16)
	]
	def __str__(self):
		return self.String.decode()


class IP_ADDR_STRING(Structure):
	_fields_ = [
        ('Next', c_void_p),
		('IpAddress', IP_ADDRESS_STRING),
		('IpMask', IP_ADDRESS_STRING),
		('Context', wintypes.DWORD)
	]
	def __str__(self):
		return str(self.IpAddress)+' '+str(self.IpMask)

class time_t(Structure):
	_fields_ = [
		('High', wintypes.DWORD),
		('Low', wintypes.DWORD),
	]
	def __str__(self):
		return "%08x%08x"%(self.High,self.Low)

class SOCKADDR(Structure):
	_fields_ = [
		('sa_family', wintypes.USHORT),
		('sa_data', wintypes.CHAR*14),
	]

class SOCKET_ADDRESS(Structure):
	_fields_ = [
		('lpSockaddr', POINTER(SOCKADDR)),
		('iSockaddrLength', wintypes.INT),
	]
	def __str__(self):
		addr = ""
		if (self.iSockaddrLength > 0):
			addr = ",".join([str(self.iSockaddrLength),str(self.lpSockaddr.contents.sa_family),str(self.lpSockaddr.contents.sa_data)])
		print (addr)
		return addr
	
class IP_ADAPTER_UNICAST_ADDRESS(Structure):
	class IP_DAD_STATE_E:
		IpDadStateInvalid     = 0
		IpDadStateTentative   = 1
		IpDadStateDuplicate   = 2
		IpDadStateDeprecated  = 3
		IpDadStatePreferred   = 4
	class IP_PREFIX_ORIGIN_E:
		IpPrefixOriginOther      = 0
		IpPrefixOriginManual     = 1
		IpPrefixOriginWellKnown  = 2
		IpPrefixOriginDhcp       = 3
		IpPrefixOriginRouterAdvertisement = 4
		IpPrefixOriginUnchanged            = 16
	class IP_SUFFIX_ORIGIN_E:
		IpSuffixOriginOther               = 0
		IpSuffixOriginManual              = 1
		IpSuffixOriginWellKnown           = 2
		IpSuffixOriginDhcp                = 3
		IpSuffixOriginLinkLayerAddress    = 4
		IpSuffixOriginRandom              = 5
		IpSuffixOriginUnchanged           = 16
	
	_fields_ = [
		('Length', wintypes.ULONG),
		('Flags', wintypes.DWORD),
		('Next', c_void_p),
		('Address', SOCKET_ADDRESS),
		('PrefixOrigin', wintypes.UINT), #IP_PREFIX_ORIGIN_E
		('SuffixOrigin', wintypes.UINT), #IP_SUFFIX_ORIGIN_E
		('DadState', wintypes.UINT),#IP_DAD_STATE_E
		('ValidLifetime', wintypes.ULONG),
		('PreferredLifetime', wintypes.ULONG),
		('LeaseLifetime', wintypes.ULONG),
		('OnLinkPrefixLength', c_uint8),
	]
	def __str__(self):
		info = [self.Flags, self.DadState, self.ValidLifetime, self.PreferredLifetime, str(self.Address)]
		return "%s"%info

class IP_ADAPTER_MULTICAST_ADDRESS(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Flags', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS)
	]
class IP_ADAPTER_ANYCAST_ADDRESS(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Flags', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS)
	]

class IP_ADAPTER_DNS_SERVER_ADDRESS(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Reserved', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS)
	]
class IP_ADAPTER_WINS_SERVER_ADDRESS(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Reserved', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS)
	]

class IP_ADAPTER_GATEWAY_ADDRESS(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Reserved', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS)
	]

class IP_ADAPTER_PREFIX(Structure):
	_fields_ = [
		('Length', wintypes.ULONG),
		('Flags', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('Address', SOCKET_ADDRESS),
		('PrefixLength', wintypes.ULONG)
	]

class IP_ADAPTER_DNS_SUFFIX(Structure):
	MAX_DNS_SUFFIX_STRING_LENGTH = 256
	_fields_ = [
		('Next', wintypes.LPVOID),
		('String', wintypes.WCHAR*MAX_DNS_SUFFIX_STRING_LENGTH)
	]

class NET_IF_NETWORK_GUID(Structure):
	_fields_ = [
		('Data1', c_ulong),
		('Data2', c_ushort),
		('Data3', c_ushort),
		('Data4', c_ubyte*8),
	]
	def __str__(self):
		return "{%08x-%04x-%04x-%s-%s}" % (
			self.Data1,
			self.Data2,
			self.Data3,
			''.join(["%02x" % d for d in self.Data4[:2]]),
			''.join(["%02x" % d for d in self.Data4[2:]]),
		)


class IP_ADAPTER_ADDRESSES(Structure):
	MAX_ADAPTER_ADDRESS_LENGTH = 8
	MAX_DHCPV6_DUID_LENGTH = 130
	class ADAPTER_FLAGS:
		IP_ADAPTER_DDNS_ENABLED = 0x01 #Dynamic DNS is enabled on this adapter
		IP_ADAPTER_REGISTER_ADAPTER_SUFFIX = 0x02 #Register the DNS suffix for this adapter
		IP_ADAPTER_DHCP_ENABLED = 0x04 #The Dynamic Host Configuration Protocol (DHCP) is enabled on this adapter
		IP_ADAPTER_RECEIVE_ONLY = 0x08 #The adapter is a receive-only adapter
		IP_ADAPTER_NO_MULTICAST = 0x10 #The adapter is not a multicast recipient
		IP_ADAPTER_IPV6_OTHER_STATEFUL_CONFIG = 0x20 #The adapter contains other IPv6-specific stateful configuration information. 
		IP_ADAPTER_NETBIOS_OVER_TCPIP_ENABLED = 0x40 #The adapter is enabled for NetBIOS over TCP/IP. 
		IP_ADAPTER_IPV4_ENABLED = 0x80 #The adapter is enabled for IPv4. 
		IP_ADAPTER_IPV6_ENABLED = 0x100 #The adapter is enabled for IPv6. 
		IP_ADAPTER_IPV6_MANAGE_ADDRESS_CONFIG = 0x200 #The adapter is enabled for IPv6 managed address configuration. 
	class IF_OPER_STATUS_E:
		IfOperStatusUp   = 1
		IfOperStatusDown = 2
		IfOperStatusTesting = 3
		IfOperStatusUnknown = 4
		IfOperStatusDormant  = 5
		IfOperStatusNotPresent = 6
		IfOperStatusLowerLayerDown = 7
	class IFTYPE:
		IF_TYPE_OTHER = 1
		IF_TYPE_ETHERNET_CSMACD = 6
		IF_TYPE_ISO88025_TOKENRING = 9
		IF_TYPE_PPP = 23
		IF_TYPE_SOFTWARE_LOOPBACK = 24
		IF_TYPE_ATM = 37
		IF_TYPE_IEEE80211 = 71
		IF_TYPE_TUNNEL = 131
		IF_TYPE_IEEE1394 = 144
	class NET_IF_CONNECTION_TYPE_E:
		NET_IF_CONNECTION_DEDICATED = 1
		NET_IF_CONNECTION_PASSIVE = 2
		NET_IF_CONNECTION_DEMAND = 3
		NET_IF_CONNECTION_MAXIMUM = 4
	class TUNNEL_TYPE_E:
		TUNNEL_TYPE_NONE = 0 #Not a tunnel.
		TUNNEL_TYPE_OTHER = 1 #None of the following tunnel types.
		TUNNEL_TYPE_DIRECT = 2 #A packet is encapsulated directly within a normal IP header, with no intermediate header, and unicast to the remote tunnel endpoint.
		TUNNEL_TYPE_6TO4 = 11 #An IPv6 packet is encapsulated directly within an IPv4 header, with no intermediate header, and unicast to the destination determined by the 6to4 protocol.
		TUNNEL_TYPE_ISATAP = 13 #An IPv6 packet is encapsulated directly within an IPv4 header, with no intermediate header, and unicast to the destination determined by the ISATAP protocol.
		TUNNEL_TYPE_TEREDO = 14 #Teredo encapsulation for IPv6 packets.
		TUNNEL_TYPE_IPHTTPS = 15 #IP over HTTPS encapsulation for IPv6 packets.
	_fields_ = [
		('Length', wintypes.ULONG),
		('IfIndex', wintypes.DWORD),
		('Next', wintypes.LPVOID),
		('AdapterName', wintypes.PCHAR),
		('FirstUnicastAddress', POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
		('FirstAnycastAddress', POINTER(IP_ADAPTER_ANYCAST_ADDRESS)),
		('FirstMulticastAddress', POINTER(IP_ADAPTER_MULTICAST_ADDRESS)),
		('FirstDnsServerAddress', POINTER(IP_ADAPTER_DNS_SERVER_ADDRESS)),
		('DnsSuffix', wintypes.PWCHAR),
		('Description', wintypes.PWCHAR),
		('FriendlyName', wintypes.PWCHAR),
		('PhysicalAddress', wintypes.BYTE*MAX_ADAPTER_ADDRESS_LENGTH),
		('PhysicalAddressLength', wintypes.DWORD),
		('Flags', wintypes.DWORD), #ADAPTER_FLAGS
		('Mtu', wintypes.DWORD),
		('IfType', wintypes.DWORD),
		('OperStatus', wintypes.UINT), #IF_OPER_STATUS_E
		('Ipv6IfIndex', wintypes.DWORD),
		('ZoneIndices', wintypes.DWORD*16),
		('FirstPrefix', POINTER(IP_ADAPTER_PREFIX)),
		('TransmitLinkSpeed', c_uint64),
		('ReceiveLinkSpeed', c_uint64),
		('FirstWinsServerAddress', POINTER(IP_ADAPTER_WINS_SERVER_ADDRESS)),
		('FirstGatewayAddress', POINTER(IP_ADAPTER_GATEWAY_ADDRESS)),
		('Ipv4Metric', wintypes.ULONG),
		('Ipv6Metric', wintypes.ULONG),
		('Luid', c_uint64),
		('Dhcpv4Server', SOCKET_ADDRESS),
		('CompartmentId', wintypes.UINT),#NET_IF_COMPARTMENT_ID
		('NetworkGuid', NET_IF_NETWORK_GUID),
		('ConnectionType', wintypes.UINT),#NET_IF_CONNECTION_TYPE
		('TunnelType', wintypes.UINT),#TUNNEL_TYPE
		('Dhcpv6Server', SOCKET_ADDRESS),
		('Dhcpv6ClientDuid', wintypes.BYTE*MAX_DHCPV6_DUID_LENGTH),
		('Dhcpv6ClientDuidLength', wintypes.ULONG),
		('Dhcpv6Iaid', wintypes.ULONG),
		('FirstDnsSuffix', POINTER(IP_ADAPTER_DNS_SUFFIX)),
	]
	def __getitem__(self,_k):
		if isinstance(_k,int):
			return self._fields_[_k]
		else:
			return self.__getattribute__(_k)

#ULONG WINAPI GetAdaptersAddresses(
#  _In_    ULONG                 Family,
#  _In_    ULONG                 Flags,
#  _In_    PVOID                 Reserved,
#  _Inout_ PIP_ADAPTER_ADDRESSES AdapterAddresses,
#  _Inout_ PULONG                SizePointer
#);
class GAA_FAMILY:
	AF_UNSPEC = 0 #both ipv4 & ipv6
	AF_INET = 2 #only ipv4
	AF_INET6 = 23 #only ipv6
	
class GAA_FLAGS:
	GAA_FLAG_SKIP_UNICAST = 0x01
	GAA_FLAG_SKIP_ANYCAST = 0x02
	GAA_FLAG_SKIP_MULTICAST = 0x04
	GAA_FLAG_SKIP_DNS_SERVER = 0x08
	GAA_FLAG_INCLUDE_PREFIX = 0x10
	GAA_FLAG_SKIP_FRIENDLY_NAME = 0x20
	GAA_FLAG_INCLUDE_WINS_INFO = 0x40
	GAA_FLAG_INCLUDE_GATEWAYS = 0x80
	GAA_FLAG_INCLUDE_ALL_INTERFACES = 0x100 #Return addresses for all NDIS interfaces. This flag is supported on Windows Vista and later.
	GAA_FLAG_INCLUDE_ALL_COMPARTMENTS = 0x200
	GAA_FLAG_INCLUDE_TUNNEL_BINDINGORDER = 0x400
	
def GetAdaptersAddresses_info(text=None):
	ipinfo = []
	if g_dll_handle is None:
		initialize_dll()
	hlib = g_dll_handle
	if hlib is None:
		return -1,''
	adapterIpAddr = IP_ADAPTER_ADDRESSES()
	padapter = cast(byref(adapterIpAddr), POINTER(IP_ADAPTER_ADDRESSES))
	ulOutBufLen = wintypes.ULONG(sizeof(adapterIpAddr))
	flags = c_uint(GAA_FLAGS.GAA_FLAG_INCLUDE_PREFIX|GAA_FLAGS.GAA_FLAG_INCLUDE_GATEWAYS|GAA_FLAGS.GAA_FLAG_INCLUDE_ALL_INTERFACES)
	print ('flags',flags,ulOutBufLen,padapter)
	ret = hlib.GetAdaptersAddresses( c_int(0), flags, c_void_p(0), byref(adapterIpAddr), byref(ulOutBufLen) )
	if ERROR_BUFFER_OVERFLOW == ret:
		print ('ERROR_BUFFER_OVERFLOW',flags,ulOutBufLen.value)
		adapterIpAddr = c_buffer(b'\0', ulOutBufLen.value + 16) #add aditonal 64 bytes
		padapter = cast(byref(adapterIpAddr), POINTER(IP_ADAPTER_ADDRESSES))
	elif 0 != ret:
		return (ret,ipinfo)
	
	ret = hlib.GetAdaptersAddresses( c_int(0), flags, c_void_p(0), byref(adapterIpAddr), byref(ulOutBufLen) )
	
	if ret != 0:
		return ret,padapter
	#info = [padapter.IfIndex, padapter.AdapterName, FirstUnicastAddress, FirstAnycastAddress, FirstMulticastAddress, FirstDnsServerAddress
	for _k in padapter.contents:#IP_ADAPTER_ADDRESSES._fields_:
		print (_k[0]),
		info = padapter.contents[_k[0]]
		if isinstance(info,wintypes.PCHAR):
			print ('\t %s'% string_at(info))
		elif isinstance(info,wintypes.PWCHAR):
			print ('\t %s'% wstring_at(info))
		elif isinstance(info,POINTER(IP_ADAPTER_UNICAST_ADDRESS)):
			print ('\t %s'% info.contents)
		else:
			print ('\t', info)
	#padapter = cast(padapter.contents.Next, POINTER(IP_ADAPTER_ADDRESSES))
	return ret,ipinfo
	
class IP_ADAPTER_INFO(Structure):
	_fields_ = [
        ('Next', c_void_p),
        ('ComboIndex', wintypes.DWORD),
        ('AdapterName', c_char*260),
        ('Description', c_char*132),
		('AddressLength', wintypes.UINT),
		('Address', 		c_ubyte*8),
		('Index', 			wintypes.DWORD),
		('Type', 			wintypes.UINT),
		('DhcpEnabled', 	wintypes.UINT),
		('CurrentIpAddress', 		POINTER(IP_ADDR_STRING)),
		('IpAddressList', 		IP_ADDR_STRING),
		('GatewayList', 		IP_ADDR_STRING),
		('DhcpServer', 		IP_ADDR_STRING),
		('HaveWins', 		wintypes.BOOL),
		('PrimaryWinsServer', 		IP_ADDR_STRING),
		('SecondaryWinsServer', 		IP_ADDR_STRING),
		('LeaseObtained', 		time_t),
		('LeaseExpires', 		time_t)
    ]
	__type__desc = {
		1: 'Type Other',
		6: 'Ethernet',
		9: 'TokenRing',
		15: 'FDDI',
		23: 'PPP',
		24: 'LoopBack',
		28: 'Slip'
	}
	def __get_type_str(self,net_type):
		type_str = 'unknown(%d)' %self.Type
		if self.Type in self.__type__desc:
			type_str = self.__type__desc[self.Type]
		return type_str
	def getdict(self):
		d = {}
		for k in self._fields_:
			d.setdefault(k, self.k)
		return d
	def __str__(self):
		type_str = self.__get_type_str(self.Type)
		
		#print 'CurrentIpAddress bool: ', bool(self.CurrentIpAddress)
		return "Description:\t%s\nMAC-Address:\t%s\nType:\t%s\tDhcpEnabled:\t%d%sObtained:\t%s\tExpires:\t%s" %(
			self.Description,
			''.join(['%02X-' % d for d in self.Address[0:self.AddressLength-1]])+'%02X' %self.Address[self.AddressLength-1],
			type_str,
			self.DhcpEnabled,
			linesep,
			self.LeaseObtained,
			self.LeaseExpires,
		) + linesep+linesep+ 'Address:\t'+str(self.IpAddressList) +linesep + 'Gateway:\t'+str(self.GatewayList) +linesep + 'DhcpServer:\t'+str(self.DhcpServer)

def initialize_dll():
	global g_dll_handle
	g_dll_handle = windll.LoadLibrary("IPHLPAPI.dll")

#do initialize when load 
initialize_dll()

def wait_ipaddr_change():
	if g_dll_handle is None:
		return
	hlib = g_dll_handle
	hand = wintypes.HANDLE();
	hand.value = 0
	return hlib.NotifyAddrChange(byref(hand), 0);
	
def get_adapters_info(text=None):
	ipinfo = []
	#print 'net'
	if g_dll_handle is None:
		initialize_dll()
	hlib = g_dll_handle
	if hlib is None:
		return -1,''
	adapter = IP_ADAPTER_INFO()
	padapter = cast(byref(adapter), POINTER(IP_ADAPTER_INFO))
	ulOutBufLen = wintypes.ULONG(sizeof(adapter))
	
	ret = hlib.GetAdaptersInfo( byref(adapter), byref(ulOutBufLen) )
	if ERROR_BUFFER_OVERFLOW == ret:
		adapter = c_buffer(b'\0', ulOutBufLen.value + 128) #add aditonal 64 bytes
		padapter = cast(byref(adapter), POINTER(IP_ADAPTER_INFO))
	elif 0 != ret:
		return (ret,ipinfo)
	
	ret = hlib.GetAdaptersInfo( byref(adapter), byref(ulOutBufLen) )
	
	if ret == 0:
		while padapter is not None:
			ip_addr = str(padapter.contents.IpAddressList)
			gw_addr = str(padapter.contents.GatewayList)
			desc = str(padapter.contents.Description)
			
			#print ('desc',padapter.contents.Description,type(padapter.contents.Description),padapter.contents.Next)
			desc = desc.strip()
			if text != None: #get the adapter of the given text description
				text = text.strip()
				if desc.endswith(text):
					ipinfo.append((padapter.contents.Description, ip_addr, gw_addr, 
					''.join(['%02X-' % d for d in padapter.contents.Address[0:padapter.contents.AddressLength-1]])+'%02X' %padapter.contents.Address[padapter.contents.AddressLength-1],
					padapter.contents.DhcpEnabled,
					str(padapter.contents.LeaseObtained),
					str(padapter.contents.LeaseExpires),
					str(padapter.contents)))
					
					break
			else:
				ipinfo.append((padapter.contents.Description, ip_addr, gw_addr, 
				''.join(['%02X-' % d for d in padapter.contents.Address[0:padapter.contents.AddressLength-1]])+'%02X' %padapter.contents.Address[padapter.contents.AddressLength-1],
				padapter.contents.DhcpEnabled,
				str(padapter.contents.LeaseObtained),
				str(padapter.contents.LeaseExpires),
				str(padapter.contents)))
			if bool(padapter.contents.Next) is True:
				padapter = cast(padapter.contents.Next, POINTER(IP_ADAPTER_INFO))
			else:
				padapter = None
	
	return (ret,ipinfo)

if __name__ == '__main__':
	ret,info = get_adapters_info()
	if 0 == ret:
		print (info)
	else:
		print ('get adapter info error')
	
	ret,info = GetAdaptersAddresses_info()
	if 0 == ret:
		print ('ok',info)
	else:
		print ('get adapter info error')
		