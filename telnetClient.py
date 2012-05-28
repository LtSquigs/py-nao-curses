import telnetlib 
from telnetlib import DO, DONT, WILL, WONT, theNULL, TTYPE, IAC, SB, SE, ECHO 


class TelnetClient():
	"""
	Handles connecting to nethack server, negotiating telnet options, and
	reading/writing to telnet connection. 
	"""	
	def __init__(self, server = "nethack.alt.org"):
		"""
		Initializes telnet client and sets the nethack server to connect to.
		"""
		self.nethackServer = server
		self.telnetSock = telnetlib.Telnet()
		self.telnetSock.set_option_negotiation_callback(self.negotiate)
		
	def setServer(self, serverName):
		"""
		Change nethack server to connect to.
		"""
		self.nethackServer = serverName
		
	def connect(self):
		"""
		Connect to nethack server.
		"""
		self.telnetSock.open(self.nethackServer)
		
	def fileno(self):
		return self.telnetSock.fileno()
		
	def write(self, buffer):
		"""
		Send buffer to nethack server.
		"""
		self.telnetSock.write(buffer)
		
	def read(self):
		"""
		Returns any data that can be read from the telnet connection without
		blocking.
		"""
		return self.telnetSock.read_very_eager()
		
	def negotiate(self, sock, command, option): 
		"""
		Handles negotiating telnet options, right now only replies to the server
		with what terminal it is. (xterm)
		"""
		negotiation_list=[ 
			['BINARY',WONT,'WONT'], 
			['ECHO',WONT,'WONT'], 
			['RCP',WONT,'WONT'], 
			['SGA',WONT,'WONT'], 
			['NAMS',WONT,'WONT'], 
			['STATUS',WONT,'WONT'], 
			['TM',WONT,'WONT'], 
			['RCTE',WONT,'WONT'], 
			['NAOL',WONT,'WONT'], 
			['NAOP',WONT,'WONT'], 
			['NAOCRD',WONT,'WONT'], 
			['NAOHTS',WONT,'WONT'], 
			['NAOHTD',WONT,'WONT'], 
			['NAOFFD',WONT,'WONT'], 
			['NAOVTS',WONT,'WONT'], 
			['NAOVTD',WONT,'WONT'], 
			['NAOLFD',WONT,'WONT'], 
			['XASCII',WONT,'WONT'], 
			['LOGOUT',WONT,'WONT'], 
			['BM',WONT,'WONT'], 
			['DET',WONT,'WONT'], 
			['SUPDUP',WONT,'WONT'], 
			['SUPDUPOUTPUT',WONT,'WONT'], 
			['SNDLOC',WONT,'WONT'], 
			['TTYPE',WILL,'WILL'], 
			['EOR',WONT,'WONT'], 
			['TUID',WONT,'WONT'], 
			['OUTMRK',WONT,'WONT'], 
			['TTYLOC',WONT,'WONT'], 
			['VT3270REGIME',WONT,'WONT'], 
			['X3PAD',WONT,'WONT'], 
			['NAWS',WONT,'WONT'], 
			['TSPEED',WONT,'WONT'], 
				['LFLOW',WONT,'WONT'], 
				['LINEMODE',WONT,'WONT'], 
			['XDISPLOC',WONT,'WONT'], 
			['OLD_ENVIRON',WONT,'WONT'], 
			['AUTHENTICATION',WONT,'WONT'], 
			['ENCRYPT',WONT,'WONT'], 
			['NEW_ENVIRON',WONT,'WONT'] 
		] 
		
		if ord(option)<40: 
			received_option=negotiation_list[ord(option)][0] 
			response=negotiation_list[ord(option)][1] 
			print_response=negotiation_list[ord(option)][2] 
		else: 
			received_option='unrecognised' 
			response=WONT 
			print_response='WONT' 
			
		if command==DO: 
			sock.sendall("%s%s%s" % (IAC, response, option))
		elif command==SE: 
			sock.sendall("%s%s%s%sxterm%s%s" %	(IAC,SB,TTYPE,chr(0),IAC,SE)) 
			
		return 

