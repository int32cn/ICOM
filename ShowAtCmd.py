#-*- encoding: gb2312 -*-
#/*****************************************************************************/
#/* FileName:     ShowAtCmd.py                                                */
#/* Description:  change hex code display to ascii display                    */
#/* CopyRight:     Huawei Technologies Co., Ltd.                              */
#/* Created By:   Chenjianzhong   00146421                                    */
#/* HISTORY VER:   1.0                                                        */
#/* VERSION:       2.0                                                        */
#/*****************************************************************************/

atCmd1 = '61 74 ' #"at"
atCmd2 = '41 54 ' #"AT"
atCmd3 = '0d 0a ' #"atCmd result"
atCmd4 = '61 2f ' #"a/"
atCmd5 = '41 2f ' #"A/"

sipCmds = ('INVITE','ACK','BYE','CANCEL','REGISTER','OPTIONS', #sip basic
			'UPDATE','INFO','SUBSCRIBER','NOTIFY','MESSAGE','PRACK','REFER','SIP', #sip extend
			'GET','PUT','POST','HTTP') #http

sipCmdsHex = []
#automatic guess ATS3 ATS4
ats3_auto = ''
ats4_auto = ''

import os,sys, re, string
#import traceback

def getSipKeyWords():
	global sipCmdsHex
	for cmd in sipCmds:
		cmd_l = ['%02x'%ord(i) for i in cmd]
		cmd_hex_str = ' '.join(cmd_l)
		#print (cmd,cmd_hex_str)
		sipCmdsHex.append(cmd_hex_str)
		sipCmdsHex.append(cmd_hex_str.swapcase())
	
def getAtKeyWords():
	return (atCmd1,atCmd2,atCmd3)
	
def setAtKeyWord(keyWord,keyWord1=None,keyWord2=None):
	global atCmd1,atCmd2,atCmd3,atCmd4,atCmd5
	atCmd1 = keyWord
	if keyWord1 is not None:
		atCmd2 = keyWord1
	if keyWord2 is not None:
		atCmd3 = keyWord2
	
#def is_valid_hex(ch):
#	return (ch >='0' and ch <='9') or (ch >= 'a' and ch <= 'f') or (ch >= 'A' and ch <= 'F')
	
def is_valid_char(lineLen, pos, line_str,be_strict=None):
	if pos < 0 or pos + 2 >= lineLen:
		return False
	offset = pos
	end_char_count = 0
	while offset + 2 < lineLen:
		be_err_char = False
		if be_strict is True and (offset - pos) < 10:
			if line_str[offset] != ' ' and line_str[offset+2] != ' ':
				return False
		cmdChar = line_str[offset]
		if cmdChar == ' ' or cmdChar == '\t' or cmdChar == '\r' or cmdChar == '\n':
			offset += 1
			continue
		cmdChar = line_str[offset:offset+2]
		offset += 2
		try:
			chrInt = int(cmdChar,16)
			if chrInt == 0x0a or chrInt == 0x0d or chrInt == 0x09:
				continue
			elif chrInt == 0x00:
				end_char_count += 1
				continue
			elif chrInt < 0x20 or chrInt >= 0x80:
				#print ('chrInt:%d,%s,%d\n'%(pos,cmdChar,chrInt))
				be_err_char = True
		except Exception as e:
			#print ('Exception in is_valid_char check:%s\n'%e)
			be_err_char = True
			pass
		
		if be_err_char is True:
			return False
		if be_strict is True and end_char_count > 3:
			return False
		if be_strict is None and offset > pos + 6:
			break
		
	return True

def re_sub_str_check(match_str):
	space_len = len(match_str.group('SS'))
	if space_len > 40:
		return ' '*(space_len-36)
	elif space_len > 14:
		return ' '*(space_len-10)
	elif space_len > 10:
		return ' '*(space_len-8)
	elif space_len > 6:
		return ' '*(space_len-4)
	else:
		return match_str.group('SS')

def get_cmd_pos(lineStr):
	if lineStr.find('IMS') > 0:
		for cmd_prefix in sipCmdsHex:
			_pos = lineStr.find(cmd_prefix)
			#print ('ims',cmd_prefix,_pos)
			yield _pos
	for cmd_prefix in (atCmd3,atCmd2,atCmd1,atCmd4,atCmd5):
		_pos = lineStr.find(cmd_prefix)
		yield _pos
	global ats3_auto,ats4_auto
	if ats3_auto != '' or ats4_auto != '':
		ats3s4_auto = '%02x %02x'%(ats3_auto, ats4_auto)
		_pos = lineStr.find(ats3s4_auto)
		if _pos < 0:
			ats3s4_auto = '%02X %02X'%(ats3_auto, ats4_auto)
			_pos = lineStr.find(ats3s4_auto)
		yield _pos
	
def changeAtDisplay(filePath) :
    if not os.path.isfile(filePath):
        print (filePath)
        print ("ERROR: Input param error")
        return 1
    
    fileSrc = open(filePath, 'r')
    if not fileSrc:
        return 2
    
    fileTar = open(filePath+".txt", 'w')
    if not fileTar:
        fileSrc.close()
        return 2
    
    getSipKeyWords()
    
    err_at_count = 0
    ok_at_count = 0
    ats3s4_auto_guess = False
    cur_is_guess_pos = False
    global ats3_auto
    global ats4_auto
    for lineStr in fileSrc :
        newLine = lineStr
        lineLen = len(newLine)
        pos = -1
        for pos_x in get_cmd_pos(lineStr):
            if is_valid_char(lineLen,pos_x,lineStr):
                pos = pos_x
                cur_is_guess_pos = False
                break
        
        if ats3s4_auto_guess is False and err_at_count >= (ok_at_count // 3):
            ats3s4_auto_guess = True
        if pos < 0 and ats3s4_auto_guess is True:
            for pos_x in range(0,lineLen-6):
                if is_valid_char(lineLen,pos_x,lineStr,True):
                    pos = pos_x
                    cur_is_guess_pos = True
                    break
        
        if pos >= 0 :
            #print "pos=%d"%(pos)
            newLineList = []
            newLine_start = re.sub(r'''((\w+) ){28,}''', '', lineStr[0:pos])
            cmdStr = lineStr[pos:]
            #print cmdStr
            cmdCharArry = cmdStr.split(' ')
            for cmdChar in cmdCharArry :
                #print "cmdChar",  cmdChar
                #print len(cmdChar)
                if len(cmdChar) > 1 :
                    chrCode = ' '
                    #print cmdChar
                    try:
                        chrCode = chr(int(cmdChar,16))
                    except:
                        chrCode = " "
                    newLineList.append(chrCode)
                    #print "chrCode", chrCode
            newLine = ''.join(newLineList)
            if cur_is_guess_pos is True:
                ok_pos = newLine.find('OK')
                if ok_pos >= 2 and ok_pos + 4 <= len(newLine):
                    begin_s3s4 = newLine[ok_pos-2:ok_pos]
                    end_s3s4   = newLine[ok_pos+2:ok_pos+4]
                    if begin_s3s4 == end_s3s4:
                        ats3_auto = ord(begin_s3s4[0])
                        ats4_auto = ord(begin_s3s4[1])
            newLine = newLine_start + newLine.replace('\r','\\r').replace('\n','\\n').replace('\0','\\0')
            ok_at_count += 1
        else:
            err_at_count += 1
            
        newLine = re.sub(r'''(?P<SS>(\s)+)''', re_sub_str_check, newLine)
        fileTar.write(newLine)
        fileTar.write('\n')
        
    fileSrc.close()
    fileTar.close()
    return 0
    
if __name__ == '__main__':
    #print ProjDef[0][3]["ap_wlan"]
    if len(sys.argv) < 2 :
        print ("ERROR: too few params! ")
        sys.exit(1)
    if 0 != changeAtDisplay(sys.argv[1]) :         
        print ("translate file %s fails"%(sys.argv[1]))
        sys.exit(2)
