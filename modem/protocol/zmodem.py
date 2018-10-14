import datetime
import os
import time
from modem.base import Modem
from modem.const import *
from modem.tools import log
from functools import reduce

class ZMODEM(Modem):
    '''
    ZMODEM protocol implementation, expects an object to read from and an
    object to write to.
    '''
    SENDER_WAIT_INTI = 0x10
    SENDING_ZRQINIT = 0x11
    SENDING_ZFILE = 0x12
    WAITING_ZPOS = 0x13
    SENDING_ZDATA = 0x14
    SENDING_DATAFRAME = 0x15
    SENDING_ZFIN  = 0x16
    SENDING_ONE_DONE_AND_HAS_NEXT_FILE = 0x17
    SEND_ALL_DONE = 0x18
    SENDING_ABORT_ZFIN = 0x19
    SEND_ALL_DONE_ABORT = 0x20
    SENDING_SKIP = 0x21
    SENDING_ZFILE_NEXT = 0x22
    
    def recv(self, basedir, retry=16, timeout=60, delay=1):
        '''
        Receive some files via the ZMODEM protocol and place them under
        ``basedir``::

            >>> print modem.recv(basedir)
            3

        Returns the number of files received on success or ``None`` in case of
        failure.

        N.B.: currently there are no control on the existence of files, so they
        will be silently overwritten.
        '''
        # Loop until we established a connection, we expect to receive a
        # different packet than ZRQINIT
        kind = TIMEOUT
        zrinit_cnt = 0
        while kind != ZFILE and zrinit_cnt < retry:
            if kind in [TIMEOUT, ZRQINIT]:
                self._send_zrinit(timeout)
            zrinit_cnt += 1
            kind = self._recv_header(timeout)[0]
            log.info('ZMODEM rec:%d'%kind)
            if kind == ZABORT:
                break
        if zrinit_cnt >= retry or kind != ZFILE:
            return
        log.info('ZMODEM connection established')

        zrinit_cnt = 0
        # Receive files
        while zrinit_cnt < retry:
            if kind == ZFILE:
                self._recv_file(basedir, timeout, retry)
                kind = TIMEOUT
                zrinit_cnt = 0
            elif kind == ZFIN:
                break
            else:
                log.info('Did not get a file offer? Sending position header')
                self._send_pos_header(ZRPOS, 0, timeout)
                zrinit_cnt += 1

            while kind is TIMEOUT and zrinit_cnt < retry:
                self._send_zrinit(timeout)
                zrinit_cnt += 1
                kind = self._recv_header(timeout)[0]

        if zrinit_cnt >= retry:
            return
        # Acknowledge the ZFIN
        log.info('Received ZFIN, done receiving files')
        self._send_hex_header([ZFIN, 0, 0, 0, 0], timeout)

        # Wait for the over and out sequence
        while kind not in [ord('O'), TIMEOUT]:
            kind = self._recv(timeout)

        if kind is not TIMEOUT:
            while kind not in [ord('O'), TIMEOUT]:
                kind = self._recv(timeout)

    def _recv(self, timeout):
        # Outer loop
        CAN_CODE = ord(CAN)
        while True:
            while True:
                char = self._recv_raw(timeout)
                if char is TIMEOUT:
                    return TIMEOUT

                if char == ZDLE:
                    break
                elif char in [0x10, 0x90, 0x11, 0x91, 0x13, 0x93]:
                    continue
                else:
                    # Regular character
                    return char

            # ZDLE encoded sequence or session abort
            eschar = self._recv_raw(timeout)
            if eschar is TIMEOUT:
                return TIMEOUT

            #if eschar in [0x11, 0x91, 0x13, 0x93, ZDLE]:
            #    print("unexpected1:0x%x"%char)
            ##    char = self._recv_raw(timeout)
            #    if char is TIMEOUT:
            #        return TIMEOUT
            
            if eschar == CAN_CODE:
                eschar = self._recv_raw(timeout)
                if eschar is TIMEOUT:
                    return TIMEOUT
            if eschar == CAN_CODE:
                eschar = self._recv_raw(timeout)
                if eschar is TIMEOUT:
                    return TIMEOUT
            if eschar == CAN_CODE:
                eschar = self._recv_raw(timeout)
                if eschar is TIMEOUT:
                    return TIMEOUT
            # Special cases
            if eschar in [ZCRCE, ZCRCG, ZCRCQ, ZCRCW]:
                return eschar | ZDLEESC
            elif eschar == ZRUB0:
                return 0x7f
            elif eschar == ZRUB1:
                return 0xff
            elif eschar == CAN_CODE:
                return ZCAN
            else:
                # Escape sequence
                if eschar & 0x60 == 0x40:
                    return eschar ^ 0x40
                break
        #print ('ch:0x%x,0x%x'%(char, eschar))
        return INVDATA
    def _recv_raw(self, timeout):
        char = self.getc(1, timeout)
        if char == '' or char == b'' or char == TIMEOUT:
            return TIMEOUT
        if isinstance(char, bytes):
            char = ord(char)
        #print('[%d]'%char)
        return char

    def _recv_data(self, ack_file_pos, timeout):
        zack_header = [ZACK, 0, 0, 0, 0]
        pos = ack_file_pos

        if self._recv_bits == 16:
            sub_frame_kind, data = self._recv_16_data(timeout)
        elif self._recv_bits == 32:
            sub_frame_kind, data = self._recv_32_data(timeout)
        else:
            raise TypeError('Invalid _recv_bits size')

        print("sub_frame:0x%02x"%sub_frame_kind)
        # Update file positions
        if sub_frame_kind is INVDATA:
            #raise Exception("invalid data")
            return INVDATA, b''
        if sub_frame_kind is TIMEOUT:
            return TIMEOUT, b''
        else:
            pos += len(data)

        # Frame continues non-stop
        if sub_frame_kind == ZCRCG:
            return FRAMEOK, data
        # Frame ends
        elif sub_frame_kind == ZCRCE:
            return ENDOFFRAME, data
        # Frame continues; ZACK expected
        elif sub_frame_kind == ZCRCQ:
            self._send_pos_header(ZACK, pos, timeout)
            return FRAMEOK, data
        # Frame ends; ZACK expected
        elif sub_frame_kind == ZCRCW:
            self._send_pos_header(ZACK, pos, timeout)
            return ENDOFFRAME, data
        else:
            return INVDATA, data

    def _recv_16_data(self, timeout):
        char = 0
        data = []
        mine = 0
        while char < 0x100:
            char = self._recv(timeout)
            if char is INVDATA:
                return INVDATA, b''
            elif char is TIMEOUT:
                log.error('Invalid b16 data timeout: %d'%len(data))
                return TIMEOUT, b''
            elif char is ZCAN:
                return ZCAN, b''
            elif char < 0x100:
                mine = self.calc_crc16(char & 0xff, mine)
                #log.info("%02x"%char)
                data.append(bytes([char]))

        # Calculate our crc, unescape the sub_frame_kind
        sub_frame_kind = char ^ ZDLEESC
        mine = self.calc_crc16(sub_frame_kind, mine)
        #log.info("ch:0x%02x,crc:0x%08x"%(sub_frame_kind,mine))
        # Read their crc
        rcrc  = self._recv(timeout) << 0x08
        rcrc |= self._recv(timeout)

        if mine != rcrc:
            log.error('Invalid b16 data My CRC = %08x, theirs = %08x, len:%d' % (mine, rcrc, len(data)))
            return INVDATA, b''
        else:
            return sub_frame_kind, b''.join(data)

    def _recv_32_data(self, timeout):
        char = 0
        data = []
        mine = 0
        while char < 0x100:
            char = self._recv(timeout)
            if char is TIMEOUT:
                return TIMEOUT, ''
            elif char < 0x100:
                mine = self.calc_crc32(bytes([char & 0xff]), mine)
                data.append(bytes([char]))

        # Calculate our crc, unescape the sub_frame_kind
        sub_frame_kind = char ^ ZDLEESC
        mine = self.calc_crc32(bytes([sub_frame_kind]), mine)

        # Read their crc
        rcrc  = self._recv(timeout)
        rcrc |= self._recv(timeout) << 0x08
        rcrc |= self._recv(timeout) << 0x10
        rcrc |= self._recv(timeout) << 0x18

        if mine != rcrc:
            log.error('Invalid b32 data My CRC = %08x, theirs = %08x len:%d' % (mine, rcrc, len(data)))
            return timeout, b''
        else:
            return sub_frame_kind, b''.join(data)

    def _recv_header(self, timeout, errors=10):
        header_length = 0
        error_count = 0
        char = None
        continues_can_ch_cnt = 0
        while header_length <= 0:
            # Frist ZPAD
            while char != ZPAD:
                char = self._recv_raw(timeout)
                if char is TIMEOUT:
                    return [TIMEOUT]
                if char is ZDLE: 
                    continues_can_ch_cnt += 1
                    if continues_can_ch_cnt >= 5:
                        return [ZCAN]
                else:
                    continues_can_ch_cnt = 0
                
            # Second ZPAD
            char = self._recv_raw(timeout)
            if char == ZPAD:
                # Get raw character
                char = self._recv_raw(timeout)
                if char is TIMEOUT:
                    return [TIMEOUT]

            # Spurious ZPAD check
            if char != ZDLE:
                continue

            # Read header style
            char = self._recv_raw(timeout)
            if char is TIMEOUT:
                return [TIMEOUT]
            
            if char == ZBIN:
                header_length, header = self._recv_bin16_header(timeout)
                self._recv_bits = 16
            elif char == ZHEX:
                header_length, header = self._recv_hex_header(timeout)
                self._recv_bits = 16
            elif char == ZBIN32:
                header_length, header = self._recv_bin32_header(timeout)
                self._recv_bits = 32
            else:
                error_count += 1
                if error_count > errors:
                    return [TIMEOUT]
                continue
        if header[0] != ZACK:
            log.info('GET header %d, %s'%(header_length, header))

        # We received a valid header
        
        return header

    def _recv_bin16_header(self, timeout):
        '''
        Recieve a header with 16 bit CRC.
        '''
        header = []
        mine = 0
        for x in range(0, 5):
            char = self._recv(timeout)
            if char is TIMEOUT:
                return 0, header
            else:
                mine = self.calc_crc16(char, mine)
                header.append(char)

        rcrc  = self._recv(timeout) << 0x08
        rcrc |= self._recv(timeout)

        if mine != rcrc:
            log.error('Invalid b16 header CRC = %04x, theirs = %04x' % (mine, rcrc))
            return 0, header
        else:
            return 5, header

    def _recv_bin32_header(self, timeout):
        '''
        Receive a header with 32 bit CRC.
        '''
        header = []
        mine = 0
        for x in range(0, 5):
            char = self._recv(timeout)
            if char is TIMEOUT:
                return 0, header
            else:
                mine = self.calc_crc32(bytes([char]), mine)
                header.append(char)

        # Read their crc
        rcrc  = self._recv(timeout)
        rcrc |= self._recv(timeout) << 0x08
        rcrc |= self._recv(timeout) << 0x10
        rcrc |= self._recv(timeout) << 0x18

        if mine != rcrc:
            log.error('Invalid b32 header CRC = %08x, theirs = %08x' % (mine, rcrc))
            return 0, header
        else:
            return 5, header

    def _recv_hex_header(self, timeout):
        '''
        Receive a header with HEX encoding.
        '''
        header = []
        mine = 0
        for x in range(0, 5):
            char = self._recv_hex(timeout)
            if char is TIMEOUT:
                return TIMEOUT, header
            mine = self.calc_crc16(char, mine)
            header.append(char)

        # Read their crc
        char = self._recv_hex(timeout)
        if char is TIMEOUT:
            return TIMEOUT, header
        rcrc = char << 0x08
        char = self._recv_hex(timeout)
        if char is TIMEOUT:
            return TIMEOUT, header
        rcrc |= char

        if mine != rcrc:
            log.error('Invalid hex header My CRC = %04x, theirs = %04x' % (mine, rcrc))
            return 0, header

        
        # Read to see if we receive a carriage return
        char = self._recv_raw(timeout)
        if (char&0x7F) == ord(b'\r'):
            # Expect a second one (which we discard)
            self._recv_raw(timeout)
        else:
            print('hex end:0x%2x'%char)
        return 5, header

    def _recv_hex(self, timeout):
        n1 = self._recv_hex_nibble(timeout)
        if n1 is TIMEOUT:
            return TIMEOUT
        n0 = self._recv_hex_nibble(timeout)
        if n0 is TIMEOUT:
            return TIMEOUT
        return (n1 << 0x04) | n0

    def _recv_hex_nibble(self, timeout):
        char = self.getc(1, timeout)
        if char is TIMEOUT:
            return TIMEOUT
        if isinstance(char, int):
            char = bytes([char])
        if char > b'9':
            if char < b'a' or char > b'f':
                # Illegal character
                return TIMEOUT
            #return ord(char) - ord('a') + 10
            return ord(char) - ord('a') + 10
        else:
            if char < b'0':
                # Illegal character
                return TIMEOUT
            return ord(char) - ord('0')

    def _recv_file(self, basedir, timeout, retry):
        log.info('About to receive a file in %s' % (basedir,))
        pos = 0

        # Read the data subpacket containing the file information
        kind, data = self._recv_data(pos, timeout)
        pos += len(data)
        if kind not in [FRAMEOK, ENDOFFRAME]:
            if not kind is TIMEOUT:
                # File info metadata corrupted
                self._send_znak(pos, timeout)
            return False

        # We got the file name
        part = data.split(b'\x00')
        filename = part[0]
        if not isinstance(basedir,bytes):
            basedir = bytes(basedir,"utf-8")
        filepath = os.path.join(basedir, os.path.basename(filename))
        fp = open(filepath, 'w+b')
        if not fp:
            log.error("open file [%s] err"%filepath)
            return False
        part = part[1].replace(b'  ',b' ').split(b' ')
        log.info('Meta %r' % (part,))
        size = int(part[0])
        # Date is octal (!?)
        date = datetime.datetime.fromtimestamp(int(part[1])) if len(part) > 1 and part[1] else b''
        # We ignore mode and serial number, whatever, dude :-)

        log.info('kind:%d Receiving file "%s" with size %d, mtime %s' % \
            (kind, filename, size, date))

        # Receive contents
        start = time.time()
        kind = ZFILE
        total_size = 0
        continues_no_file_data_received_cnt = 0
        while  continues_no_file_data_received_cnt < retry:
            kind, chunk_size = self._recv_file_data(kind, fp.tell(), fp, timeout)
            print('size %08d/%08d, %d'%(total_size, size, chunk_size))

            if chunk_size <= 0:
                continues_no_file_data_received_cnt += 1
            else:
                total_size += chunk_size
                continues_no_file_data_received_cnt = 0
            
            if size > 0 and total_size >= size and continues_no_file_data_received_cnt > 3:
                break
            if kind == ZEOF:
                break
 
        # End of file
        speed = (total_size / (time.time() - start))
        
        if kind == ZEOF:
            log.info('Receiving file "%s" done at %.02f bps' % (filename, speed))
        else:
            log.info('Receiving file "%s" Error at %.02f bps' % (filename, speed))
        # Update file metadata
        fp.close()
        #mtime = time.mktime(date.timetuple()) #TODO JJJ
        #os.utime(filepath, (mtime, mtime))    #TODO JJJ
        return True
    def _recv_file_data(self, kind, pos, fp, timeout):
        pos_header_send_cnt = 0
        dpos = -1
        if kind == ZFILE or kind == INVDATA or kind == TIMEOUT:
            self._send_pos_header(ZRPOS, pos, timeout)
        while dpos != pos:
            kind = 0
            while kind != ZDATA and kind != ZEOF:
                if kind is TIMEOUT:
                    if pos_header_send_cnt < 1:
                        self._send_pos_header(ZRPOS, pos, timeout)
                        pos_header_send_cnt += 1
                    else:
                        return TIMEOUT, 0
                else:
                    header = self._recv_header(timeout)
                    kind = header[0]
            
            # Read until we are at the correct block
            dpos = header[ZP0] | (header[ZP1] << 8) | (header[ZP2] << 16) | (header[ZP3] << 24)
            
            if kind == ZEOF and dpos <= pos:
                break
            if dpos != pos and pos_header_send_cnt < 1:
                self._send_pos_header(ZRPOS, pos, timeout)
                pos_header_send_cnt += 1
            
        if kind == ZEOF:
            return kind, 0
        # TODO: stream to file handle directly
        kind = FRAMEOK
        size = 0
        while kind == FRAMEOK:
            kind, chunk = self._recv_data(pos, timeout)
            if kind in [ENDOFFRAME, FRAMEOK]:
                fp.write(chunk)
                size += len(chunk)

        return kind, size

    def _send_znak(self, pos, timeout):
        self._send_pos_header(ZNAK, pos, timeout)

    def _send_pos_header(self, kind, pos, timeout):
        header = []
        if kind == ZACK:
            print("send ack:%d"%pos)
        elif kind == ZRPOS:
            print("send pos:%d"%pos)
        else:
            print("send header:0x%x 0x%04x"%(kind,pos))
        header.append(kind)
        header.append(pos & 0xff)
        header.append((pos >> 8) & 0xff)
        header.append((pos >> 16) & 0xff)
        header.append((pos >> 24) & 0xff)
        self._send_hex_header(header, timeout)

    def _get_hex(self,ch):
        ch &= 0xff
        return b'%x%x'%(ch >> 0x04, ch&0x0f)

    def _send_bin16_header(self, header, timeout):
        char_list = [ZPAD, ZDLE, ZBIN]
        # Update CRC
        for ch in header:
            char_list.extend(self._get_char_escape(ch))
        # Transmit the CRC
        crc16_val = self.calc_crc16(header, 0)
        char_list.extend(self._get_char_escape((crc16_val >> 8)&0xff))
        char_list.extend(self._get_char_escape(crc16_val&0xff))
        ret = self.putc(bytes(char_list))
        return -1 if ret < 0 else 0
    def _send_hex_header(self, header, timeout):
        bytes_list = [bytes([ZPAD, ZPAD, ZDLE, ZHEX])]
        bytes_list.extend([self._get_hex(ch) for ch in header])
        # calculate the CRC
        crc16_val = self.calc_crc16(header, 0)
        bytes_list.append(self._get_hex(crc16_val>>8))
        bytes_list.append(self._get_hex(crc16_val&0xff))
        bytes_list.append(b'\r\n')
        if header[0] != ZFIN and header[0] != ZACK:
            bytes_list.append(XON)
        #print(b''.join(bytes_list))
        ret = self.putc(b''.join(bytes_list), timeout)
    def _send_zrinit(self, timeout):
        log.debug('Sending ZRINIT header')
        header = [ZRINIT, 0, 0, 0, ZF0_CANFDX | CANOVIO | ZF0_CANFC32] #ZF0_TESCCTL
        self._send_hex_header(header, timeout)
    def _send_wakeup(self,timeout):
        self.putc(b'rz\r', timeout)
    def _send_zsqinit(self, timeout):
        header = [ZRQINIT, 0, 0, 0, 0]
        self._send_hex_header(header, timeout)
    def _get_char_escape(self,c):
        chr_list = []
        if c == 0xff:
            chr_list.append(ZDLE)
            chr_list.append(ZRUB1)
        elif c == 0x7f:
            chr_list.append(ZDLE)
            chr_list.append(ZRUB0)
        elif c in [0x10, 0x90, 0x11, 0x91, 0x13, 0x93]:
            chr_list.append(ZDLE)
            chr_list.append(c^0x40)
        elif c == ZDLE:
            chr_list.append(ZDLE)
            chr_list.append(ZDLEE)
        else:
            chr_list.append(c)
        return chr_list
    def _send_bin16_pos_header(self, kind, pos, timeout):
        header = []
        header.append(kind)
        header.append(pos & 0xff)
        header.append((pos >> 8) & 0xff)
        header.append((pos >> 16) & 0xff)
        header.append((pos >> 24) & 0xff)
        print("send b16 header:0x%x, pos:0x%x, %s"%(kind, pos, header))
        return self._send_bin16_header(header, timeout)
    def _write_zdle_data(self,frm_type,data,timeout):
        char_list = []
        for ch in data:
            #log.info("ch:0x%02x,crc:0x%08x"%(ch&0xff,crc16))
            char_list.extend(self._get_char_escape(ch))
        
        crc16 = self.calc_crc16(data, 0)
        crc16 = self.calc_crc16(frm_type, crc16)
        #print('frm:0x%x'%frm_type)
        #log.info("ch:0x%02x,crc:0x%08x"%(crc_byte&0xff,crc16))
        char_list.append(ZDLE)
        char_list.append(frm_type)
        char_list.extend(self._get_char_escape((crc16>>8)&0xff))
        char_list.extend(self._get_char_escape(crc16&0xff))
        ret = self.putc(bytes(char_list), timeout)
        return -1 if ret < 0 else 0
    def _send_zfile_header(self,filename,file_fize, m_time, files_to_tran, left_all_file_size, timeout):
        data = []
        if not isinstance(filename,bytes):
            try:
                filename = bytes(filename,'utf-8')
            except Exception as e:
                filename = bytes([ord(_) for _ in filename if ord(_) < 255])
        filename.replace(b'\\',b'/').replace(b'//',b'/')
        mode = 0
        trans_sn = 666
        data.append(b"%s\x00%d %d %d %d %d %d"%(filename, file_fize, m_time, mode, trans_sn, files_to_tran, left_all_file_size))
        data.append(b'\0')
        log.info("sendZFILE:%s"%filename)
        self._send_bin16_header([ZFILE, 0,0,6,3], timeout)
        return self._write_zdle_data(ZCRCW, b''.join(data), timeout)
    def _send_zdata_header(self,file_offset,timeout):
        return self._send_bin16_pos_header(ZDATA, file_offset, timeout)
    def _send_zeof_header(self,file_offset,timeout):
        self._send_pos_header(ZEOF, file_offset, timeout)
    def _send_zfin_header(self,file_offset,timeout):
        self._send_pos_header(ZFIN, file_offset, timeout)
    def _send_over_and_out(self):
        self.putc(b'OO')
    def _send_cancel_transfer(self):
        cancel_chrs = [24,24,24,24,24,24,24,24,8,8,8,8,8,8,8,8,8,8,0]
        self.putc(bytes(cancel_chrs))
    def _send_state_next(self, cur_state, header, is_eof, files_to_tran):
        next_state = cur_state
        kind = header[0]
        
        #equal state of transtion
        if cur_state == self.SENDING_ZFILE_NEXT:
            cur_state = next_state = self.SENDING_ZFILE
        
        if cur_state == self.SENDING_ZDATA and kind == ZACK:
            pass
        elif cur_state == self.SENDING_ZDATA and kind == ZRPOS:
            pass
        elif cur_state == self.SENDER_WAIT_INTI and kind == TIMEOUT:
            next_state = self.SENDING_ZRQINIT
        elif cur_state == self.SENDER_WAIT_INTI and kind == ZRINIT:
            next_state = self.SENDING_ZFILE
        elif cur_state == self.SENDING_ZRQINIT and kind == ZRINIT:
            next_state = self.SENDING_ZFILE
        elif cur_state == self.WAITING_ZPOS and kind == ZRINIT:
            next_state = self.SENDING_ZFILE
        elif cur_state == self.WAITING_ZPOS and kind == TIMEOUT:
            next_state = self.SENDING_ZFILE
        elif cur_state == self.SENDING_ZFILE and kind == ZRPOS:
            next_state = self.SENDING_ZDATA
        elif cur_state == self.SENDING_ZFILE and kind == ZSKIP:
            next_state = self.SENDING_SKIP
        elif cur_state == self.SENDING_ZFILE and kind == ZACK:
            next_state = self.SENDING_ZDATA
        elif cur_state == self.SENDING_ZFILE and kind == ZABORT:
            next_state = self.SENDING_ABORT_ZFIN
        elif cur_state == self.SENDING_ZFILE and kind == ZFERR:
            next_state = self.SENDING_ABORT_ZFIN
        elif cur_state == self.SENDING_ZFILE and kind == ZRINIT:
            next_state = self.WAITING_ZPOS
        elif cur_state == self.SENDING_ZDATA and kind == ZFERR:
            next_state = self.SENDING_ABORT_ZFIN
        elif cur_state == self.SENDING_ZDATA and kind == ZABORT:
            next_state = self.SENDING_ABORT_ZFIN
        elif cur_state == self.WAITING_ZPOS and kind == ZRPOS:
            next_state = self.SENDING_ZDATA
        elif cur_state == self.SENDING_ZDATA and kind == ZRINIT:
            if not is_eof:
                next_state = self.SENDING_ZFILE
            elif files_to_tran <= 1:
                next_state = self.SENDING_ZFIN
            else:
                next_state = self.SENDING_ONE_DONE_AND_HAS_NEXT_FILE
            #print("is_eof:%s files_to_tran:%d,next_state:0x%x"%(is_eof, files_to_tran,next_state))
        elif cur_state == self.SENDING_ZFIN and kind == ZFIN:
            next_state = self.SEND_ALL_DONE
        elif cur_state == self.SENDING_ZFIN and kind == ZABORT:
            next_state = self.SENDING_ABORT_ZFIN
        elif cur_state == self.SENDING_ZFIN and kind == ZRPOS:
            next_state = self.SENDING_ZDATA
        elif cur_state == self.SENDING_ABORT_ZFIN and kind == ZFIN:
            next_state = self.SEND_ALL_DONE_ABORT
        
        return cur_state,next_state
    def get_left_file_size(self, file_info_list,idx):
        if idx >= len(file_info_list):
            return 0
        else:
            return reduce(lambda x,y:x+y[1].st_size, file_info_list[idx:], 0)
    def send(self, pattern, retry=16, timeout=60, info_callback=None):
        # Get a list of files to send
        file_info_list = []
        try:
            if os.path.isdir(pattern):
                for dirpath, dirnames, topfilenames in os.walk(pattern):
                    file_info_list.extend([(os.path.join(dirpath,n),os.stat(os.path.join(dirpath,n))) for n in topfilenames])
                    for subdir in dirnames:
                        subdirpath,subdirnames,subfilenames = os.walk(os.path.join(dirpath,subdir))
                        file_info_list.extend([(os.path.join(dirpath,n),os.stat(os.path.join(dirpath,n))) for n in subfilenames])
            elif os.path.isfile(pattern):
                file_info_list.append((pattern,os.stat(pattern)))
        except Exception as e:
            log.error("zmodem get file err:%s"%e)
        if not file_info_list:
            return True
        
        DATA_SIZE_100K = 1024*100
        DATA_SIZE_1M  = 1014*1024
        DATA_SIZE_10M  = 1014*1024*10
        SUB_PACKERT_SIZE = 1024
        MIDDLE_SUB_PACKET_SIZE = 512
        MIN_SUB_PACKET_SIZE = 256
        SUB_PACKERT_ACK_PER = 16
        SUB_PACKERT_ACK_PER_MIN = 4
        SUB_PACKERT_ACK_PER_MAX = 128
        # initialize protocol
        error_count = 0
        crc_mode = 0
        zr_init_flags = 0
        zr_init_buffer_size = 0
        total_file_cnt = len(file_info_list)
        last_state = cur_state = self.SENDER_WAIT_INTI
        self._send_wakeup(timeout)
        self._send_zsqinit(timeout)

        for file_index, file_info in enumerate(file_info_list):
            if cur_state == self.SEND_ALL_DONE_ABORT:
                print("receiver abort")
                break
            filename = file_info[0]
            filestat = file_info[1]
            fd = open(filename, "rb")
            if not fd:
                print("open %s fail,skip"%filename)
                continue
            file_stat = os.fstat(fd.fileno())
            left_all_file_size = self.get_left_file_size(file_info_list, file_index)
            last_send_pos = send_pos = recv_ack_pos = recv_zpos = 0
            send_data_frame_idx = 0
            
            left_files_to_tran = total_file_cnt - file_index
            data_frame_packet_size = SUB_PACKERT_SIZE
            if file_stat.st_size < DATA_SIZE_100K:
                send_data_frame_cnt = SUB_PACKERT_ACK_PER_MIN
            elif file_stat.st_size > DATA_SIZE_10M:
                send_data_frame_cnt = SUB_PACKERT_ACK_PER_MAX
            elif file_stat.st_size > DATA_SIZE_1M: #1M ~ 10M
                send_data_frame_cnt = SUB_PACKERT_ACK_PER + ((file_stat.st_size - DATA_SIZE_1M)/DATA_SIZE_100K) * (SUB_PACKERT_ACK_PER_MAX - SUB_PACKERT_ACK_PER)/((DATA_SIZE_10M - DATA_SIZE_1M)/DATA_SIZE_100K)
            else: # 100K ~ 1M
                send_data_frame_cnt = SUB_PACKERT_ACK_PER_MIN + ((file_stat.st_size - DATA_SIZE_100K)//DATA_SIZE_100K) * (SUB_PACKERT_ACK_PER - SUB_PACKERT_ACK_PER_MIN)/((DATA_SIZE_1M - DATA_SIZE_100K)/DATA_SIZE_100K)
            
            send_data_frame_cnt = int(send_data_frame_cnt)
            debug_info = 'filename:%s, size:%d, frmcnt:%d\n'%(filename, file_stat.st_size, send_data_frame_cnt)
            if info_callback:
                info_callback(debug_info)
            else:
                print(debug_info)
            if file_index > 0 and (cur_state == self.SENDING_ONE_DONE_AND_HAS_NEXT_FILE or cur_state == self.SENDING_SKIP):
                last_state = cur_state = self.SENDING_ZFILE_NEXT
            else:
                last_state = cur_state = self.SENDER_WAIT_INTI
            continues_zpos_cnt = 0
            continues_start_zpos = 0
            end_of_file_send = False
            send_zdata_frame_type = 0
            send_data_err_cnt = 0
            error_count = 0
            file_data_need_async_ack = 0
            data_need_ack_time = 0
            percent_last = percent_now = 0
            while True:
                percent_last = percent_now
                last_state = cur_state
                last_send_pos = send_pos
                recv_zpos_get = False
                header_need_ack = file_data_need_sync_ack = False
                
                if last_state == self.SENDING_ZDATA:
                    if send_zdata_frame_type == ZCRCQ:
                        file_data_need_async_ack += 1
                        data_need_ack_time = time.time()
                    elif send_zdata_frame_type == ZCRCW:
                        file_data_need_sync_ack = True
                        data_need_ack_time = time.time()
                elif last_state != self.SENDING_ZFILE_NEXT:
                    header_need_ack = True
                
                if header_need_ack or file_data_need_sync_ack:
                    recv_timeout = 0.3 + file_data_need_async_ack * 0.1 + error_count * 0.03
                elif file_data_need_async_ack > 1:
                    recv_timeout = file_data_need_async_ack * 0.03
                else:
                    recv_timeout = 0.0

                header = self._recv_header(recv_timeout)
                #print('h:%s, sync:%s async:%d, er:%d ->%f'%(header_need_ack, file_data_need_sync_ack, file_data_need_async_ack, error_count, recv_timeout))
                header_type = header[0]
                
                if header_type == ZRPOS:
                    recv_zpos_get = True
                    recv_zpos = header[ZP0] | (header[ZP1] << 8) | (header[ZP2] << 16) | (header[ZP3] << 24)
                elif header_type == ZACK:
                    recv_ack_pos = header[ZP0] | (header[ZP1] << 8) | (header[ZP2] << 16) | (header[ZP3] << 24)
                    if not file_data_need_sync_ack and file_data_need_async_ack > 0:
                        file_data_need_async_ack -= 1
                elif header_type == ZRINIT:
                    zr_init_flags = header[ZF0] | (header[ZF1] << 8)
                    zr_init_buffer_size = header[ZP0] | (header[ZP1]<<8)
                    print (header, '0x%x'%zr_init_flags, zr_init_buffer_size)
                elif header_type != TIMEOUT:
                    print('header_type:0x%x'%header_type if header_type is not None else "None")
                
                last_state, cur_state = self._send_state_next(last_state, header, end_of_file_send, left_files_to_tran)
                percent_now = 1000*send_pos//(file_stat.st_size if file_stat.st_size > 0 else 1)
                if header_need_ack or file_data_need_sync_ack or file_data_need_async_ack or header_type != TIMEOUT or cur_state != last_state or percent_now != percent_last:
                    process_info = '%3d.%d%% send:%-6d ack:%-6d zrpos:%d%s \n'%(percent_now//10, percent_now%10, send_pos, recv_ack_pos, recv_zpos, '<N>' if recv_zpos_get else '')
                    debug_info = "0x%2x frm:%4d/%d %s"%(cur_state, send_data_frame_idx, send_data_frame_cnt, process_info)
                    if info_callback:
                        info_callback(debug_info)
                    else:
                        print(debug_info)
                
                if cur_state == last_state:
                    if cur_state == self.SENDING_ZDATA:
                        if file_data_need_sync_ack is True:
                            if header_type == TIMEOUT:
                                error_count += 1
                            elif error_count > 2:
                                error_count -= 2
                        elif file_data_need_async_ack > 3 and header_type == TIMEOUT:
                            error_count += 1
                    elif header_type == TIMEOUT:
                        error_count += 1
                        
                    if error_count > retry or send_data_err_cnt > retry:
                        self._send_cancel_transfer()
                        if info_callback:
                            info_callback("too many errors, abort\n")
                        break
                elif error_count > 0:
                    error_count -= 1
                
                if recv_zpos_get is True and recv_zpos < send_pos:
                    send_pos = recv_zpos
                    send_data_frame_idx = 0
                    continues_zpos_cnt += 1
                    if continues_zpos_cnt == 1:
                        continues_start_zpos = recv_zpos
                    if continues_zpos_cnt > 2 and send_data_frame_cnt >= 2:
                        send_data_frame_cnt -= 1
                    elif continues_zpos_cnt > (retry + retry + - 1)/ 3:
                        data_frame_packet_size = MIDDLE_SUB_PACKET_SIZE
                    elif continues_zpos_cnt > (retry + retry + - 1)/ 2:
                        data_frame_packet_size = MIN_SUB_PACKET_SIZE
                    elif continues_zpos_cnt > retry and continues_start_zpos == recv_zpos:
                        self._send_cancel_transfer()
                        if info_callback:
                            info_callback("too many errors, abort\n")
                        break
                else:
                    continues_zpos_cnt = 0
                
                if cur_state == self.SENDING_ZRQINIT:
                    if error_count > 1 and error_count%2 == 0:
                        self._send_wakeup(timeout)
                    self._send_zsqinit(timeout)
                elif cur_state == self.SENDING_ZFILE:
                    if self._send_zfile_header(filename, file_stat.st_size, file_stat.st_mtime, left_files_to_tran, left_all_file_size, timeout) < 0:
                        send_data_err_cnt += 1
                    else:
                        send_data_err_cnt = 0
                elif cur_state == self.SENDING_ZDATA:
                    if last_send_pos != send_pos:
                        fd.seek(send_pos)
                    data = fd.read(data_frame_packet_size)
                    data_len = len(data)
                    if send_data_frame_idx == 0 and data_len > 0:
                        if send_zdata_frame_type == ZCRCG or send_zdata_frame_type == ZCRCQ:
                            fd.seek(last_send_pos)
                            fill_end_pack_data = fd.read(4)
                            if self._write_zdle_data(ZCRCW, fill_end_pack_data, timeout) < 0:
                                send_data_err_cnt += 1
                            else:
                                send_data_err_cnt = 0
                            fd.seek(send_pos + data_len)
                        if self._send_zdata_header(send_pos, timeout) < 0:
                            send_data_err_cnt += 1
                        else:
                            send_data_err_cnt = 0
                    send_data_frame_idx += 1
                    send_pos += data_len
                    
                    if data_len == 0:
                        #file ends
                        end_of_file_send = True
                        self._send_zeof_header(send_pos,timeout)
                        send_zdata_frame_type = ZEOF
                        send_data_frame_idx = 0
                    elif (send_data_frame_idx % send_data_frame_cnt) ==  0:
                        if zr_init_buffer_size > 0 and zr_init_buffer_size <= send_data_frame_idx*data_frame_packet_size:
                            send_zdata_frame_type = ZCRCW
                            send_data_frame_idx = 0
                        elif zr_init_flags&CANFDX:
                            send_zdata_frame_type = ZCRCQ
                        else:
                            send_zdata_frame_type = ZCRCW
                            send_data_frame_idx = 0
                        if self._write_zdle_data(send_zdata_frame_type, data, timeout) < 0:#ZACK expected, end of frame
                            send_data_err_cnt += 1
                        else:
                            send_data_err_cnt = 0
                    elif data_len < data_frame_packet_size:
                        #file end, and we recheck if really file end
                        data_next = fd.read(data_frame_packet_size)
                        send_zdata_frame_type = ZCRCE if not data_next else ZCRCW
                        if self._write_zdle_data(send_zdata_frame_type, data, timeout) < 0:# CRCE no ZACK expected, end of frame/file
                            send_data_err_cnt += 1
                        else:
                            send_data_err_cnt = 0
                        send_data_frame_idx = 0
                        #do not read the data, for next loop, and do not care of file offst for we will feek again
                    else:
                        if zr_init_buffer_size > 0 and zr_init_buffer_size <= send_data_frame_idx*data_frame_packet_size:
                            send_zdata_frame_type = ZCRCW
                            send_data_frame_idx = 0
                        elif zr_init_flags&CANOVIO:
                            #atleast one ack every 3 seconds
                            if time.time() > data_need_ack_time + 3.0:
                                send_zdata_frame_type = ZCRCG
                            else:
                                send_zdata_frame_type = ZCRCG
                        else:
                            send_zdata_frame_type = ZCRCW
                            send_data_frame_idx = 0
                        if self._write_zdle_data(send_zdata_frame_type, data, timeout) < 0:#NO ZACK expected, continue of frame
                            send_data_err_cnt += 1
                        else:
                            send_data_err_cnt = 0
                    #print('tsts',ts1-ts, ts2-ts1, ts3-ts2, ts4-ts3)
                elif cur_state == self.SENDING_ZFIN:
                    self._send_zfin_header(send_pos,timeout)
                elif cur_state == self.SENDING_ABORT_ZFIN:
                    self._send_zfin_header(send_pos,timeout)
                    if info_callback:
                        info_callback("abort by receiver\n")
                elif cur_state == self.SENDING_ONE_DONE_AND_HAS_NEXT_FILE:
                    if info_callback:
                        info_callback("one file send done, and to send next file\n")
                    break
                elif cur_state == self.SENDING_SKIP:
                    if info_callback:
                        info_callback("file skiped by receiver\n")
                    break
                elif cur_state == self.SEND_ALL_DONE or cur_state == self.SEND_ALL_DONE_ABORT:
                    self._send_over_and_out()
                    if info_callback:
                        info_callback("send over and out\n")
                    break;
            fd.close() 
        return True if cur_state == self.SEND_ALL_DONE else False