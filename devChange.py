#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
Copyright (C) 2010 dbzhang800
All rights reserved.
'''

import sys
import ctypes
import ctypes.wintypes as wintypes 
from PyQt4.QtCore import *
from PyQt4.QtGui import *

NULL = 0
INVALID_HANDLE_VALUE = -1
DBT_DEVTYP_DEVICEINTERFACE = 5
DEVICE_NOTIFY_WINDOW_HANDLE = 0x00000000
DBT_DEVICEREMOVECOMPLETE = 0x8004
DBT_DEVICEARRIVAL = 0x8000
WM_DEVICECHANGE = 0x0219

user32 = ctypes.windll.user32
RegisterDeviceNotification = user32.RegisterDeviceNotificationW
UnregisterDeviceNotification = user32.UnregisterDeviceNotification

class GUID(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8)]
                
class DEV_BROADCAST_DEVICEINTERFACE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("dbcc_size",  wintypes.DWORD), 
                ("dbcc_devicetype",  wintypes.DWORD), 
                ("dbcc_reserved",  wintypes.DWORD), 
                ("dbcc_classguid",  GUID), 
                ("dbcc_name",  ctypes.c_wchar*260)]

class DEV_BROADCAST_HDR(ctypes.Structure):
    _fields_ = [("dbch_size", wintypes.DWORD),
                ("dbch_devicetype", wintypes.DWORD),
                ("dbch_reserved", wintypes.DWORD)]


GUID_DEVCLASS_PORTS = GUID(0x4D36E978, 0xE325, 0x11CE,
        (ctypes.c_ubyte*8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18))
GUID_DEVINTERFACE_USB_DEVICE = GUID(0xA5DCBF10L, 0x6530,0x11D2, 
        (ctypes.c_ubyte*8)(0x90, 0x1F, 0x00,0xC0, 0x4F, 0xB9, 0x51, 0xED))


class Window(QWidget):
    def __init__(self,  parent=None):
        super(Window,  self).__init__(parent)
        self.resize(QSize(600,  320))
        self.setWindowTitle("Device Notify")
        self.setupNotification()
        vbox = QVBoxLayout(self)
        vbox.addWidget(QLabel("Log window:",  self))
        self.logEdit = QPlainTextEdit(self)
        vbox.addWidget(self.logEdit)
        self.setLayout(vbox)
        
    def setupNotification(self):
        dbh = DEV_BROADCAST_DEVICEINTERFACE()
        dbh.dbcc_size = ctypes.sizeof(DEV_BROADCAST_DEVICEINTERFACE)
        dbh.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE
        dbh.dbcc_classguid = GUID_DEVINTERFACE_USB_DEVICE #GUID_DEVCLASS_PORTS
        self.hNofity = RegisterDeviceNotification(int(self.winId()), 
                                                ctypes.byref(dbh), 
                                                DEVICE_NOTIFY_WINDOW_HANDLE)
        if self.hNofity == NULL:
            print ctypes.FormatError(), int(self.winId())
            print "RegisterDeviceNotification failed"
            
    def closeEvent(self,  evt):
        if self.hNofity:
            UnregisterDeviceNotification(self.hNofity)
        super(Window,  self).closeEvent(evt)

    def winEvent(self, message):
        if message.message == WM_DEVICECHANGE:
            self.onDeviceChanged(message.wParam, message.lParam)
            return True, id(message)
        return False, id(message)

    def onDeviceChanged(self, wParam, lParam):
        if DBT_DEVICEARRIVAL == wParam:
            self.logEdit.appendHtml("<font color=blue>Device Arrival:</font>")
        elif DBT_DEVICEREMOVECOMPLETE == wParam:
            self.logEdit.appendHtml("<font color=red>Device Removed:</font>")

        if (DBT_DEVICEARRIVAL == wParam or DBT_DEVICEREMOVECOMPLETE == wParam):
            dbh = DEV_BROADCAST_HDR.from_address(lParam)
            if dbh.dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE:
                dbd = DEV_BROADCAST_DEVICEINTERFACE.from_address(lParam)
                self.logEdit.appendPlainText(dbd.dbcc_name)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_())