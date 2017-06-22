# Some exceptions for some possible illegal states that may occur. 
# TODO: Add more of these
class NeedPasswordError(Exception):
	def __str__(self):
		return('Explicit users need passwords')

class PassNotNeededError(Exception):
	def __str__(self):
		return('Implicit users cannot have passwords')

class UserAlreadyExistsError(Exception):
	def __str__(self):
		return('User %s already exists' %self.user)
	def __init__(self, user):
		self.user = user

class UserNotFound(Exception):
	def __init__(self, user):
		self.user = user
	def __str__(self):
		return('Could not find user %s' %self.user)


# Same thing with this. 
class helpCmd: 
	def __init__(self, channel, cmd):
		self.channel = channel
		self.cmd = cmd

# Not much to do here, just passing in some useful functions
class periodic:
	def __init__(self, bot):
		self.bot = bot
		self.conninfo = bot.conn
		self.conn = bot.conn
		self.socket = bot.conn.socket
		self.sendata = bot.conn.send
		self.getlevel = bot.getlevel
		self.hasPriv = bot.hasPriv

# This is the class used for when an external function needs to
# be called. This stuff gets mostly pre-processed so the contructor
# doesn't do much. 
class cmdMsg:
	def __init__(self, bot, channel, nick, cmd, run, isPrivate):
		self.bot = bot
		self.channel = channel
		self.nick = nick
		# legacy
		self.getlevel = bot.getlevel
		self.botnick = bot.nick
		self.cmd = cmd
		self.syscmd = bot.syscmd
		self.run = run
		self.numlevel = bot.getlevel
		self.senddata = bot.conn.send
		self.showdbg = bot.showdbg
		self.getLevelStr = bot.getLevelStr
		self.levelToStr = bot.levelToStr
		self.showErr = bot.showErr
		self.hasPriv = bot.hasPriv
		self.isPrivate = isPrivate
		self.conn = bot.conn

# This is the big one. This is what gets passed to listeners. 
# Here, the constructor actually does stuff. 
# TODO: NICK events, and don't use the word 'type'
class lineEvent:
	def __init__(self, bot, line):
		self.line = line.rstrip()
		self.bot = bot
		self.conninfo = bot.conn
		self.conn = bot.conn
		self.senddata = bot.conn.send
		self.getlevel = bot.getlevel
		self.numlevel = bot.getlevel
		self.showdbg = bot.showdbg
		self.showErr = bot.showErr
		self.getLevelStr = bot.getLevelStr
		self.levelToStr = bot.levelToStr
		self.linesplit = self.line.split(' ')
		self.userString = ''
		self.etype = ''
		self.syscmd = bot.syscmd
		self.hasPriv = bot.hasPriv

		if self.linesplit[0] == 'PING':
			self.etype = 'ping'
			self.ping = self.line.split()
			self.target = self.ping[1]
			return
		
		if self.linesplit[0] == 'ERROR':
			self.etype = 'error'
			return
		
		if self.linesplit[1] == 'PART':
			self.etype = 'part' 
			self.userString = self.linesplit[0]
			self.channel = self.linesplit[2]
			if len(self.linesplit) >= 4:
				self.reason = self.linesplit[3][1:]

		if self.linesplit[1] == 'JOIN':
			self.etype = 'join'
			self.userString = self.linesplit[0]
			self.channel = self.linesplit[2]
			if len(self.linesplit) >= 4:
				self.reason = self.linesplit[3][1:]

		if self.linesplit[1] =='NICK':
			self.etype = 'nick'
			self.userString = self.linesplit[0]
			self.newNick = self.linesplit[2]
		
		if self.linesplit[1] =='QUIT':
			self.etype = 'quit'
			self.userString = self.linesplit[0]
			self.reason = self.linesplit[2][1:]

		if self.linesplit[1] == 'PRIVMSG':
			self.etype = 'privmsg'
			self.userString = self.linesplit[0]
			self.channel = self.linesplit[2]
			if self.channel[0] == '#':
				self.isPrivate = False
			else:
				self.isPrivate = True 
			
			if self.isPrivate:
				self.channel = self.userString.split(':')[1].split('!')[0]

			self.message = ' '.join(self.linesplit[3:])
			if (self.message[0] == ':'):
				self.message = self.message[1:]

		"""
		elif self.linesplit[1] in ('353'):
			self.
			"""


		if self.userString:
			part1 = self.userString.split(':')[1]
			part2 = part1.split('!')
			part3 = part2[1].split('@')
			self.nick = part2[0]
			self.user = part3[0]
			self.realName = part3[1]

		if not(self.etype):
			self.etype = self.linesplit[1]

# Given a nick, an explicit auth name, their level, and their permissions, 
# construct an aUser object for them. 
class aUser:
	def __init__(self, nick, authName, level, perms = []):
		self.nick = nick
		self.authName = authName
		self.level = level
		self.grant = set()
		self.deny = set()
		for i in perms:
			if i:
				if i[0] == '+':
					self.grant.add(i[1:])
				elif i[0] == '-':
					self.deny.add(i[1:])
				else:
					raise(Exception('Failed to process permission %s for user %s.' %(i, self.authName)))

		for i in self.grant:
			if i in self.deny:
				raise(Exception('User %s has been granted and denied permission %s' %(self.authName, i)))

	def rename(self, newNick):
		self.nick = newNick

	def chgLvl(self, newLevel):
		self.level = newLevel
	

# Implicit auth version of aUser. Doesn't take an authName
# since authName and nick will always be the same for implicit auth. 
class asUser:
	def __init__(self, nick, level, perms):
		self.nick = nick
		self.authName = nick
		self.level = level
		self.grant = set()
		self.deny = set()
		for i in perms:
			if i[0] == '+':
				self.grant.add(i[1:])
			elif i[0] == '-':
				self.deny.add(i[1:])
			else:
				raise(Exception('Failed to process permission %s for user %s.' %(i, self.authName)))

		for i in self.grant:
			if i in self.deny:
				raise(Exception('User %s has been granted and denied permission %s' %(self.authName, i)))

	def chgLvl(self, newLevel):
		self.level = newLevel	


# Entry in the auth list. Just used for simple lookups of auth data from the files. 
class uEntry:
	def __init__(self, authName, level, perms = []):
		self.authName = authName
		self.level = level
		self.grant = set()
		self.deny = set()
		for i in perms:
			if i:
				if i[0] == '+':
					self.grant.add(i[1:])
				elif i[0] == '-':
					self.deny.add(i[1:])
				else:
					raise(Exception('Failed to process permission %s for user %s.' %(i, self.authName)))

		for i in self.grant:
			if i in self.deny:
				raise(Exception('User %s has been granted and denied permission %s' %(self.authName, i)))

class BotStopEvent(Exception):
	def __init__(self, text, retval):
		super(BotStopEvent, self).__init__(text)
		self.retval = retval


class ChannelMapUser:
	__slot__ = ['nick']
	def __init__(self, name):
		self.nick = name

	def rename(self, newName):
		self.nick = newName

	def __str__(self):
		return self.nick


class ChannelMapEntry:
	__slots__ = ['chanName', 'userMap']
	def __init__(self, name):
		self.chanName = name
		self.userMap = {}

	def _addMemberEntry(self, entry):
		self.userMap[entry.nick] = entry

	def addMember(self, nick):
		self._addMemberEntry(ChannelMapUser(nick))

	def removeMember(self, nick):
		del self.userMap[nick]

	def removeMemberIfExists(self, nick):
		try:
			self.removeMember(self, nick)
		except:
			pass

	def renameMember(self, old, new):
		entry = self.userMap.pop(old)
		entry.rename(new)
		self._addMemberEntry(entry)

	def renameIfExists(self, old, new):
		try:
			self.renameMember(old, new)
		except KeyError:
			pass

	def refresh(self, nameList):
		oldSet = set(self.userMap.keys())
		newSet = set(nameList)
		toRemove = oldSet - newSet
		toAdd = newSet - oldSet
		map(this.removeMember, toRemove)
		map(this.addMember, toAdd)
