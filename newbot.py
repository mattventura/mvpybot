#!/usr/bin/python3

#	MVpybot, a Python IRC bot.
#	Copyright (C) 2009-2014 Matt Ventura
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.



# Not sure if this note is still relevant since I'm not the one who noticed it:
#	A note:
#	   Please do not try to run the bot in IDLE. Your system will slow down.
#	   The bot will run much better just from the commandline version of Python.
#	--Darren VanBuren

# Required builtin python modules
import sys
import socket
import string
import os
import time
import random
import inspect
import builtins
import traceback
from imp import reload
import re

# To be fixed later
import classes
from classes import *

import builtinfuncs

def reload_all():
	reload(builtinfuncs)
	reload(classes)

#Because sha is depreciated, we use the import ____ as ____ trickery
#   as well as try...except magic.
try:
	from hashlib import sha1 as sha
except ImportError:
	from sha import sha as sha

from subprocess import Popen, PIPE


# Import user settings
# Options is the one the user should change most of the time
# Config is just some strings and stuff
import options
import config

# Allow easy importing from the modules folder
sys.path.append("modules")


class Bot(object):


	def BotMain(self, botConn):
		try:
			self.BotInit()
			self.RunMainLoop()
		except BotStopEvent as e:
			return e.retval

		except:
			raise

	def __init__(self, botConn):
		self.conn = botConn

	def BotInit(self):
		# Announce that we are logging
		self.logdata(time.strftime('---- [ Session starting at %y-%m-%d %H:%M:%S ] ----'))

		self.showdbg('Initializing...')
		self.showdbg('Loading modules...')
		
		# Initialize authlist
		self.authlist = []
		self.chanMap = {}

		# This is where we load plugins
		# The general plugin system is this:

		# Functions are things called when a user tries to run a command, 
		# but no built-in function is found for it. These register a function
		# with the name that the user would type for the command. 
		# These are passed a cmdMsg object. 

		# Helps are like commands, but are called when you use the help command,
		# and no built-in help is available. These are passed a helpCMd object. 

		# Listeners handle certain events (or lack thereof). Listeners need to register
		# for the type of event they want (like 'join', 'privmsg', or 'part'. They are
		# passed a lineEvent object. You can also register for 'any' to listen
		# on any event, or 'periodic' for when the bot receives no data from the server
		# in a certain period of time. 

		# See some of the included modules for examples. o

		# Modules can declare a variable of 'enabled'. Set this to False to disable it. 
		# If it is omitted, True is assumed. 

		# These variables:
		# funcregistry is a dictionary of functions, by command name. 
		# listenerregistry is a dictionary containing a list for each event type
		# helpregistry is like funcregistry
		# Each entry in these is a [modules, function] pair
		# library_list then contains a list of all modules imported
		# libracy_dict is a dictionary of { name : module } pairst

		self.funcregistry = {}
		self.listenerregistry = {}
		self.helpregistry = {}
		self.library_list = []
		self.library_dict = {}

		for file in os.listdir(os.path.abspath("modules")):
			pname, fileext = os.path.splitext(file)
			if fileext == '.py':
				try:
					module = __import__(pname)
				except:
					self.showErr('Error importing plugin ' + pname)
					self.reportErr(sys.exc_info())

				self.library_list.append(module)
				self.library_dict[pname] = module
				if hasattr(module, 'register') and getattr(module, 'enabled', 1):
					regs = self
					builtins.lastMod = module
					try:
						getattr(module, 'register')(regs)
					except:
						self.showErr('Error registering plugin ' + pname)
						self.reportErr(sys.exc_info())
		
		# Load the simple auth file if using implicit/simple auth
		# This file needs to be formatted as such:
		# username1 user
		# username2 admin
		# It must be a space in-between, and you must use the friendly-name
		# user levels, rather than numbers. 
		
		if not(self.conn.userAuth):
			try:
				with open('ausers') as f:
					auLines = f.readlines()
					for line in auLines:
						line = line.rstrip()
						lineParts = line.split(' ')
						self.authlist.append(asUser(lineParts[0], int(lineParts[1]), lineParts[2:]))
			except IOError:
				self.ErrorAndStop('Error loading implicit auth list.', 255)
			except: 
				self.ErrorAndStop('Unknown error while loading implicit auth list.', 255)

		conn = self.conn
		# Legacy stuff
		self.host = self.conn.host
		self.port = self.conn.port

		# More legacy stuff
		builtins.host = conn.host

		# Expose our logger function to the connection object
		# so that it can properly log/output data. 
		self.conn.setLogger(self.logdata)

		# Legacy variable names
		self.cspass = self.conn.csp

		# Initialize these to almost-blank strings to avoid some problems
		self.line = ' '
		self.tosend = ' '

		# If the connection is already connected (in the case of a reload), 
		# do nothing. Otherwise, connect and initialize. 
		if self.conn.fullyDone:
			pass
		else:
			self.conn.initialize()

		for channel in self.conn.initChans:
			self.JoinChannel(channel)
			
		# For if we reload, this tries to reload the old auth list
		def loadauthlist():
			return builtins.authlist

		# We only do this if we're using explicit authentication
		if self.conn.userAuth:
			try:
				self.authlist = loadauthlist()
			except:
				# If there's no auth list to load, load a blank one
				self.authlist = []

		self.conn.s.settimeout(5) # This sets the max time to wait for data
		self.nick = options.NICK

	def RunMainLoop(self):
		while True:
			retval = self.MainLoop()
			if retval is not None:
				return retval

	def MainLoop(self):

		# main loop
		# Note that this will also affect how often periodics are run

		linebuffer = None
		try:
			linebuffer = self.conn.recv()
			if not(linebuffer):
				# Check if there was a socket error. If there was, tell the wrapper that. 
				# TODO: make the bot handle reconnects internally
				self.logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: lost connection)'))
				self.ErrorAndStop('Lost connection', 255)
	
		# No new data
		except socket.error:
			pass

		except KeyboardInterrupt:
			self.ErrorAndStop('Keyboard Interrupt', 0)
		except:
			pass

		# If we got no data from the server, run periodics
		if not(linebuffer):
			self.runPeriodics()

		# What to do if we did get data
		else:
			# If the server dumped a bunch of lines at once, split them
			# TODO: check if we actually still need this
			# TODO: implement some type of queue in the server object
			# so that it doesn't need to be done here. 
			lines = linebuffer.splitlines()
			for line in lines:
				try:
					# Turn our line into a lineEvent object
					e = lineEvent(self, line)
				except:
					self.showdbg('Failed basic line parsing! Line: ' + line)
					self.reportErr(sys.exc_info())
					continue
					
				# If the data we received was a PRIVMSG, do the usual privmsg parsing
				if e.etype == 'privmsg':
					
					# Parse returns a dictionary containing some stuff, including an action to take if applicable
					lstat = self.parse(e)
					
					try:
						
						# If parse()'s return contains an action, carry out that action
						if 'action' in lstat:

							if lstat['action'] == "restart":
								self.logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: restart requested)'))
								raise BotStopEvent('Restart requested', 1)

							if lstat['action'] == "die":
								self.logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: stop requested)'))
								raise BotStopEvent('Die requested', 0)

							if lstat['action'] == "reload":
								if self.conn.userAuth:
									builtins.authlist = self.authlist
								self.logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: reload requested)'))
								raise BotStopEvent('Reload requested', 2)

					# If there was any error, do our usual error reporting. 
					except BotStopEvent as e:
						raise
					except:
						self.reportErr(sys.exc_info())
	
				# Fail gracefuly if the server gives us an error. 
				if e.etype == 'error':
					self.logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: received error from server)'))
					self.ErrorAndStop('Received error from server', 255)

				# If a user leaves the server, remove them from the auth list
				elif (e.etype == 'quit'):
					for i in self.authlist:
						if i.nick == e.nick:
							self.showdbg('Removing nick %s from authlist due to quit' %(e.nick))
							self.authlist.remove(i)

				# If a user changes their nick, update the auth list accordingly
				elif (e.etype == 'nick'):
					for i in self.authlist:
						if i.nick == e.nick:
							self.showdbg('Upddating nick %s in authlist to %s' %(e.nick, e.newNick))
							i.nick = e.newNick
					self.processNick(e)

				elif (e.etype == 'join'):
					self.processJoin(e)

				elif (e.etype == 'part'):
					self.processPart(e)

				self.runListeners(e)

	def runListeners(self, e):
		# Run listeners of the apporpriate type
		if e.etype:
			if e.etype in self.listenerregistry:
				for function in self.listenerregistry[e.etype]:
					l = function[0]
					target = function[1]
					
					try:
						target(e)
					except:
						self.reportErr(sys.exc_info())

			# Also run listeners who hook onto 'any'
			if 'any' in self.listenerregistry:
				for function in self.listenerregistry['any']:
					l = function[0]
					target = function[1]

					try:
						target(e)
					except:
						self.reportErr(sys.exc_info())

	modFunc = builtinfuncs.modFunc
	userMgmtFunc = builtinfuncs.userMgmtFunc

	# This big function is called when we want to parse an incoming PRIVMSG
	# e: the event, which we've already created
	def parse(self, e):
		# Legacy
		sender = e.nick
		channel = e.channel
		msg = e.message
		conn = e.conn

		# Figure out if it is a channel message or a private message
		isprivate = e.isPrivate
		if isprivate:
			channel = sender

		run = ''
		out = ''
		length = len(msg)

		# Quick fix
		if not(length):
			msg = '(null)'

		# There are three ways to call a command:
		# #1: Use the command prefix, set in options
		if (msg[0] == options.cmdprefix):
			cmd = msg[1:].split(' ')
			run = cmd[0]
			cmdstring = ' '.join(cmd)

		msgparts = msg.split(' ')

		# #2: Say the bot's name, followed by a colon and space
		if ((msgparts[0].lower() == options.NICK.lower() + ':') and msgparts):
			cmd = msgparts[1:]
			run = cmd[0].rstrip()
			cmdstring = ' '.join(cmd)

		# #3: Directly send the bot a PM
		if isprivate:
			cmd = msgparts[0:]
			run = cmd[0].rstrip()
			cmdstring = ' '.join(cmd)

		# Do this stuff if it is determined that we should try
		# to run a command
		if (run):

			# We construct this object to pass to functions that correspond to actual chat functions
			msgObj = cmdMsg(self, channel, sender, cmd, run, isprivate)

			# Builtin functions
			# Some of these can be externalized, others cannot since some of the auth system stuff
			# never gets exposed to them. 
			funcs = {'test' : self.testFunc, 
				'userinfo' : self.userinfoFunc, 'auth' : self.authFunc, 'auths' : self.authFunc, 'authenticate' : self.authFunc, 
				'level' : self.levelFunc, 'deauth' : self.deauthFunc, 'register' : self.registerUserFunc, 
				'pass' : self.passFunc, 'passwd' : self.passwdFunc, 'authdump' : self.authDump, 'errtest' : self.errTest,
				'modules' : self.modFunc, 'help' : self.helpFunc, 'err' : self.errFunc, 'errors' : self.errFunc,
				'reloadopts' : self.reloadOpts, 'reloadcfg' : self.reloadConfig, 'perm' : self.userMgmtFunc, 'user' : self.userMgmtFunc
			}

			try: 
				# If the command is in our built-ins, run it
				if run in funcs:
					out = funcs[run](msgObj)

				# Commands for stopping/starting/reloading/etc: This is important so read this.
				# It's not incredibly intuitive. 
				# reload: the wrapper one level above this bot (mvpybot.py) just does a reload()
				# on the bot module, then restarts it. Saves authenticated users first. Does not
				# use a new connection. 
				# restart: restarts the bot. Saves auth list. Doesn't actually reload the bot
				# so I'm not sure when you would actually want to use this. Uses same connection. 
				# die: both the bot and the wrapper one level above it stop. If you ran mvpybot.py
				# directly, it will stop. If you're running start.py, it will automatically be
				# restarted. 
				# Yes, this means that unlike most programs, 'reload' actually does more than 'restart'. 

				# These reside here because it would get messy to put them elsewhere. 
				if (run == 'restart'):
					if (self.getlevel(sender) >= self.getPrivReq('power', 20)):
						self.showdbg('Restart requested')
						self.conn.privmsg(channel,  'Restarting...')
						return {'action': "restart"}
					else:
						out = config.privrejectadmin

				elif (run == 'die'):
					if (self.getlevel(sender) >= self.getPrivReq('power', 20)):
						self.showdbg('Stop requested')
						self.conn.privmsg(channel,  'Stopping...')
						return {'action': "die"}
					else:
						out = config.privrejectadmin

				elif (run == 'reload'):
					if (self.getlevel(sender) >= self.getPrivReq('power', 20)):
						self.showdbg('Reload requested')
						self.conn.privmsg(channel,  'Reloading...')
						return {'action': "reload"}
					else:
						out = config.privrejectadmin

			
			# Report errors that occur when running a built-in function
			except:
				self.reportErr(sys.exc_info())
				out = config.intErrorMsg
			
			# Functions can return True if they wish to indicate that they were successful
			# but do not want to actually send anything to the server, or they have sent
			# things to the server through conn.* methods. 
			nodata = False
			try:
				if out == True:
					nodata = True
			except:
				pass
			if nodata:
				return {}
			
			
			if (out):
				# out might either be a formatted PRIVMSG or just some text
				# that should be sent to the correct place
				# Actually, it should never be formatted anymore. 
				if (out[0:7] != 'PRIVMSG'):
					conn.privmsg(channel, out)
				else:
					conn.send(out + '\n')

			# Try to run a module function, since we'll only get to this point
			# if it wasn't handled by an appropriate builtin. 
			else:
				# Check if the name we want exists in funcregistry
				if run in self.funcregistry:
					target = self.funcregistry[run]
					l = target[0]
					# Pass all this stuff in via our msgObj object
					try:
						out = target[1](msgObj)
						if out is None:
							self.showErr('Command returned None. This is most likely a bug in that command.')
							return {}
						# Something can return True to silenty proceed
						if out is True:
							return {}
						if (out.split(' ')[0] != 'PRIVMSG'):
							out = 'PRIVMSG %s :%s\n' %(channel, out)
					except:
						# If an error occurs, record it and tell the user something happened. 
						self.reportErr(sys.exc_info())
						out = 'PRIVMSG %s :%s' % (channel, config.modErrorMsg)
						
				else: 
					found = 0

				# Send out data to the server, assuming there's something to send. 
				try:
					if (out):
						if (out[-1] != '\n'):
							out += '\n'
						self.conn.send(out)

					# If the command was not found, tell the user that.
					# Note that this has to be enabled in config, since
					# it can end up doing annoying/undesired things sometimes. 
					elif config.cnf_enable:
						out = 'PRIVMSG ' + channel + ' :Command not found'
						conn.send(out + '\n')

				# Report any error that may have happened when processing the data. 
				except:
					self.reportErr(sys.exc_info())

		# This function only returns stuff if we need to signal the main loop to exit. 
		return {}

	# Class definitions



	# This is a function that can be used to call external programs
	# Be sure that the program does not hang, or else the bot will hang
	# To make it un-hangable, look at the math plugin for an example
	# of how to modify it.
	# And of course, MAKE SURE MODULES THAT USE THIS ARE VERY SECURE!
	# If you aren't planning on using any modules that make use of this, 
	# you may want to just commend this out. 
	def syscmd(self, command):
		self.showdbg('SYSCMD called. Running "' + ' '.join(command) + '".')
		result = Popen(command, stdout = PIPE).communicate()[0]
		return result

	# Tries to guess whether 'a' or 'an' should be used with a word
	@staticmethod
	def getArticle(word):
		if word.lower() == 'user':
			return('a')
		elif word[0] in ('a', 'e', 'i', 'o', 'u'):
			return('an')
		else:
			return('a')

	# Tries to find a privilege level in config.py
	# Failing that, it will return the default argument. 
	# This can be used to allow addons to specify a default privilege
	# level while still allowing it to be overridden in config.py. 
	def getPrivReq(self, priv, default = 0):
		if priv in config.reqprivlevels:
			return config.reqprivlevels[priv]
		else:
			return default

	# Check if someone has a privilege
	def hasPriv(self, nick, priv, default = 3):
		# Try to find the user's current auth info
		try:
			auth = self.getAuth(nick)
		except UserNotFound:
			# If not found, just assume that the user has a level of 0
			# and return True if the privilege requested is less than
			# or equal to that. 
			return(0 >= self.getPrivReq(priv, default))
		# If the user has specifically been denied the privilege in question, 
		# return False
		if priv in auth.deny:
			return False
		# Otherwise, if they have specifically been granted it, return True. 
		elif priv in auth.grant:
			return True
		# If the user's level is above the level required to implicitly grant the
		# privilege, return True
		elif self.getlevel(nick) >= self.getPrivReq(priv, default):
			return True
		# Otherwise, return False
		else:
			return False


	# Builtin command functions

	# Test function
	def testFunc(self, msg):
		return('%s: test' %msg.nick)

	# Lookup user info for a particular username
	# Requires acctInfo priv, defaults to 0.  
	def userinfoFunc(self, msg):

		if (len(msg.cmd) != 2):
			return('Incorrect usage. Syntax: user <username>')

		elif not(hasPriv(msg.nick, 'acctInfo', 0)):
			return(config.privrejectgeneric)

		else:
			username = msg.cmd[1]
			try:
				authEntry = userLookup(username)
			except UserNotFound:
				return('That user is not in the user list')

			fUser = authEntry.authName
			fLevel = authEntry.level
			fLevelStr = levelToStr(fLevel)
			article = getArticle(fLevelStr)
			return('%s is level %s (%s %s).' %(fUser, str(fLevel), article, fLevelStr))
						
					
	# Look up a user's info from files only. 
	def userLookup(self, authName):

			if conn.userAuth:
				authFile = 'users'
			else:
				authFile = 'ausers'

			with open(authFile,  'r') as f:

				for fline in f.readlines():

					fline = fline.rstrip()
					lineParts = fline.split(' ')
					

					if lineParts[0] == authName:

						fUser = lineParts[0]
						# fPass = lineParts[1]
						if conn.userAuth:
							fLevel = int(lineParts[2])
							fPerms = lineParts[3:]
						else:
							fLevel = int(lineParts[1])
							fPerms = lineParts[2:]

						return(uEntry(fUser, fLevel, fPerms))

			raise(UserNotFound(authName))	

					

	# Format a permissions string
	# Format is (+|-)<perm><spacer>
	# For example, +acctInfo -acctMgmt
	# This is used both to format it for the auth files (spacer = ' ')
	# and for user-friendly output for account management commands (spacer = ', ')
	def formatPerms(self, grant, deny, spacer = ' '):
		outStr = ''
		for i in grant:
			outStr += '+%s%s' %(i, spacer)
		for i in deny:
			outStr += '-%s%s' %(i, spacer)
		# Fenceposting, fix, remove the data at the end of the string
		# equal to the length of the spacer. 
		outStr = outStr[:(-1*len(spacer))]
		return(outStr)



	# Authenticate a user
	def authFunc(self, msg):

		# If using implicit auth, there is no auth command. 
		if not(self.conn.userAuth):
			return(config.simpleAuthNotice)

		# Syntax error
		elif len(msg.cmd) != 3:
			return('Incorrect syntax. Usage: auth <username> <pass>')

		# If someone tries to use this command out in the open. 
		elif not(msg.isPrivate):
			return('''Use this in a /msg, don't use it in a channel. Now go change your passsword.''')
		
		# If someone is already authenticated, remind them. 
		elif self.getlevel(msg.nick) != 0:
			return('You are already authenticated. If you would like to change accounts, you can deauth and try again.')

		# If none of the above apply, it's time to check their credentials. 
		else:
			iName = msg.cmd[1].rstrip()
			iPass = msg.cmd[2].rstrip()

			with open('users', 'r') as f:
				# found means we found the username in the auth file. 
				# correct means the password actually matched. 
				correct = False
				found = False
				self.showdbg('%s is attempting to authenticate.' % iName)

				for fLine in f.readlines():
					fLine = fLine.rstrip()
					lineParts = fLine.split(' ')

					# If name matches, check this entry and mark found as True.
					if lineParts[0] == iName:
						found = True
						fPass = lineParts[1]
						fLevel = int(lineParts[2])
						perms = lineParts[3:]
						# The password in the file might be plaintext (e.g. if it was manually
						# edited into the file by an administrator) or it may be hashed (every other
						# scenario). 
						if iPass == fPass:
							correct = True
						elif ('HASH:' + sha(iPass.encode()).hexdigest()) == fPass:
							correct = True
							
			# Correct username
			if found:
				# Correct username + password
				if correct:
					# If they have explicit permissions specified in the file, add those
					# into our aUser object. 
					if perms:
						self.authlist.append(aUser(msg.nick, iName, fLevel, perms))
					else:
						self.authlist.append(aUser(msg.nick, iName, fLevel))
						

					self.showdbg('%s is authenticated' %iName)

					# 'auths' is the command to silently succeed, i.e. we don't report
					# the success back to the user. 
					if msg.run == 'auths':
						return(True)

					# Otherwise, tell them they were successful
					else:
						return('Password accepted, you are now authenticated')

				# Correct username, but wrong password
				else:
					self.showdbg('%s tried to authenticate, but their password was rejected' %iName)
					return('Incorrect password')

			# Wrong username
			else:
				self.showdbg('%s tried to authenticate, but their username was not found' %iName)
				return('Incorrect username')
						
	# Function to check the user level of yourself or someone else
	# Requires acctInfo priv
	def levelFunc(self, msg):
		
		if not(hasPriv(msg.nick, 'acctInfo', 3)):
			return(config.privrejectgeneric)

		# Checking oneself
		if len(msg.cmd) == 1:
			lNick = msg.nick

		# Checking someone else
		else:
			lNick = msg.cmd[1]

		try:
			lAuth = getAuth(lNick)
		except UserNotFound:
			return('User not found.')
		strLevel = levelToStr(lAuth.level)


		# Always print level info
		outStr = '%s is level %s (%s %s). ' %(lNick, str(lAuth.level), getArticle(strLevel), strLevel)

		# Additionally, print granted and/or denied permissions if they exist. 
		if lAuth.grant:
			outStr += 'Granted permissions: '
			for i in lAuth.grant:
				outStr += i + ', '
			outStr = outStr[:-2] + '. '

		if lAuth.deny:
			outStr += 'Denied permissions: '
			for i in lAuth.deny:
				outStr += i + ', '
			outStr = outStr[:-2] + '. '

		return(outStr)

	# Log out
	def deauthFunc(self, msg):
		
		if not(self.conn.userAuth):
			return(config.simpleAuthNotice)

		else:
			found = False
			iName = msg.nick
			if self.getlevel(iName) != 0:
				for i in self.authlist:
					
					alName = i.nick
					if alName == iName:
						self.authlist.remove(i)
						found = True

				if found:
					return('Deauthenticated')

				else:
					return('An error has occured')

			else:
				return('You are not authenticated')

	# Register a new user
	def registerUserFunc(self, msg):
		
		if not(conn.userAuth):
			return(config.simpleAuthNotice)

		else:
			
			if (len(msg.cmd) != 3):
				return('Incorrect syntax. Usage: register <username> <password>')

			else:
				try:
					addUser(msg.cmd[1], msg.cmd[2])
				except UserAlreadyExistsError:
					return('Sorry, that username is already taken')
				return('Account created. You can now authenticate.')


	# Command to actually add a new user. 
	# Used by both the register function and the account management function (user aka perm)
	# to actually expose this functionality to users/admins. 
	def addUser(self, name, password = None, level = config.newUserLevel, grant = set(), deny = set()):
		
		if conn.userAuth:
			if password == None:
				raise(NeedPasswordError())
			authFile = 'users'
		else:
			if password != None:
				raise(PassNotNeededError())
			authFile = 'ausers'


		with open(authFile, 'r') as f:
			valid = True
			for fLine in f:
				fLineSplit = fLine.split(' ')
				if name == fLineSplit[0]:
					valid = False
					raise(UserAlreadyExistsError(name))

		if valid:
			with open(authFile, 'a') as f:
				if conn.userAuth:
					fileOut = '%s HASH:%s %s %s\n' %(name, sha(password.encode()).hexdigest(), str(config.newUserLevel), formatPerms(grant, deny))
				else:
					fileOut = '%s %s %s\n' %(name, str(config.newUserLevel), formatPerms(grant, deny))
				f.write(fileOut)



	# Function to change a user's password
	# Exposed to user through pass and passwd commands. 
	def chgUserPass(self, user, newPass):
		if not(conn.userAuth):
			raise(Exception('Simple auth is enabled, so there are no passwords to change'))

		else:
			self.showdbg('Attempting to change password for %s' %user)

			if conn.userAuth:
				authFile = 'users'
			else:
				authFile = 'ausers'

			with open(authFile, 'r') as f:
				outData = ''
				found = False
				
				for fLine in f:
					
					lineSplit = fLine.split(' ')
					if user == lineSplit[0]:
						outData += '%s HASH:%s %s' %(lineSplit[0], sha(newPass.encode()).hexdigest(), ' '.join(lineSplit[2:]))
						self.showdbg('Found entry, modifying...')
						found = True

					else:
						outData += fLine

			if found:
				with open(authFile, 'w') as f:
					f.write(outData)
					f.truncate()
				
				self.showdbg('Changed password for %s' %user)
				return

			else:
				
				self.showdbg('Could not find user %s' %user)
				raise(UserNotFound(user))
					
	# Function to change a user's level
	def chgUserLvl(self, user, newLevel):
		
		self.showdbg('Attempting to change level for %s' %user)

		if conn.userAuth:
			authFile = 'users'
		else:
			authFile = 'ausers'

		with open(authFile, 'r') as f:
			outData = ''
			found = False
			
			for fLine in f:
				
				lineSplit = fLine.split(' ')
				
				if user == lineSplit[0]:
					if conn.userAuth:
						outData += '%s %s %s' %(' '.join(lineSplit[0:2]), str(newLevel), ' '.join(lineSplit[3:]))
					else:
						outData += '%s %s %s' %(lineSplit[0], str(newLevel), ' '.join(lineSplit[2:]))
					self.showdbg('Found entry, modifying...')
					found = True

				else:
					outData += fLine

		if found:
			with open(authFile, 'w') as f:
				f.write(outData)
				f.truncate()
			
			self.showdbg('Changed level for %s' %user)
			return

		else:
			
			self.showdbg('Could not find user %s' %user)
			raise(UserNotFound(user))
				
			
	# Function to change a user's privileges
	# This function requires ALL of the privileges you want the user to have after the change. 
	def chgUserPrivs(self, user, grant, deny):
		
		self.showdbg('Attempting to change privs for %s' %user)
		if conn.userAuth:
			authFile = 'users'
		else:
			authFile = 'ausers'


		with open(authFile, 'r') as f:
			outData = ''
			found = False
			
			for fLine in f:
				lineSplit = fLine.split(' ')
				
				if user == lineSplit[0]:
					newPrivs = formatPerms(grant, deny)
					if conn.userAuth:
						outData += '%s %s\n' %(' '.join(lineSplit[0:3]), newPrivs)
					else:
						outData += '%s %s\n' %(' '.join(lineSplit[0:2]), newPrivs)
					self.showdbg('Found entry, modifying...')
					found = True

				else:
					outData += fLine

		if found:
			with open(authFile, 'w') as f:
				f.write(outData)
				f.truncate()
			
			self.showdbg('Changed privs for %s' %user)
			return

		else:
			self.showdbg('Could not find user %s' %user)
			raise(UserNotFound(user))

	# Function to change your own pass
	def passFunc(self, msg):
		
		if not(conn.userAuth):
			return(config.simpleAuthNotice)

		else:

			if (len(msg.cmd) != 2):
				return('Incorrect syntax. Usage: pass <password>')

			else:
				authEntry = getAuth(msg.nick)
				if authEntry:
					authName = authEntry.authName

					result = chgUserPass(authName, msg.cmd[1])

					if result:
						return('Successfully changed password')

					else:
						return('An error has occurred')

				else:
					
					return('You must be authtenticated to use this command')
							

	# Function to change someone else's password. 
	def passwdFunc(self, msg):
		
		if not(conn.userAuth):
			return(config.simpleAuthNotice)

		elif (len(msg.cmd) != 3):
			return('Incorrect syntax. Usage: passwd <username> <password>')

		elif not(hasPriv(msg.nick, 'acctMgmt', 20)):
			return(config.privrejectadmin)

		else:
			result = chgUserPass(msg.cmd[1], msg.cmd[2])

			if result:
				return('Successfully changed password for %s' %msg.cmd[1])

			else:
				return('Could not find user %s in the users file' %msg.cmd[1])

	# Dump authenticated users to the console/log. 
	def authDump(self, msg):
		
		if not(conn.userAuth):
			return(config.simpleAuthNotice)

		elif not(hasPriv(msg.nick, 'acctMgmt', 20)):
			return(config.privrejectadmin)

		else:
			self.showdbg('Dumping auth list. Format is nick, authname, level')
			for i in self.authlist:
				self.showdbg('%s, %s, %s, %s, %s' %(i.nick, i.authName, str(i.level), str(i.grant), str(i.deny)))
				return('Dumped auth list to console')

	# Generate an error. 
	def errTest(self, msg):

		if hasPriv(msg.nick, 'errors', 20):
			self.showdbg('Error test requested')
			msg.conn.send('PRIVMSG %s :Error requested. Check the console.\n' %msg.channel)
			time.sleep(1)
			raise(Exception('User-requested error'))
		else:
			return(config.privrejectadmin)

	# The help system
	def helpFunc(self, msg):
		
		if len(msg.cmd) == 1:
			return('PRIVMSG %s :%s Use help <command> for help on a particular command. To use a command either say %s: <command> or %scommand.\n' %(msg.channel, config.defaulthelp, self.nick, options.cmdprefix))
		else:
			msg.cmd[1] = msg.cmd[1].rstrip()
			handled = False

			if msg.cmd[1] in self.helpregistry:
				item = self.helpregistry[msg.cmd[1]]
				l = item[0]
				
				handled = True
				target = item[1]
				
				out = target(classes.helpCmd(msg.channel, msg.cmd[1:]))
				if out.find('PRIVMSG') == -1:
					out = 'PRIVMSG %s :%s' %(msg.channel, out)

				return(out)

				return('Either that command does not exist, or help has not been written for it. ')

	# The error system
	def errFunc(self, msg):
		if self.getlevel(msg.nick) < self.getPrivReq('errors', 20):
			return config.privrejectadmin

		elif len(msg.cmd) == 1:
			return('There are currently %s stored errors' %int(len(builtins.errors)))

		elif msg.cmd[1] == 'last':
			if len(builtins.errors) > 0:
				errString = fmtErr(builtins.errors[-1])
				errLines = errString.splitlines()
				for el in errLines:
					if config.privacy:
						el = re.sub('/home/.*?/', '/home/***/', el)
					
					msg.conn.send('PRIVMSG %s :%s\n' %(msg.channel, el))
				return True
			else:
				return('There are no errors to report')

		elif msg.cmd[1] == 'list':
			if len(builtins.errors) > 0:
				outStr = 'Stored errors: '
				for i in range(len(builtins.errors)):
					errName = builtins.errors[i][0].__name__
					outStr += '%s: %s, ' %(str(i), errName)
				outStr = outStr[:-2] + '. '
				return(outStr)
			else:
				return('No stored errors to report.')
		
		else:
			try:
				errNum = int(msg.cmd[1])
			except:
				return('Syntax error. Usage: errors <errNum | last>.')

			try:
				err = builtins.errors[errNum]
			except IndexError:
				return('Error number is out of bounds')

			errString = fmtErr(builtins.errors[errNum])
			errLines = errString.splitlines()
			for el in errLines:
				msg.conn.send('PRIVMSG %s :%s\n' %(msg.channel, el))
			return True

	# Format an error trace into a more friendly format. 
	def fmtErr(self, err):
		errParts = traceback.format_exception(err[0], err[1], err[2])

		errString = ''.join(errParts)

		return errString

	# Reload options.py
	def reloadOpts(self, msg):
		if not(hasPriv(msg.nick, 'config', 20)):
			return(config.privrejectadmin)
		else:
			self.showdbg('Reloading options...')
			reload(options)
			return('Reloaded options.py')


	# Reload config.py
	def reloadConfig(self, msg):
		if not(hasPriv(msg.nick, 'config', 20)):
			return(config.privrejectadmin)
		else:
			self.showdbg('Reloading config...')
			reload(config)
			return('Reloaded config.py')
		

	# Reload a module by name
	def reloadByName(self, modName):
		
		module = self.library_dict[modName]
		builtins.lastMod = module

		regs = self

		for mod in self.funcregistry:
			if mod[0] == modName:
				funcregistry.pop(mod)

		for mod in self.helpregistry:
			if mod[0] == modName:
				funcregistry.pop(mod)

		for evtype in self.listenerregistry:
			for mod in self.listenerregistry[evtype]:
				if mod[0].__name__ == modName:
					self.listenerregistry[evtype].remove(mod)


		try:
			reload(module)
		except:
			self.showErr('Error reloading module %s' %modName)
			self.reportErr(sys.exc_info())
			return(False)
			

		if getattr(module, 'enabled', True):
			
			try:
				getattr(module, 'register')(regs)
				return(True)
			except:
				self.showErr('Error registering module %s' %modName)
				self.reportErr(sys.exc_info())
				return(False)

		else:
			return(True)
			

	# Register a new function
	def registerfunction(self, name, function):
		module = builtins.lastMod
		self.funcregistry[name] = [module, function]

	# Add a new listener
	def addlistener(self, event, function):
		module = builtins.lastMod
		if event not in self.listenerregistry:
			self.listenerregistry[event] = []
		self.listenerregistry[event].append([module, function])

	# Add a new help page
	def addhelp(self, name, function):
		module = builtins.lastMod
		self.helpregistry[name] = [module, function]

	# Function to return the auth object of a nick
	def getAuth(self, name):
		found = False
		for i in self.authlist:
			if i.nick == name:
				found = True
				result = i
				break
		if found:
			return i
		else:
			raise UserNotFound(name)

	# Function for getting the level of somebody
	# Works with both implicit and explicit authentication. 
	def getlevel(self, name):
		found = False
		iname = name
		for i in self.authlist:
			if i.nick == name:
				found = True
				flevel = i.level
		if found:
			return flevel
		else:
			return 0

	def getLevelStr(self, name):
		return self.levelToStr(self.getlevel(name))

	def levelToStr(self, level):
		if level < 0:
			return('invalid')
		try:
			return(config.privilegelevels[level])
		except: 
			return(self.levelToStr(level - 1))


	# Display data being received from the server
	# Prefixes it with server name and a >, then logs it

	def dispdata(self, todisp):
		for line in todisp.splitlines():
			outstr = '(%s)> %s\n' %(self.conn.host, line.rstrip())
			try:
				sys.stdout.write(outstr)
			except:
				outstrEnc = outstr.encode('ascii', 'replace').decode()
				sys.stdout.write(outstrEnc)
			self.logdata(outstr)

	# Output some debugging info to console/log
	# Prefixes it with server name and a *
	def showdbg(self, toshow):
		if not(isinstance(toshow, str)):
			toshow = str(toshow)
		for line in toshow.splitlines():
			if line:
				outstr = '(%s)* %s' %(self.conn.host, line.rstrip()) 
				self.logdata(outstr)

	# Show and log an error message. 
	# This prefixes the line with ! after the server part. 
	def showErr(self, toshow):
		if not(isinstance(toshow, str)):
			toshow = str(toshow)
		for line in toshow.splitlines():
			if line:
				outstr = '(%s)! %s' %(self.conn.host, line.rstrip()) 
				self.logdata(outstr)

	# Report an error to the error collector, and
	# also print it out line by line using showErr()
	def reportErr(self, err):
		formatted = traceback.format_exception(err[0], err[1], err[2])
		for l in formatted:
			self.showErr(l)
		builtins.errors.append(err)
		

	# Senddata function here for legacy purposes. 
	# You should always be doing conn.send now, or one of the other
	# conn.* methods. 
	def senddata(self, tosend, alt=False):
		self.conn.send(tosend, alt)

	# logdata(string): Puts the string in the log file, along with a timestamp
	# Prints the data to console as well. 

	def logdata(self, data):
		print(data)
		if options.logging:
			try:
				with open('log.' + self.conn.host, 'a', encoding = 'utf-8') as logfile:
					timestamp = time.strftime('[%y-%m-%d %H:%M:%S] ')
					logfile.write(timestamp + data + '\n')
					logfile.close()
			except: 
				raise
				print('!!!ERROR WITH LOG FILE!!!')

	def runPeriodics(self):
		etype = 'periodic'
		if etype in self.listenerregistry:
			for function in self.listenerregistry[etype]:
				l = function[0]
				target = function[1]
				periodicObj = periodic(self)
				try:
					target(periodicObj)
				except:
					self.reportErr(sys.exc_info())

			time.sleep(1)

	def BotStop(self, text, retval):
		self.showErr(text)
		raise BotStopEvent(text, retval)


	def ErrorAndStop(self, text, retval):
		self.reportErr(sys.exc_info())
		self.BotStop(text, retval)


	def JoinChannel(self, channelName):
		self.conn.joinChannel(channelName)
		self.chanMap[channelName] = ChannelMapEntry(channelName)


	def PartChannel(self, channelName):
		self.conn.partChannel(channelName)
		del self.chanMap[channelName]


	def processJoin(self, event):
		try:
			self.showdbg('Adding user %s to channel %s' % (event.nick, event.channel))
			self.chanMap[event.channel].addMember(event.nick)
		except Exception as e:
			self.reportErr(sys.exc_info())


	def processPart(self, event):
		try:
			self.chanMap[event.channel].removeMemberIfExists(event.nick)
		except Exception as e:
			self.reportErr(sys.exc_info())


	namesCache = {}

	def process353(self, event):
		channel = event.linesplit[4]
		if channel not in self.namesCache:
			self.namesCache[channel] = []
		names = event.linesplit[5:]
		if not names:
			return
		# First name will have a leading colon, remove it
		if names[0] and names[0][0] == ':':
			names[0] = names[0][1:]

		self.namesCache[channel] += names


	def process366(self, event):
		channel = event.linesplit[3]
		allNames = namesCache.pop(channel)
		self.chanMap[channel].refresh(allNames)

	


	def processNick(self, event):
		old = event.nick
		new = event.newNick
		for channelEntry in self.chanMap.values():
			channelEntry.renameIfExists(old, new)

	
	def getUsersInChannel(self, channel):
		userEntries = self.chanMap[channel].userMap.values()
		return map(str, userEntries)


	def getChannels(self):
		return self.chanMap.keys()
