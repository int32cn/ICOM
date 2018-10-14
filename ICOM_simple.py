#!/usr/bin/python
# -*- coding= utf-8 -*-

from ICOM_P_simple import icom_main,multiprocessing
import sys

if __name__ == '__main__':
	multiprocessing.freeze_support()
	icom_main(sys.argv)
	