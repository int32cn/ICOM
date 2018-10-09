

def init():
	print ('do init')
	
def parse(in_data):
	if in_data is None:
		print ('in data None')
		return None
	else:
		print ("in data:%s"%in_data)
	return "GET:%s"%in_data if in_data else ""