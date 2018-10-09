#!/usr/bin/python
# -*- coding= utf-8 -*-
#file:  xml_to_dict.py

#from xml.dom import *
from  xml.dom.minidom import Document,parseString,Node
from json import load as json_load
from json import dumps as json_dumps
from os import linesep as oslinesep
#from debug_utils import *

def xml_node_to_dict(node):
	out = {}
	if node.nodeType!=Node.ELEMENT_NODE:
		return None
	for attrName,attrVal in node.attributes.items():
		out['@'+attrName] = attrVal
		#print ('AAAA',attrName,attrVal,type(attrVal))
	for item in node.childNodes:
		if item.nodeType==Node.TEXT_NODE or item.nodeType==Node.CDATA_SECTION_NODE:
			#print ('XXX',node.tagName,item.nodeValue,type(item.nodeValue))
			if node.childNodes.length==1:
				out[node.tagName] = item.nodeValue#.encode('utf-8')
			else:
				val = item.nodeValue.strip()
				if len(val)>0:
					out[node.tagName] = val#.encode('utf-8')
		elif item.nodeType==Node.ELEMENT_NODE:
			temp_data = xml_node_to_dict(item)
			
			if len(temp_data) == 1 and item.tagName in temp_data:
				temp_data = temp_data[item.tagName]
			if item.tagName in out:
				if type(out[item.tagName])==list:
					out[item.tagName].append(temp_data)
				else:
					out[item.tagName] = [out[item.tagName], temp_data]
			else:
				out[item.tagName] = temp_data
	return out

def dict_to_xml_node(dict_in):
	out = {}
	if node.nodeType!=Node.ELEMENT_NODE:
		return None
	for attrName,attrVal in node.attributes.items():
		out['@'+attrName] = attrVal
		#print ('EAAA',attrName,attrVal,type(attrVal))
	for item in node.childNodes:
		if item.nodeType==Node.TEXT_NODE or item.nodeType==Node.CDATA_SECTION_NODE:
			#print ('EXXX',node.tagName,item.nodeValue,type(item.nodeValue))
			if node.childNodes.length==1:
				out[node.tagName] = item.nodeValue.encode('utf-8')
			else:
				val = item.nodeValue.strip()
				if len(val)>0:
					out[node.tagName] = val.encode('utf-8')
		elif item.nodeType==Node.ELEMENT_NODE:
			temp_data = xml_node_to_dict(item)
			
			if len(temp_data) == 1 and item.tagName in temp_data:
				temp_data = temp_data[item.tagName]
			if item.tagName in out:
				if type(out[item.tagName])==list:
					out[item.tagName].append(temp_data)
				else:
					out[item.tagName] = [out[item.tagName], temp_data]
			else:
				out[item.tagName] = temp_data
	return out

def xml_to_dict(str_xml):
    try:
        dom = parseString(str_xml)
    except Exception as err:
        print (__file__,  str(err))
        return None
    #
    root = dom.documentElement
    out_dict = {root.tagName:xml_node_to_dict(root)}
    #print (out_dict)
    return out_dict

def xmlfile_to_dict(file_path):
    f = open(file_path, 'rb')
    str_xml = f.read()
    f.close()
    #
    return xml_to_dict(str_xml)

def dict_to_xml(dom,node,dict_in,encoding):
	for key,val in dict_in.items():
		key = str(key)
		if type(val) == type({}):
			subnode = dom.createElement(key)
			dict_to_xml(dom,subnode,val,encoding)
			node.appendChild(subnode)
		elif type(val) == type([]) or type(val) == type((0,)):
			for elem in val:
				subnode = dom.createElement(key)
				if isinstance(elem,dict):
					dict_to_xml(dom,subnode,elem,encoding)
				elif isinstance(elem,str):
					subnode.appendChild(dom.createTextNode(elem))
				elif type(elem) == type(u''):
					elem = elem.encode(encoding)
					subnode.appendChild(dom.createTextNode(elem))
				node.appendChild(subnode)
		elif type(val) == type('') or type(val) == type(u'') or type(val) == type(1) or type(val) == type(b''):
			if type(val) == type(1):
				val = str(val)
			elif type(val) == type(b''):
				val = val.decode(encoding)
			
			if key.startswith('@') or key.startswith(u'@'):
				key = key[1:]
				node.setAttribute(key, val)
			elif hasattr(node,'tagName') and key == node.tagName:
				node.appendChild(dom.createTextNode(val))
			else:
				subnode = dom.createElement(key)
				subnode.appendChild(dom.createTextNode(val))
				node.appendChild(subnode)
		else:
			print ('unknown type,skip',type(val),val)

def Indent(dom, node, indent = 0):
    # Copy child list because it will change soon
    children = node.childNodes[:]
    # Main node doesn't need to be indented
    if indent:
        text = dom.createTextNode(oslinesep + '\t' * indent)
        node.parentNode.insertBefore(text, node)
    if children:
        # Append newline after last child, except for text nodes
        if children[-1].nodeType == node.ELEMENT_NODE:
            text = dom.createTextNode(oslinesep + '\t' * indent)
            node.appendChild(text)
        # Indent children which are elements
        for n in children:
            if n.nodeType == node.ELEMENT_NODE:
                Indent(dom, n, indent + 1)

def root_dict_to_xml(dict_in,encoding=None,root_value=None):
	dom = Document()
	rootnode = dom
	if encoding is None:
		encoding = 'utf-8'
	if root_value is not None:
		rootnode = dom.createElement(root_value)
		dom.appendChild(rootnode)
	dict_to_xml(dom,rootnode,dict_in,encoding)
	
	#xml_string = dom.toprettyxml()
	#xml_string = dom.toxml(encoding=encoding)
	Indent(dom, dom.documentElement)
	
	return dom
	
def do_parse_xmlfile_to_json(file_path):
    f = open(file_path, 'rb')
    str_xml = f.read()
    f.close()
    #convert xml to dict
    data = xml_to_dict(str_xml)
    str_json = json_dumps(data, indent=2)
    f = open(file_path+'.js', 'wb')
    f.write(str_json.encode('utf-8'))
    f.close()

def do_parse_dict_to_xml(dict_in,file_name,encoding=None):
    from codecs import lookup as codecs_lookup
    if encoding is None:
        encoding = 'utf-8'
    dom = root_dict_to_xml(dict_in,encoding)
    #print 'complete',data
    f = open(file_name, 'wb')
    writer = codecs_lookup(encoding)[3](f)
    dom.writexml(writer, encoding = encoding)
    f.close()

def do_parse_json_file_to_xml(file_path,encoding=None):
    from codecs import lookup as codecs_lookup
    f = open(file_path, 'r')
    str_json = json_load(f)
    f.close()
    
    if encoding is None:
        encoding = 'utf-8'
    dom = root_dict_to_xml(str_json,encoding)
    #print 'complete',data
    f = open(file_path+'.xml', 'wb')
    writer = codecs_lookup(encoding)[3](f)
    dom.writexml(writer, encoding = encoding)
    f.close()

if __name__=='__main__':
    import sys
    argc = len(sys.argv)
    from os.path import splitext
    if argc<2:
        print ('usage:%s <file>' % sys.argv[0])
        sys.exit(-1)
    basename,extname = splitext(sys.argv[1])
    if extname == '.xml':
        do_parse_xmlfile_to_json(sys.argv[1])
    else:
        do_parse_json_file_to_xml(sys.argv[1])
    #
    print ('OK')

