import ctypes
import os


def comports(guid_class_id,available_only=True):
    """This generator scans the device registry for com ports and yields port, desc, hwid.
       If available_only is true only return currently existing ports."""
    
    if guid_class_id != "NET":
        for dwIndex in range(128):
            if os.path.exists("/dev/ttyUSB%d" % dwIndex):
                szFriendlyName = "/dev/ttyUSB%d" % dwIndex
                yield szFriendlyName, 'xxxx', 'yyyy'
            elif os.path.exists("/dev/tty%d" % dwIndex):
                szFriendlyName = "/dev/tty%d" % dwIndex
                yield szFriendlyName, szFriendlyName, 'yyyy'
    else:
        yield "x", "", ""


if __name__ == '__main__':
    for desc, hwid, GUID in comports('COM',True):
        print "%s (%s) %s" % (desc, hwid, GUID)
        try:
			import serial
			#print " "*10, serial.Serial(port) #test open
        except:
			print 'open fail', port
    
    # list of all ports the system knows
    print "-"*60
    for desc, hwid, GUID in comports('NET',True):
        print "%s (%s) {%s}" % (desc, hwid, GUID)

