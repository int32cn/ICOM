# mysetup.py
from distutils.core import setup
import py2exe

#setup(windows=["ICOM.py"])
py2exe_options = {"py2exe": {
    "compressed": 2,  
    "optimize": 2,
	'dist_dir':'ICOM_APP',
    "bundle_files": 1,
	#"packages":,
    #"dll_excludes": ["mswsock.dll", "powrprof.dll"],  
    "excludes": ["email", "System", "clr"],  
    #"typelibs": [("{A435DD76-804E-4475-8FAB-986EACD1C6BE}", 0x0, 1, 0), ]  
	}
}
setup(
	name = 'ICOM for nt',  
	description = 'Simple COM tool for windows. Contact shujunwei@qq.com for any suggestion.',
	version = '1.0', 
	author = 'shujunwei',
	author_email = 'shujunwei@qq.com',
    data_files=['icon.icon'],  
    #windows=[{
	console=[{
        'script': 'ICOM.py',
		'copyright':'Free of use and distribute.',
        "icon_resources": [
			(1, './icon.ico')
        ]}], 
	windows=[{
        'script': 'ser.py',
		'copyright':'Free of use and distribute.',
        "icon_resources": [
			(1, './icon.ico')
        ]}],
    #zipfile=None,#'core.lib',  
	#zipfile='core.lib',
    options=py2exe_options  
)


#then run mysetup.py as following:
#python mysetup.py py2exe
