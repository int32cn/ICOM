#!/usr/bin/python
# -*- coding= utf-8 -*-

import rsa
import rsa.bigfile as bigfile
import os
from hashlib import md5

n=0xd2f19713e618a7ee8338a835350ee7de1f3a1d05da35bc1e5f16e1a2b69cbbd674118154d526740690c2bbe9b6d8fbcfde0e422b91a2c8c87b154cabc8764602c2e4b537a146d2990151f4e13da9edeb1babd8229d49ec9e4a569e1642e55de98a83e7d136331dbcfa8c6974ce3fab646361854d8b488ca87a24f713f09940526f608c3383258b5c77acaa1d2003eea2791f7f4273cfc02c34c9ee030f8849e2b7aa7962684c1a92418928c47b4ed19bf15a3479a808f81ea77d414c8b44176f2ce16aa283e1f37fa6353161a916917df2e06c188bee7798a24380e174371fc42d7a4c539b85eb3f77f92c7e80cf95a22f955fd0419c5953ec25f8a6e974081d

e=0x10001

d=0xacbe854f195e559fa03c349ba600b7e711c18064fb8687b083847470d084d7da4e20cbbdd1f3f48e2fdc1910d2d92c95d4adee8849727a649b4f1d038c5d370629de2b7d0c08b88bee25d498e3eb95d7b4486cee23ca970825ae7b3595c0c9c067db8f6aa7ad028c70cdadcaa6e0431629c081eeb7c248d5366c495cee8cec80b95507940e8d60536ba4e9b71cd92efc8a16a39dfaf8af82ac78e938c2ec5c70a75716c3e00d60d3370d10359f2321366e43c0ef1555248c5be231f41dcdcfab904583f6eac8508d9eef76628303201c34fb2e620e6df3add4b3c090b7659ec66213167326551db11954671d14563defaa86f3e483ceace0d2e866d6f297cfa1

p=0xdd15ef9b685bf3b68b1c68b0355d8549485ac84bbcc7e4882e004e6cbe9db701f078fe805362fa1b384212625014d55d0f7dca3a05152f9e9974dd8ea3ccb8d738dba8924f325c37f1ee1bd3f1fab9fd5c9d0332171716e81538d964674d09134e3af1975227d54c5e897c8ff798b88105b8b389ef01d1e47425de24b07104c5eb595bfa39b656a9

g=0xf441a24339aae290d010a87548ddb5b66d91a44dd224f14f4e07bcfbf34a500c108641cc68eeb0a17b167f7b93025fa41508b96c984868460823e6035ff36dee6a71e52102abdebd341340ebd7d0978c667b1e78faac22f2dea907ca90079ace052a30967370fa494a3db37ffafd869338f5bd6ee0027255

default_pu=rsa.PublicKey(n,e)

default_pr=rsa.PrivateKey(n,e,d,p,g)

pem_data_f_name = 'data.bin'
pem_data_f_common_name = 'dataCommon.bin'

def _do_hash(msg):
	hasher = md5()
	hasher.update(msg)
	return hasher.digest()

def save_pem_data(f_path,pr):
	infile = pr.open('plain.txt','rb')
	outfile = open(os.path.join(f_path,pem_data_f_name),'wb+')
	bigfile.encrypt_bigfile(infile, outfile, default_pu)
	infile.close()
	outfile.close()

def save_pem_data_common(f_path,pr):
	infile = pr.open('plain.txt','rb')
	outfile = open(os.path.join(f_path,pem_data_f_common_name),'wb+')
	bigfile.encrypt_bigfile(infile, outfile, default_pu)
	infile.close()
	outfile.close()

class KTemp_buffer():
	def __init__(self):
		self.offset = 0
		self._hash_val = b''
		self.__data = []
	def open(self,*args):
		self.__int__()
	def close(self):
		self.offset = 0
		self.__data = None
	def write(self,bytes):
		self.__data.append(bytes)
	def set_hash(self,hash_val):
		self._hash_val = hash_val
	def get(self):
		return self._hash_val+b''.join(self.__data)

def get_auth_key_info():
	d = os.urandom(32)
	e = rsa.encrypt(d,default_pu)
	print (d,e)
	print (len(d),len(e))
	print (sign(d))
	return e

def parse_data(data):
	if type(data) != type(b''):
		return data
	if not data.startswith(b'PrivateKey('):
		return None
	datalist = data.replace(b' ',b'').replace(b')',b'').split(b',')
	if len(datalist) != 5:
		return None
	n = int(datalist[0].replace(b'PrivateKey(',b''),16)
	e = int(datalist[1],16)
	d = int(datalist[2],16)
	p = int(datalist[3],16)
	g = int(datalist[4],16)
	
	return rsa.PublicKey(n,e),rsa.PrivateKey(n,e,d,p,g)

def _load_pem_data_(f_path,f_name):
	data = (None,None)
	try:
		data_path = os.path.join(f_path,f_name)
		infile = open(data_path,'rb')
		outfile = KTemp_buffer()
		bigfile.decrypt_bigfile(infile, outfile, default_pr)
		infile.close()
		data = outfile.get()
		outfile.close()
		data = parse_data(data)
	except Exception as e:
		print('load pem data %s failed(%s)\n'%(f_path,e))
		#logger.warning('load pem data %s failed\n'%f_path)
		pass
	return data

def load_pem_data(f_path):
	return _load_pem_data_(f_path,pem_data_f_name)
def load_pem_data_common(f_path):
	return _load_pem_data_(f_path,pem_data_f_common_name)

def decrypt_data_common(data,dataLen,prk=default_pr,do_hash=None):
	if prk is None:
		return data
	en_len = 0
	if do_hash is not None and hasattr(do_hash, '__call__'):
		hash_val = do_hash(b'')
		hash_len = len(hash_val)
		if dataLen < hash_len:
			raise ValueError('Invalid dataLen: %d' % dataLen)
		hash_val = do_hash(data[hash_len:])
		if data[0:hash_len] != hash_val:
			raise ValueError('Invalid hash val: %s' % hash_val)
		en_len = hash_len
	outfile = KTemp_buffer()
	
	while en_len + 256 < dataLen:
		outfile.write(rsa.decrypt(data[en_len:en_len+256],prk))
		en_len += 256
	if en_len < dataLen:
		outfile.write(rsa.decrypt(data[en_len:],prk))
	return outfile.get()

def encrypt_data_common(data,dataLen,puk=default_pu,do_hash=None):
	if puk is None:
		return data
	outfile = KTemp_buffer()
	en_len = 0
	while en_len + 256 < dataLen:
		outfile.write(rsa.encrypt(data[en_len:en_len+256],puk))
		en_len += 256
	if en_len < dataLen:
		outfile.write(rsa.encrypt(data[en_len:],puk))
	en_data = outfile.get()
	if do_hash is not None and hasattr(do_hash, '__call__'):
		hash_val = do_hash(en_data)
		outfile.set_hash(hash_val)
		en_data = outfile.get()
	return en_data

def hash_encrypt_data_common(data,dataLen,puk=default_pu):
	return encrypt_data_common(data,dataLen,puk,_do_hash)
def hash_decrypt_data_common(data,dataLen,puk=default_pu):
	return decrypt_data_common(data,dataLen,puk,_do_hash)

def gen_ken_data(nbits):
	(pubkey,privkey) = rsa.newkeys(nbits)
	return (pubkey,privkey)

def get_default_k():
	return default_pu,default_pr

def get_pub_pk(pu):
	return pu.save_pkcs1()

def test_bigfile():
	infile = open('plain.jpg','rb')
	outfile = open('enrcrypt.bin','wb+')
	bigfile.encrypt_bigfile(infile, outfile, default_pu)
	infile.close()
	outfile.close()
	
	infile = open('enrcrypt.bin','rb')
	outfile = open('decrypt.jpg','wb+')
	bigfile.decrypt_bigfile(infile, outfile, default_pr)
	infile.close()
	outfile.close()

if __name__ == '__main__':
	(pubkey,privkey) = gen_ken_data(2048)
	save_pem_data('.',privkey)
	(pubkey,privkey) = gen_ken_data(2048)
	save_pem_data_common('.',privkey)
	pu,pr = load_pem_data('.')
	if pu == pubkey and pr == privkey:
		print ('match\n')
