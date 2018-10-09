import	ctypes
dllkernel32 = ctypes.windll.kernel32

CreateSemaphore      = dllkernel32.CreateSemaphoreW
ReleaseSemaphore     = dllkernel32.ReleaseSemaphore
WaitForSingleObject  = dllkernel32.WaitForSingleObject
CloseHandle          = dllkernel32.CloseHandle
GetLastError         = dllkernel32.GetLastError

g_instance_sema_handle = None
g_only_instance_sema_handle = None

ERROR_ALREADY_EXISTS = 183

WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT  = 0x00000102

def check_the_only_instance(semaphore_name):
	global g_only_instance_sema_handle
	only_instance = False
	new_buf = ctypes.create_unicode_buffer('\0' * 258)
	new_buf.value = "icom_only_sema%s"%semaphore_name
	sema_handle = CreateSemaphore(0, ctypes.c_long(0), ctypes.c_long(1), ctypes.byref(new_buf))
	lst_err = GetLastError()
	del new_buf
	if lst_err and lst_err != ERROR_ALREADY_EXISTS and sema_handle:
		print('only instance err %d'%lst_err)
		
	if sema_handle and lst_err == 0:
		only_instance = True
		g_only_instance_sema_handle = sema_handle
	elif sema_handle:
		CloseHandle(sema_handle)
	
	return only_instance

def	get_instance_num(max_instance, semaphore_name):
	global g_instance_sema_handle
	if check_the_only_instance(semaphore_name):
		return 0
	
	sema_val = ctypes.c_long(max_instance + 1)
	new_buf = ctypes.create_unicode_buffer('\0' * 258)

	new_buf.value = "icom_sema%s"%semaphore_name
	g_instance_sema_handle = CreateSemaphore(0, ctypes.c_long(max_instance), ctypes.c_long(max_instance), ctypes.byref(new_buf))

	if not g_instance_sema_handle:
		del new_buf
		return sema_val.value
	else:
		wait_semaphore_ret	=	WaitForSingleObject(g_instance_sema_handle, 100);
		
		if	(WAIT_OBJECT_0	==	wait_semaphore_ret):
			ReleaseSemaphore(g_instance_sema_handle, ctypes.c_long(1), ctypes.byref(sema_val))
			if 0 < sema_val.value <= max_instance:
				sema_val.value = max_instance - sema_val.value + 1
		
		print	("wait_semaphore_ret:%s"%wait_semaphore_ret)
	del new_buf
	return sema_val.value

def pyi_add_instance_num():
	if g_instance_sema_handle:
		WaitForSingleObject(g_instance_sema_handle, 100);


def pyi_release_instance_num():
	sema_val = ctypes.c_long(0)
	global g_instance_sema_handle
	if g_instance_sema_handle:
		ReleaseSemaphore(g_instance_sema_handle, 1, ctypes.byref(sema_val))
		CloseHandle(g_instance_sema_handle)
		g_instance_sema_handle = 0
	if g_only_instance_sema_handle:
		CloseHandle(g_only_instance_sema_handle)
		
if __name__ == '__main__':
	num = get_instance_num(10, "my-sema-test-py")
	print ('num:%d'%num)
	pyi_add_instance_num()
	pyi_release_instance_num()
	print (check_the_only_instance("my-sema-test-py"))
	print (check_the_only_instance("my-sema-test-py"))
	print (check_the_only_instance("my-sema-test-py"))
	input()

	