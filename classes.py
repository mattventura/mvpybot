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


class LineParseError(Exception):
	pass


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
# BaseLineEvent should be treated as psuedo-abstract. It should
# never be instantiated directly, only subclasses.
class BaseLineEvent:

	def __new__(cls, bot, line):
		if cls is BaseLineEvent:
			raise Exception('BaseLineEvent should never be instantiated directly')
		else:
			return object.__new__(cls)

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
		self.syscmd = bot.syscmd
		self.hasPriv = bot.hasPriv


class PingEvent(BaseLineEvent):
	etype = 'ping'
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.ping = self.linesplit
		self.target = self.ping[1]

class ErrorEvent(BaseLineEvent):
	etype = 'error'

class UserEvent(BaseLineEvent):
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.userString = self.linesplit[0]
		self.nick, self.user, self.host = process_user_string(self.userString)


def process_user_string(userString):
		# TODO: replace this with a regex
		# Line begins with a : so strip it
		if userString[0] == ':':
			userString = userString[1:]
		# Separate 
		split1 = userString.split('!')
		split2 = split1[1].split('@')
		nick = split1[0]
		user = split2[0]
		host = split2[1]
		return nick, user, host


# These have exactly the same format except the event type itself
class JoinPartEvent(UserEvent):
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.userString = self.linesplit[0]
		self.channel = self.linesplit[2]
		if self.channel[:1] == ':':
			self.channel = self.channel[1:]
		if len(self.linesplit) >= 4:
			self.reason = self.linesplit[3][1:]

class JoinEvent(JoinPartEvent):
	etype = 'join'


class PartEvent(JoinPartEvent):
	etype = 'part'


class NickEvent(UserEvent):
	etype = 'nick'
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.newNick = self.linesplit[2]


class QuitEvent(UserEvent):
	etype = 'quit'
	def __init__(self, bot, line):
		super().__init__(bot, line)
		reason = self.linesplit[2]
		if reason[0] == ':':
			reason = reason[1:]
		self.reason = reason


class PrivmsgEvent(UserEvent):
	etype = 'privmsg'
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.channel = self.linesplit[2]
		self.isPrivate = (self.channel[0] != '#')
		if self.isPrivate:
			self.channel = self.nick

		self.message = ' '.join(self.linesplit[3:])
		if (self.message[0] == ':'):
			self.message = self.message[1:]


class UnknownEvent(BaseLineEvent):
	def __init__(self, bot, line):
		super().__init__(bot, line)
		self.etype = self.linesplit[1]


# Mapping for events where the event type is established in the
# first (#0) field of the event.
etypeMap0 = {'PING': PingEvent, 'ERROR': ErrorEvent}
# Mapping for events where the event type is established in the
# second (#1) field of the event.
etypeMap1 = {'PART': PartEvent, 'JOIN': JoinEvent,
	'NICK': NickEvent, 'QUIT': QuitEvent, 'PRIVMSG': PrivmsgEvent}

def lineEvent(bot, line):
	linesplit = line.split(' ')
	if len(linesplit) < 2:
		raise classes.LineParseError('Line had less than two fields')
	field0, field1 = linesplit[0:2]

	try:
		etypeCls = etypeMap0[field0]
	except KeyError:
		try:
			etypeCls = etypeMap1[field1]
		except KeyError:
			etypeCls = UnknownEvent

	return etypeCls(bot, line)


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
