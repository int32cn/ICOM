# -*- mode: python -*-

_out_file = open('D:\\ICOM_C\\ICOM\out_modules.txt','w')
_out_file_r = open('D:\\ICOM_C\\ICOM\out_modules_r.txt','w')

def write_out_module_file(f,a):
    def _do_write_group(titile_str,g):
        _count = len(g)
        f.writelines('%s:%d\n'%(titile_str,_count))
        for i in range(0,_count):
            f.writelines('\t%s\n'%repr(g[i]))
        f.writelines('\n')
    _do_write_group('pure',a.pure)
    _do_write_group('binaries',a.binaries)
    _do_write_group('zipfiles',a.zipfiles)
    _do_write_group('datas',a.datas)
    f.close()

def _do_remove_spec_module(a,spec_m_list):
    def x_module_name_match(m,spec_m_list):
        if 3 == len(m):
            if os.path.basename(m[1]) in spec_m_list:
                return True
        return False
    def x_check_module_group(mg):
        modules_copy = mg[0:]
        for m in modules_copy:
            if x_module_name_match(m,spec_m_list) is True:
                mg.remove(m)
    x_check_module_group(a.pure)
    x_check_module_group(a.binaries)
    x_check_module_group(a.zipfiles)
    x_check_module_group(a.datas)

def _do_remove_spec_codec(a,spec_c_list):
    def x_codec_name_match(m,spec_c_list):
        if 3 == len(m):
            if m[0].startswith('encodings.cp') or m[0].startswith('encodings.iso') or m[0].startswith('encodings.mac') or m[0].startswith('encodings.gb'):
                codec_name = m[0].replace('encodings.','')
                if codec_name not in spec_c_list:
                    return True
        return False
    def x_check_codec_group(mg):
        modules_copy = mg[0:]
        for m in modules_copy:
            if x_codec_name_match(m,spec_c_list) is True:
                mg.remove(m)
    x_check_codec_group(a.pure)
    x_check_codec_group(a.binaries)
    x_check_codec_group(a.zipfiles)
    x_check_codec_group(a.datas)
    

block_cipher = None


a = Analysis(['D:\\ICOM_C\\ICOM.py'],
             pathex=['D:\\pyinstall\\pyinstaller-3.0\\ICOM'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
write_out_module_file(_out_file,a)
_del_list = ['cp932.pyc',
            #'msvcr90.dll','msvcp90.dll','msvcm90.dll',
            'IPHLPAPI.dll','_ssl.pyd','kernel32.dll','bz2.pyd',
            'urllib2.pyc','bz2_codec.pyc','ssl.pyc','palmos.pyc','pyconfig.h','difflib.pyc',
            'sample.tcl','sample2.tcl','demo.tcl','winico.html','manpage.css','smiley.ico','tkchat.ico']

_reserve_codec_list = ['gb2312','cp936',]

_do_remove_spec_module(a,_del_list)
_do_remove_spec_codec(a,_reserve_codec_list)

write_out_module_file(_out_file_r,a)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [('cmdlist.xml','D:\\ICOM_C\\cmdlist.xml','DATA'),('license.txt','D:\\ICOM_C\\license.txt','DATA')],
          [('data.bin','D:\\ICOM_C\\data.bin','DATA'),('dataCommon.bin','D:\\ICOM_C\\dataCommon.bin','DATA')],
          [('icon.ico','D:\\ICOM_C\\icon.ico', 'DATA'),('earth.ico','D:\\ICOM_C\\earth.ico', 'DATA')],
          name='ICOM',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon='D:\\ICOM_C\\earth.ico')

exe_g = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [('cmdlist.xml','D:\\ICOM_C\\cmdlist.xml','DATA'),('license.txt','D:\\ICOM_C\\license.txt','DATA')],
          [('data.bin','D:\\ICOM_C\\data.bin','DATA'),('dataCommon.bin','D:\\ICOM_C\\dataCommon.bin','DATA')],
          [('icon.ico','D:\\ICOM_C\\icon.ico', 'DATA'),('earth.ico','D:\\ICOM_C\\earth.ico', 'DATA')],
          name='ICOM_g',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          icon='D:\\ICOM_C\\icon.ico')

exe_d = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [('cmdlist.xml','D:\\ICOM_C\\cmdlist.xml','DATA'),('license.txt','D:\\ICOM_C\\license.txt','DATA')],
          [('data.bin','D:\\ICOM_C\\data.bin','DATA'),('dataCommon.bin','D:\\ICOM_C\\dataCommon.bin','DATA')],
          [('icom.bin','D:\\ICOM_C\\icom.rar','DATA')],
          [('icon.ico','D:\\ICOM_C\\icon.ico', 'DATA'),('earth.ico','D:\\ICOM_C\\earth.ico', 'DATA')],
          name='ICOM_d',
          debug=True,
          strip=False,
          upx=False,
          console=True,
          icon='D:\\ICOM_C\\icon.ico')


