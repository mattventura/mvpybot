#!/usr/bin/python3

global NICK

class ircSrv:
	
	global NICK
	
	def __init__(self, server, port = 6667, svrPass = False, csPass = False, chans = [], user = NICK, mode = 8, rn = NICK):
		self.host = server
		self.password = svrPass
		self.port = port
		self.csp = csPass
		self.chans = chans
		self.userString = 'USER ' + user + ' ' + str(mode) + ' * : ' + rn
		self.userAuth = True
		self.throttle = False


class twIrc:
	
	def __init__(self, chans, authkey):
		self.host = 'irc.twitch.tv'
		self.port = 6667
		self.csp = False
		self.chans = chans
		self.userString = 'USER ' + NICK + ' 8 * : ' + NICK
		self.userAuth = False
		self.password = authkey
		self.throttle = 2.5

class twIrcNt:
	
	def __init__(self, chans, authkey):
		self.host = 'irc.twitch.tv'
		self.port = 6667
		self.csp = False
		self.chans = chans
		self.userString = 'USER ' + NICK + ' 8 * : ' + NICK
		self.userAuth = False
		self.password = authkey
		self.throttle = 0.5
