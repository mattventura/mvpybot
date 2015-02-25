#!/usr/bin/python3

import time
import socket

class ircSrv:
	
	
	def __init__(self, nick, server, port = 6667, svrPass = False, csPass = False, chans = [], user = False, mode = 8, rn = False):
		self.nick = nick
		if not(user):
			user = nick
		if not(rn):
			rn = nick
		self.host = server
		self.password = svrPass
		self.port = port
		self.csp = csPass
		self.initChans = chans
		self.userString = 'USER ' + user + ' ' + str(mode) + ' * : ' + rn
		self.userAuth = True
		self.throttle = False
		self.isConnected = False
		self.lastMsgOut = 0
		self.fullyDone = False

	# Not used yet?
	logfunc = None
	def setLogger(self, logger):
		self.logfunc = logger


	def logData(self, data):
		if self.logfunc:
			self.logfunc(data)

	def showout(self, out, alt):
		if alt:
			out = alt
		outstr = '(%s)< %s' %(self.host, out.rstrip())

		self.logData(outstr)

	def showin(self, out):
		outstr = '(%s)> %s' %(self.host, out.rstrip())
		self.logData(outstr)


	def showdbg(self, out):
		outstr = '(%s)* %s' %(self.host, out.rstrip())
		self.logData(outstr)

	def _recvRaw(self):
		dataRaw = self.socket.recv(1024)
		data = dataRaw.decode()
		#print('Raw incoming: %s' %data)
		return data

	def recv(self):
		# This might throw socket.error (when there's no data), which we want to pass down anyway
		# so no need to catch it here
		data = False
		data = self._recvRaw()
		
		# Wait for a newline to be received, otherwise we get incomplete
		# lines sometimes
		# handle pings here too
		while data and data[-1] != '\n':
			data += self._recvRaw()
			
		if (data.find('PING') == 0):
			self.sendPing(data.split(' ')[1])
		
		if len(data) > 1:
			lines = data.split('\n')
			for line in lines:
				self.showin(line)
			

		return data


	def _sendToServerRaw(self, data):
		if self.isConnected:
			#print('Raw out: %s' %data)
			encdata = data.encode()
			self.socket.sendall(encdata)
		else:
			raise Exception('Tried to send data to server when not connected. ')

	def send(self, data, alt = False):
		sendparts = data.split('\n')

		if (len(sendparts) > 2):
			for part in sendparts[:-1]:
				self.send(part + '\n')

		else: 
			if self.throttle:
				timeSinceLast = time.time() - self.lastMsgOut
				if timeSinceLast < conn.throttle:
					time.sleep(conn.throttle - timeSinceLast)

			self._sendToServerRaw(sendparts[0] + '\n')
			lastMsgOut = time.time()

			
			for part in sendparts:
				if len(part) > 1:
					self.showout(part, alt)
	

	def initialize(self):
		self.connSocket()
		self.handShake()
		self.waitForHsFinish()
		self.joinChans()
		self.fullyDone = True

	def disconnect(self):
		pass

	def connSocket(self):
		host = self.host
		port = int(self.port)
		s = socket.socket()
		s.connect((host, port))
		self.socket = s
		self.s = s
		self.isConnected = True

	def sendPing(self, param):
		outStr = 'PONG %s' %param
		self.send(outStr)

	# Tell the server basic parameters after we connect
	def handShake(self):
		self.showdbg('Doing handshake...')
		# Send password
		if self.password:
			self.showdbg('Sending password...')
			self.send('PASS %s' %(self.password), 'PASS <censored>')

		# Nick
		self.showdbg('Setting nick...')
		self.send('NICK %s' %(self.nick))

		# Some servers do this as an anti-spoofer
		line = self._recvRaw()
		self.showin(line)
		time.sleep(1)
		self.s.settimeout(5)
		try:
			line = self._recvRaw()
			self.showin(line)
			if (line.find('PING') == 0):
				self.sendPing(line.split(' ')[1])
		except:
			pass

		self.send(self.userString)

		self.s.settimeout(5)

	def waitForHsFinish(self):
		line = ''
		while (line.find('001') < 1):
			line = self._recvRaw()

		self.showdbg('Connected')

	def csIdentify(self):
		csp = self.csp
		self.privmsg('nickserv', 'identify %s' %csp)
		self.showdbg('Identified with nickserv')

	
	def joinChans(self):
		self.chans = []
		for chan in self.initChans:
			self.joinChannel(chan)

		self.showdbg('Joined channels')
		
	def joinChannel(self, channel):
		self.send('JOIN %s' %channel)
		# Need to clean up, this doesn't check to see if joining was
		# actually successful
		self.chans.append(channel)






# Other server classes

class twIrc(ircSrv):
	
	def __init__(self, chans, authkey):
		self.host = 'irc.twitch.tv'
		self.port = 6667
		self.csp = False
		self.chans = chans
		self.userString = 'USER ' + NICK + ' 8 * : ' + NICK
		self.userAuth = False
		self.password = authkey
		self.throttle = 2.5
		self.isConnected = False

class twIrcNt(twIrc):
	
	def __init__(self, chans, authkey):
		self.host = 'irc.twitch.tv'
		self.port = 6667
		self.csp = False
		self.chans = chans
		self.userString = 'USER ' + NICK + ' 8 * : ' + NICK
		self.userAuth = False
		self.password = authkey
		self.throttle = 0.5
		self.isConnected = False
