#!/usr/bin/python
# -*- coding= utf-8 -*-

import logging
from sys import stdout as sys_stdout

#CRITICAL > ERROR > WARNING > INFO > DEBUG > NOTSET
logging.basicConfig(level=logging.ERROR,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='myapp.log',
                filemode='w')

stream_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%H:%M:%S',)
#file_formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)  

logger = logging.getLogger("icom")  
#file_handler = logging.FileHandler("mytest.log")
#file_handler.setLevel(logging.INFO)
#file_handler.setFormatter(file_formatter)
stream_handler = logging.StreamHandler(sys_stdout)
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(stream_formatter)  
#logger.addHandler(file_handler)  
logger.addHandler(stream_handler)

