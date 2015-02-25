#!/usr/bin/python3

#    MVpybot, a Python IRC bot.
#    Copyright (C) 2009-2014 Matt Ventura
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



# Not sure if this note is still relevant since I'm not the one who noticed it:
#    A note:
#       Please do not try to run the bot in IDLE. Your system will slow down.
#       The bot will run much better just from the commandline version of Python.
#    --Darren VanBuren

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

def botmain(botConn):

	# Expose connection to other functions
	global conn
	conn = botConn



	# Used for throttling of sending messages
	global lastMsgOut

	if conn.throttle:
		lastMsgOut = 0	

	# Announce that we are logging
	logdata(time.strftime('---- [ Session starting at %y-%m-%d %H:%M:%S ] ----'))


	showdbg('Initializing...')
	showdbg('Loading modules...')
	
	# Initialize authlist
	global authlist
	authlist = []

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
	# libracy_dict is a dictionary of { name : module } pairs
	global funcregistry
	global listenerregistry
	global helpregistry
	global library_list
	global library_dict

	# These functions have to be declared early on
	# due to dependencies. 

	funcregistry = {}
	listenerregistry = {}
	helpregistry = {}
	library_list = []
	library_dict = {}

	for file in os.listdir(os.path.abspath("modules")):
		pname, fileext = os.path.splitext(file)
		if fileext == '.py':
			try:
				module = __import__(pname)
			except:
				showErr('Error importing plugin ' + pname)
				reportErr(sys.exc_info())

			library_list.append(module)
			library_dict[pname] = module
			if hasattr(module, 'register') and getattr(module, 'enabled', 1):
				# These three functions are shoved into the module directly
				regs = registryFuncs()
				builtins.lastMod = module
				try:
					getattr(module, 'register')(regs)
				except:
					showErr('Error registering plugin ' + pname)
					reportErr(sys.exc_info())
	
	# Load the simple auth file if using implicit/simple auth
	# This file needs to be formatted as such:
	# username1 user
	# username2 admin
	# It must be a space in-between, and you must use the friendly-name
	# user levels, rather than numbers. 
	
	if not(conn.userAuth):
		try:
			with open('ausers') as f:
				auLines = f.readlines()
				for line in auLines:
					line = line.rstrip()
					lineParts = line.split(' ')
					authlist.append(asUser(lineParts[0], int(lineParts[1]), lineParts[2:]))
		except IOError:
			reportErr(sys.exc_info())
			showErr('Error loading implicit auth list.')
			return 255
		except: 
			reportErr(sys.exc_info())
			showErr('Unknown error while loading implicit auth list.')
			return 255
		
	
	# Legacy stuff
	host = conn.host
	port = conn.port

	# More legacy stuff
	builtins.host = conn.host

	# Set up logging
	conn.setLogger(logdata)

	# Legacy variable names
	cspass = conn.csp

	# Initialize these to almost-blank strings to avoid some problems
	line = ' '
	tosend = ' '

	# The variable initconn tells us if we need to do a full connection (True) 
	# or if we get to re-use it (False)
	if conn.fullyDone:
		pass
	else:
		conn.initialize()

	channels = conn.chans
	
	# For if we're reloading, this tries to reload the old auth list
	def loadauthlist():
		return builtins.authlist	

	# We only do this if we're using explicit authentication
	if conn.userAuth:
		try:
			authlist = loadauthlist()
		except:
			# If there's no auth list to load, load a blank one

			authlist = []


	# main loop
	conn.s.settimeout(5) # This sets the max time to wait for data
	# Note that this will also affect how often periodics are run

	while True:
		linebuffer = False
		try:
			linebuffer = conn.recv()
			if not(linebuffer):
				# Check if there was a socket error. If there was, tell the wrapper that. 
				logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: lost connection)'))
				return 255
	
		
		except socket.error:
			pass

		except:
			pass
		

		# If we got no data from the server, run periodics
		if not(linebuffer):
			type = 'periodic'
			if type in listenerregistry:
				for function in listenerregistry[type]:
					l = function[0]
					target = function[1]
					periodicObj = periodic(s, conn)
					try:
						target(periodicObj)
					except:
						reportErr(sys.exc_info())
	

				time.sleep(1)

		# What to do if we did get data
		else:
			# If the server dumped a bunch of lines at once, split them
			lines = linebuffer.split('\n')
			while len(lines) > 1:	 
				line = lines[0]		
				lines.pop(0)
				try:
					e = lineEvent(line, conn)
				except:
					showdbg('Failed basic line parsing! Line: ' + line)
					reportErr(sys.exc_info())
					continue
				
					

				#dispdata(line)

				# If the data we received was a PRIVMSG, do the usual privmsg parsing
				if e.type == 'privmsg':
					
					lstat = parse(e)
					
					try:
						if 'action' in lstat:

							if lstat['action'] == "restart":
								logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: restart requested)'))
								return 1

							if lstat['action'] == "die":
								logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: stop requested)'))
								return 0

							if lstat['action'] == "reload":
								if conn.userAuth:
									builtins.authlist = authlist							
								logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: reload requested)'))
								return 2

					except:
						reportErr(sys.exc_info())
	

				# Responding to pings is now part of the server object
				#if e.type == 'ping':
				#	out = 'PONG ' + e.target + '\n'
				#	senddata(out)

				# Fail gracefuly if the server gives us an error. 
				if e.type == 'error':
					logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: received error from server)'))
					return 255

				if (e.type == 'quit'):
					for i in authlist:
						if i.nick == e.nick:
							showdbg('Removing nick %s from authlist due to quit' %(e.nick))
							authlist.remove(i)

				if (e.type == 'nick'):
					for i in authlist:
						if i.nick == e.nick:
							showdbg('Upddating nick %s in authlist to %s' %(e.nick, e.newNick))
							i.nick = e.newNick
							

				# Run listeners of the apporpriate type
				if e.type:
					if e.type in listenerregistry:
						for function in listenerregistry[e.type]:
							l = function[0]
							target = function[1]
							
							try:
								target(e)
							except:
								reportErr(sys.exc_info())
	
					# Also run listeners who hook onto 'any'
					if 'any' in listenerregistry:
						for function in listenerregistry['any']:
							l = function[0]
							target = function[1]

							try:
								target(e)
							except:
								reportErr(sys.exc_info())


# This big function is called when we want to parse an incoming PRIVMSG
# e: the event, which we've already created
def parse(e):
	global authlist
	global helpregistry
	global funcregistry
	global listenerregistry
	
	# Legacy
	sender = e.nick
	channel = e.channel
	msg = e.message


	# Figure out if it is a channel message or a private message
	if (e.isPrivate):
		isprivate = 1
		channel = sender
	else:
		isprivate = 0

	run = ''
	out = ''
	length = len(msg)

	# Quick fix
	if (length == 0):
		msg = '(null)'


	# There are three ways to call a command:
	# #1: Use the command prefix, sett in options
	if (msg[0] == options.cmdprefix):
		cmd = msg[1:].split(' ')
		run = cmd[0]
		cmdstring = ' '.join(cmd)

	msgparts = msg.split(' ')


	# #2: Say the bot's name, followed by a colon and space
	if ((msgparts[0].lower() == options.NICK.lower() + ':') and (len(msgparts) > 1)):
		cmd = msgparts[1:]
		run = cmd[0].rstrip()
		cmdstring = ' '.join(cmd)

	# #3: Directly send the bot a PM
	if (isprivate == 1):
		cmd = msgparts[0:]
		run = cmd[0].rstrip()
		cmdstring = ' '.join(cmd)
	

	# Do this stuff if it is determined that we should try
	# to run a command
	if (run):

		msgObj = cmdMsg(channel, sender, options.NICK, cmd, run, isprivate)

		funcs = {'test' : testFunc, 'join' : joinFunc, 'part' : partFunc,
			'userinfo' : userinfoFunc, 'auth' : authFunc, 'auths' : authFunc, 'authenticate' : authFunc, 
			'level' : levelFunc, 'deauth' : deauthFunc, 'register' : registerUserFunc, 
			'pass' : passFunc, 'passwd' : passwdFunc, 'authdump' : authDump, 'errtest' : errTest,
			'modules' : modFunc, 'help' : helpFunc, 'err' : errFunc, 'errors' : errFunc,
			'reloadopts' : reloadOpts, 'reloadcfg' : reloadConfig, 'perm' : userMgmtFunc, 'user' : userMgmtFunc
		}

		

		try: 
			# Test command
				
			if run in funcs:
				out = funcs[run](msgObj)

			# Commands for stopping/starting/reloading/etc: This is important to read this.
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

			if (run == 'restart'):
				if (getlevel(sender) >= getPrivReq('power', 20)):
					showdbg('Restart requested')
					senddata('PRIVMSG %s :Restarting...\n' %channel)
					return {'action': "restart"}
				else:
					out = config.privrejectadmin

			elif (run == 'die'):
				if (getlevel(sender) >= getPrivReq('power', 20)):
					showdbg('Stop requested')
					senddata('PRIVMSG %s :Stopping...\n' %channel)
					return {'action': "die"}
				else:
					out = config.privrejectadmin

			elif (run == 'reload'):
				if (getlevel(sender) >= getPrivReq('power', 20)):
					showdbg('Reload requested')
					senddata('PRIVMSG %s :Reloading...\n' %channel)
					return {'action': "reload"}
				else:
					out = config.privrejectadmin

			# Generates a dummy error to test error-reporting capabilities. 
		
		except:
			reportErr(sys.exc_info())


			out = 'PRIVMSG %s :An error has occured in an internal function' %channel
		
		nodata = False
		try: 		
			if out == True:
				nodata = True
		except:
			pass
		if nodata:
			return {}
		
		
		if True:
			if (out):				
				if (out[0:7] != 'PRIVMSG'):
					out = 'PRIVMSG %s :%s' %(channel, out)
					

				senddata(out + '\n')

		# Try to run a module function since we didn't find an appropriate builtin
			else:
				if run in funcregistry:
					target = funcregistry[run]
					l = target[0]
					# Pass all this stuff in via our msgObj object
					msgObj = cmdMsg(channel, sender, options.NICK, cmd, run, isprivate)
					try: 
						out = target[1](msgObj)
						if out==True:
							return({})
						if (out.split(' ')[0] != 'PRIVMSG'):
							out = 'PRIVMSG %s :%s\n' %(channel, out)
					except:
						reportErr(sys.exc_info())
						out = 'PRIVMSG %s :An error has occured in a module' %channel
						


				else: 
					found = 0

				# Send out data to the server, assuming there's something to send. 
				try:
					if (out):				
						if (out[-1] != '\n'):
							out += '\n'
						senddata(out)

					# If the command was not found, tell the user that.
					# Note that this has to be enabled in config, since
					# it can end up doing annoying things sometimes. 
					elif config.cnf_enable:		
						out = 'PRIVMSG ' + channel + ' :Command not found'
						
						senddata(out + '\n')

				except:
					reportErr(sys.exc_info())

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
def syscmd(command):
	showdbg('SYSCMD called. Running "' + ' '.join(command) + '".')
	result = Popen(command, stdout = PIPE).communicate()[0]
	return result

# Tries to guess whether 'a' or 'an' should be used with a word
def getArticle(word):
	if word.lower() == 'user':
		return('a')
	elif word[0] in ('a', 'e', 'i', 'o', 'u'):
		return('an')
	else:
		return('a')

# Tries to find a privilege level in config.py
# Failing that, it will return the default argument. 
def getPrivReq(priv, default = 0):
	if priv in config.reqprivlevels:
		return(config.reqprivlevels[priv])
	else:
		return(default)

# Check if someone has a privilege
def hasPriv(nick, priv, default = 3):
	try:
		auth = getAuth(nick)
	except UserNotFound:
		return(0 >= getPrivReq(priv, default))
	if priv in auth.deny:
		return False
	elif priv in auth.grant:
		return True
	elif  (getlevel(nick) >= getPrivReq(priv, default)):
		return True
	else:
		return False


# Builtin command functions

def testFunc(msg):
	return('%s: test' %msg.nick)

def partFunc(msg):
	if hasPriv(msg.nick, 'chanMgmt', 20):
		channel = msg.cmd[1]
		senddata('PART %s\n' %channel)
		return('Left channel %s' %channel)
	else:
		return('%s: %s' %(msg.nick, config.privrejectadmin))

def joinFunc(msg):
	if hasPriv(msg.nick, 'chanMgmt', 20):
		channel = msg.cmd[1]
		senddata('JOIN %s\n' %channel)
		return('Joined channel %s' %channel)
	else:
		return('%s: %s' %(msg.nick, config.privrejectadmin))
		
def userinfoFunc(msg):

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
					
				
def userLookup(authName):

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

				
def userMgmtFunc(msg):
	
	if not(hasPriv(msg.nick, 'acctMgmt', 20)):
		return(config.privrejectgeneric)
	
	if len(msg.cmd) == 1:
		return('''This function requires more arguments. See 'help user' for details.''')

	

	# Make a copy since we'll be changing this
	args = msg.cmd[1:]
	argsFull = args # Just in case

	# First part: -u for user or -n for nick
	# -n can only work when the user is logged in
	# -u should be able to work any timet
	if args[0][0:2] == '-u':
		user = True
	elif args[0][0:2] == '-n':
		user = False
	else:
		return('''Incorrect syntax. See 'help user' for details. ''')
	
	if len(args[0]) > 2:
		name = args[0][2:]
		args = args[1:]
	else:
		name = args[1]
		args = args[2:]
	 
	if len(args) < 1:
		return('''This function requires more arguments. See 'help user' for details.''')
		
	# Actions: level, privs/priv
	if args[0] == 'level':
		action = 0
		args = args[1:]
	elif args[0] == 'privs' or args[0] == 'priv':
		action = 1
		args = args[1:]
	elif args[0] == 'add':
		action = 2
	else:
		return('''Action must be 'add', 'level' or 'privs'.''')



	if action == 0:
		if len(args) == 0:
			return('Not enough arguments.')
		elif args[0] == 'get':
			if user:
				try:
					authEntry = userLookup(name)
				except UserNotFound:
					return('That user was not found')
				level = authEntry.level
				return('User %s is level %s' %(name, str(level)))
			else:	
				try:
					authEntry = getAuth(name)
				except UserNotFound:
					return('That user was not found')
				level = authEntry.level
				return('User %s is level %s' %(name, str(level)))

		elif args[0] == 'set':
			try:
				newLevel = int(args[1])
			except:
				return('Level must be an integer.')
			if user:
				try:
					chgUserLvl(name, newLevel)
				except UserNotFound:
					return('User not found')
				return('''Changed level for user '%s' to %s. ''' %(name, str(newLevel)))


			else:
				try:
					authEntry = getAuth(name)
				except UserNotFound:
					return('User not found.')

				authEntry.level = newLevel

				try:
					chgUserLvl(authEntry.authName, newLevel)
				except:
					return('''Changed level for user, but couldn't update file.''')

				return('''Changed level for nick '%s' to %s. ''' %(name, str(newLevel)))

		else:
			return('''Action must be 'get' or 'set'.''')
					
				
	if action == 1:
		if len(args) == 0:
			return('Not enough arguments.')		
		elif args[0] == 'get':
			try:
				if user:
					authEntry = userLookup(name)

				else:
					authEntry = getAuth(name)
			except UserNotFound:
				return('User not found.')

			return('User %s has privileges: %s. ' %(name, formatPerms(authEntry.grant, authEntry.deny, ', ')))


		if args[0] == 'clear':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except UserNotFound:
						return('User not found.')
					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						elif i in deny:
							deny.remove(i)
					try:
						chgUserPrivs(name, grant, deny)
					except UserNotFound:
						return('User was found initially, but not when updating.')
					return('Cleared privilege(s) from user %s.' %name)

				else:
					try:
						authEntry = getAuth(name)
					except UserNotFound:
						return('User not found.')
						

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						elif i in deny:
							deny.remove(i)

					try:
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Cleared privilege(s), but could not update file.')
						
					return('''Cleared privilege(s) for nick '%s'.''' %name)
							

					
			else:
				if user:
					try:
						chgUserPrivs(name, set(), set())
					except UserNotFound:
						return('User not found.')

					return('Cleared special privileges for user %s.' %name)

				else:
					try:
						authEntry = getAuth(name)
					except UserNotFound:
						return('Could not find that nick.')
						
					authEntry.grant = set()
					authEntry.deny = set()
					try:
						chgUserPrivs(authEntry.authName, set(), set())
					except UserNotFound:
						return('Cleared special privileges for nick, but could not update file.')
					return('Cleared special privileges for nick %s.' %name)

		if args[0] == 'grant':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except UserNotFound:
						return('User not found.')
						
					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in deny:
							deny.remove(i)
						grant.add(i)
					try: 
						chgUserPrivs(name, grant, deny)
					except UserNotFound:
						return('User was found initially but not while updating')
					return('Changed privilege(s) for user %s.' %name)
				else:
					try:
						authEntry = getAuth(name)
					except UserNotFound:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in deny:
							deny.remove(i)
						grant.add(i)

					try: 
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Changed privileges, but could not update file.')
					return('''Changed privileges for nick '%s'.''' %name)

			else:				
				return('Not enough arguments.')
	
		if args[0] == 'deny':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						deny.add(i)
					try:
						chgUserPrivs(name, grant, deny)
					except:
						Raise(Exception('User was found initially, but not when updating.'))

					return('Changed privilege(s) for user %s.' %name)
				else:
					try:
						authEntry = getAuth(name)
					except UserNotFound:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						deny.add(i)

					try:
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Changed privileges, but could not update file.')
					
					return('''Changed privileges for nick '%s'.''' %name)

			else:				
				return('Not enough arguments.')

	if action == 2:
		if conn.userAuth:
			return('To add users in explicit auth mode, user the register command.')
		else:
			try:
				addUser(name)
			except UserAlreadyExistsError:
				return('Error: User already exists')
			return('Added user %s' %name)
			
		
			

def formatPerms(grant, deny, spacer = ' '):
	outStr = ''
	for i in grant:
		outStr += '+%s%s' %(i, spacer)
	for i in deny:
		outStr += '-%s%s' %(i, spacer)
	outStr = outStr[:(-1*len(spacer))]	
	return(outStr)



def authFunc(msg):

	if not(conn.userAuth):
		return(config.simpleAuthNotice)

	elif len(msg.cmd) != 3:
		return('Incorrect syntax. Usage: auth <username> <pass>')

	elif not(msg.isPrivate):
		return('''Use this in a /msg, don't use it in a channel. Now go change your passsword.''')
	
	elif getlevel(msg.nick) != 0:
		return('You are already authenticated. If you would like to change accounts, you can deauth and try again.')

	else:
		iName = msg.cmd[1].rstrip()
		iPass = msg.cmd[2].rstrip()

		with open('users', 'r') as f:
			correct = False
			found = False
			showdbg('%s is attempting to authenticate.' %iName)

			for fLine in f.readlines():
				fLine = fLine.rstrip()
				lineParts = fLine.split(' ')

				if lineParts[0] == iName:
					found = True
					fPass = lineParts[1]
					fLevel = int(lineParts[2])
					perms = lineParts[3:]
					if iPass == fPass:
						correct = True
					elif ('HASH:' + sha(iPass.encode()).hexdigest()) == fPass:
						correct = True


						
		if found:
			if correct:
				if perms:
					authlist.append(aUser(msg.nick, iName, fLevel, perms))
				else:
					authlist.append(aUser(msg.nick, iName, fLevel))
					

				showdbg('%s is authenticated' %iName)

				if msg.run == 'auths':
					return(True)

				else:
					return('Password accepted, you are now authenticated')

			else:
				
				showdbg('%s tried to authenticate, but their password was rejected' %iName)
				return('Incorrect password')

		else:

			showdbg('%s tried to authenticate, but their username was not found' %iName)
			return('Incorrect username')
					
def levelFunc(msg):
	
	if not(hasPriv(msg.nick, 'acctInfo', 3)):
		return(config.privrejectgeneric)

	if len(msg.cmd) == 1:
		lNick = msg.nick

	else:
		lNick = msg.cmd[1]

	try:
		lAuth = getAuth(lNick)
	except UserNotFound:
		return('User not found.')
	strLevel = levelToStr(lAuth.level)

	outStr = ''

	outStr += '%s is level %s (%s %s). ' %(lNick, str(lAuth.level), getArticle(strLevel), strLevel)

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

def deauthFunc(msg):
	
	if not(conn.userAuth):
		return(config.simpleAuthNotice)

	else:
		found = False
		iName = msg.nick
		if getlevel(iName) != 0:
			for i in authlist:
				
				alName = i.nick
				if alName == iName:
					authlist.remove(i)
					found = True

			if found:
				return('Deauthenticated')

			else:
				return('An error has occured')

		else:
			return('You are not authenticated')

def registerUserFunc(msg):
	
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


def addUser(name, password = None, level = config.newUserLevel, grant = set(), deny = set()):
	
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


# Function to change a user's password
def chgUserPass(user, newPass):
	
	if not(conn.userAuth):

		raise(Exception('Simple auth is enabled, so there are no passwords to change'))

	else:

		showdbg('Attempting to change password for %s' %user)

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
					showdbg('Found entry, modifying...')
					found = True

				else:
					outData += fLine

		if found:
			with open(authFile, 'w') as f:
				f.write(outData)
				f.truncate()
			
			showdbg('Changed password for %s' %user)
			return

		else:
			
			showdbg('Could not find user %s' %user)
			raise(UserNotFound(user))
				
# Function to change a user's level
def chgUserLvl(user, newLevel):
	

	showdbg('Attempting to change level for %s' %user)

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
				showdbg('Found entry, modifying...')
				found = True

			else:
				outData += fLine

	if found:
		with open(authFile, 'w') as f:
			f.write(outData)
			f.truncate()
		
		showdbg('Changed level for %s' %user)
		return

	else:
		
		showdbg('Could not find user %s' %user)
		raise(UserNotFound(user))
			
		
# Function to change a user's privileges
def chgUserPrivs(user, grant, deny):
	

	showdbg('Attempting to change privs for %s' %user)
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
				showdbg('Found entry, modifying...')
				found = True

			else:
				outData += fLine

	if found:
		with open(authFile, 'w') as f:
			f.write(outData)
			f.truncate()
		
		showdbg('Changed privs for %s' %user)
		return

	else:
		
		showdbg('Could not find user %s' %user)
		raise(UserNotFound(user))

class UserNotFound(Exception):
	def __init__(self, user):
		self.user = user
	def __str__(self):
		return('Could not find user %s' %self.user)

def passFunc(msg):
	
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
						

def passwdFunc(msg):
	
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

def authDump(msg):
	
	if not(conn.userAuth):
		return(config.simpleAuthNotice)

	elif not(hasPriv(msg.nick, 'acctMgmt', 20)):
		return(config.privrejectadmin)

	else:
		showdbg('Dumping auth list. Format is nick, authname, level')
		for i in authlist:
			showdbg('%s, %s, %s, %s, %s' %(i.nick, i.authName, str(i.level), str(i.grant), str(i.deny)))
			return('Dumped auth list to console')

def errTest(msg):

	if hasPriv(msg.nick, 'errors', 20):
		showdbg('Error test requested')
		senddata('PRIVMSG %s :Error requested. Check the console.\n' %msg.channel)
		time.sleep(1)
		raise(Exception('User-requested error'))
	else:
		return(config.privrejectadmin)



def modFunc(msg):
	
	global listenerregistry
	global helpregistry
	global funcregistry
	global library_dict

	if (len(msg.cmd) > 1):
		# Reload looks at existing modules and reloads them
		# You can also specify a specific module to reload
		if msg.cmd[1] == 'reload':
			if hasPriv(msg.nick, 'modules', 20):
				global library_dict
				if len(msg.cmd) == 2:	
					
					errored = []
					for modName in library_dict:
						try:
							if reloadByName(modName):
								pass
							else:
								errored.append(modName)

						except:
							reportErr(sys.exc_info())
							errored.append(modName)
					showdbg('Reloaded all modules')
					out = 'PRIVMSG %s :Reloaded all modules. ' %(msg.channel)
					if errored:
						out += 'The following modules encountered errors: '
						for modName in errored:
							out += modName + ', '
						out = out[:-2] + '. '
				else:
					found = []
					notFound = []
					errored = []
					for modName in msg.cmd[2:]: 
						
						if modName in library_dict:
							
							try: 
								if reloadByName(modName):
									pass
								else:
									errored.append(modName)
								found.append(modName)
								

							except:
								reportErr(sys.exc_info())
								errored.append(modName)

						else:
							notFound.append(modName)
					
					out = 'PRIVMSG %s :' %msg.channel
					if found:
						out += 'Successfully reloaded: '
						for modName in found:
							out += modName + ', '
						out = out[:-2] + '. '

					if notFound:
						out += 'Could not find: '
						for modName in notFound:
							out += modName + ', '
						out = out[:-2] + '. '
					
					if errored:
						out += 'Encountered errors with: '
						for modName in errored:
							out += modName + ', '
						out = out[:-2] + '. '


			else: 
				out = 'PRIVMSG %s :%s' %(msg.channel, config.privrejectgeneric)

		# Rescan essentially redoes the original module scanning process
		# Note that this doesn't necessarily reload a module. 
		if msg.cmd[1] == 'rescan':
			if hasPriv(msg.nick, 'modules', 20):
				showdbg('Rescan requested')
				funcregistry = {}
				listenerregistry = {}
				helpregistry = {}	
				library_list = []
				library_dict = {}
				for file in os.listdir(os.path.abspath("modules")):
					pname, fileext = os.path.splitext(file)
					if fileext == '.py':
						module = __import__(pname)
						library_list.append(module)
						library_dict[pname] = module
						if hasattr(module,'register') and getattr(module, 'enabled', 1):
							r = registryFuncs()
							getattr(module, 'register')(r)
				showdbg('Rescan complete')
				out = 'PRIVMSG %s :Rescanned' %(msg.channel) 
			else: 
				out = 'PRIVMSG %s :%s' %(msg.channel, config.privrejectgeneric)
		# Prints a list of functions or listeners
		if msg.cmd[1] == 'show':
			if not(hasPriv(msg.nick, 'showmods', 3)):
				return(config.privrejectgeneric)
			if len(msg.cmd) == 2:
				out = 'PRIVMSG %s :Currently active modules: ' %(msg.channel)
				for item in library_dict:
					if getattr(library_dict[item], 'enabled', True):
						out += str(item) + ', '
				out = out[:-2]
			
			if len(msg.cmd) == 3:

				if (msg.cmd[2] == 'disabled'):
					out = 'PRIVMSG %s :Currently active modules: ' %(msg.channel)
					for item in library_dict:
						if not(getattr(library_dict[item], 'enabled', True)):
							out += str(item) + ', '
					out = out[:-2]

				if (msg.cmd[2] == 'allmods'):
					out = 'PRIVMSG %s :Currently active modules: ' %(msg.channel)
					for item in library_dict:
						out += str(item) + ', '
					out = out[:-2]	

				if (msg.cmd[2] == 'functions'):
					out = 'PRIVMSG %s :Currently active (non builtin) commands: ' %(msg.channel)
					for item in list(funcregistry):
						
						out += str(item)+', '
					out = out[:-2]
				
				if (msg.cmd[2] == 'listeners'):
					out='PRIVMSG %s :Currently active (non builtin) listeners: ' %(msg.channel)
					for evtype in list(listenerregistry):
						for listener in listenerregistry[evtype]:
							function = listener[1]
							fstr = str(function)
							fstr = fstr.split(' ')[1]
							out += '%s (%s), ' %(fstr, evtype)
					out = out[:-2]

				if (msg.cmd[2] == 'help'):
					out = 'PRIVMSG %s :Currently active (non builtin) help: ' %(msg.channel)
					for item in list(helpregistry):
						out += str(item)+', '
					out = out[:-2]

	else:
		out = 'PRIVMSG %s :Wrong number of arguments. Usage: modules action [arguments] ' %(msg.channel)


	return(out)

def helpFunc(msg):
	
	if len(msg.cmd) == 1:
		return('PRIVMSG %s :%s Use help <command> for help on a particular command. To use a command either say %s: <command> or %scommand.\n' %(msg.channel, config.defaulthelp, builtins.NICK, options.cmdprefix))
	else:
		msg.cmd[1] = msg.cmd[1].rstrip()
		handled = False

		if msg.cmd[1] in helpregistry:
			item = helpregistry[msg.cmd[1]]
			l = item[0]
			
			handled = True
			target = item[1]
			
			out = target(helpCmd(msg.channel, msg.cmd[1:]))
			if out.find('PRIVMSG') == -1:
				out = 'PRIVMSG %s :%s' %(msg.channel, out)

			return(out)

			return('Either that command does not exist, or help has not been written for it. ')

def errFunc(msg):
	if getlevel(msg.nick) < getPrivReq('errors', 20):
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
				
				senddata('PRIVMSG %s :%s\n' %(msg.channel, el))
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
			senddata('PRIVMSG %s :%s\n' %(msg.channel, el))
		return True





def fmtErr(err):
	errParts = traceback.format_exception(err[0], err[1], err[2])

	errString = ''.join(errParts)

	return errString


def reloadOpts(msg):
	if not(hasPriv(msg.nick, 'config', 20)):
		return(config.privrejectadmin)
	else:
		showdbg('Reloading options...')
		reload(options)
		return('Reloaded options.py')


def reloadConfig(msg):
	if not(hasPriv(msg.nick, 'config', 20)):
		return(config.privrejectadmin)
	else:
		showdbg('Reloading config...')
		reload(config)
		return('Reloaded config.py')
	

def reloadByName(modName):
	
	module = library_dict[modName]
	builtins.lastMod = module

	regs = registryFuncs()

	for mod in funcregistry:
		if mod[0] == modName:
			funcregistry.pop(mod)

	for mod in helpregistry:
		if mod[0] == modName:
			funcregistry.pop(mod)

	for evtype in listenerregistry:
		for mod in listenerregistry[evtype]:
			if mod[0].__name__ == modName:
				listenerregistry[evtype].remove(mod)


	try:	
		reload(module)
	except:
		showErr('Error reloading module %s' %modName)
		reportErr(sys.exc_info())
		return(False)
		

	if getattr(module, 'enabled', True):
		
		try:
			getattr(module, 'register')(regs)
			return(True)
		except:
			showErr('Error registering module %s' %modName)
			reportErr(sys.exc_info())
			return(False)

	else:
		return(True)
		

def registerfunction(name, function):
	module = builtins.lastMod
	funcregistry[name] = [module, function]

def addlistener(event, function):
	module = builtins.lastMod
	if event in listenerregistry:
		listenerregistry[event].append([module, function])
	else:
		listenerregistry[event] = []
		listenerregistry[event].append([module, function])

def addhelp(name, function):
	module = builtins.lastMod
	helpregistry[name] = [module, function]

class registryFuncs:
	def __init__(self):
		self.registerfunction = registerfunction
		self.addlistener = addlistener
		self.addhelp = addhelp

# Function to return the auth object of a nick
def getAuth(name):
	found = False
	for i in authlist:
		if i.nick == name:
			found = True
			result = i
			break
	if found:
		return i
	else:
		raise(UserNotFound(name))
		
	

		



# Function for getting the level of somebody
# Works with both implicit and explicit authentication. 
def getlevel(name):
	found = 0
	iname = name
	for i in authlist:
		if i.nick == name:
			found = 1
			flevel = i.level
	if found == 1:
		return flevel
	else:
		return 0


def getLevelStr(name):
	return levelToStr(getlevel(name))

def levelToStr(level):
	if level < 0:
		return('invalid')
	try:
		return(config.privilegelevels[level])
	except: 
		return(levelToStr(level - 1))

# Same thing with this. 
class helpCmd: 
	def __init__(self, channel, cmd):
		self.channel = channel
		self.cmd = cmd

# Not much to do here, just passing in some useful functions
class periodic:
	def __init__(self, socket, conninfo):
		self.socket = socket
		self.conninfo = conninfo
		self.sendata = senddata
		self.numlevel = numlevel
		self.getlevel = getlevel
		self.hasPriv = hasPriv

# This is the class used for when an external function needs to
# be called. This stuff gets mostly pre-processed so the contructor
# doesn't do much. 
class cmdMsg:
	def __init__(self, channel, nick, botnick, cmd, run, isPrivate):
		self.channel = channel
		self.nick = nick
		self.getlevel = getlevel
		self.botnick = botnick
		self.cmd = cmd
		self.syscmd = syscmd
		self.run = run
		self.numlevel = getlevel
		self.senddata = senddata
		self.showdbg = showdbg
		self.getLevelStr = getLevelStr
		self.levelToStr = levelToStr
		self.showErr = showErr
		self.hasPriv = hasPriv
		self.isPrivate = isPrivate

# This is the big one. This is what gets passed to listeners. 
# Here, the constructor actually does stuff. 
# To-do: NICK events
class lineEvent:
	def __init__(self, line, conninfo ):
		self.line = line.rstrip()
		self.conninfo = conninfo
		self.conn = conninfo
		self.senddata = conninfo.send
		self.getlevel = getlevel
		self.numlevel = getlevel
		self.showdbg = showdbg
		self.showErr = showErr
		self.getLevelStr = getLevelStr
		self.levelToStr = levelToStr
		self.linesplit = self.line.split(' ')
		self.userString = ''
		self.type = ''
		self.syscmd = syscmd
		self.hasPriv = hasPriv

		if self.linesplit[0] == 'PING':
			self.type = 'ping'
			self.ping = self.line.split()
			self.target = self.ping[1]
			return(None)
		
		if self.linesplit[0] == 'ERROR':
			self.type = 'error'
			return(None)
		
		if self.linesplit[1] == 'PART':
			self.type = 'part' 
			self.userString = self.linesplit[0]
			self.channel = self.linesplit[2]
			if len(self.linesplit) >= 4:
				self.reason = self.linesplit[3][1:]

		if self.linesplit[1] == 'JOIN':
			self.type = 'join'
			self.userString = self.linesplit[0]
			self.channel = self.linesplit[2]
			if len(self.linesplit) >= 4:
				self.reason = self.linesplit[3][1:]

		if self.linesplit[1] =='NICK':
			self.type = 'nick'
			self.userString = self.linesplit[0]
			self.newNick = self.linesplit[2]
		
		if self.linesplit[1] =='QUIT':
			self.type = 'quit'
			self.userString = self.linesplit[0]
			self.reason = self.linesplit[2][1:]

		if self.linesplit[1] == 'PRIVMSG':
			self.type = 'privmsg'
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


		if self.userString:
			part1 = self.userString.split(':')[1]
			part2 = part1.split('!')
			part3 = part2[1].split('@')
			self.nick = part2[0]
			self.user = part3[0]
			self.realName = part3[1]

		if not(self.type):
			self.type = self.linesplit[1]

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


# Display data being received from the server
# Prefixes it with server name and a >, then logs it

def dispdata(todisp):
	for line in todisp.splitlines():
		outstr = '(%s)> %s\n' %(host, line.rstrip())
		try:
			sys.stdout.write(outstr)
		except:
			outstrEnc = outstr.encode('ascii', 'replace').decode()
			sys.stdout.write(outstrEnc)
		logdata(outstr)

# Output some debugging info to console/log
# Prefixes it with server name and a *
def showdbg(toshow):
	for line in toshow.splitlines():
		if line:
			outstr = '(%s)* %s' %(conn.host, line.rstrip()) 
			logdata(outstr)

def showErr(toshow):
	for line in toshow.splitlines():
		if line:
			outstr = '(%s)! %s' %(conn.host, line.rstrip()) 
			logdata(outstr)

def reportErr(err):
	formatted = traceback.format_exception(err[0], err[1], err[2])
	for l in formatted:
		showErr(l)
	builtins.errors.append(err)
	

# senddata: Send data to the server, output it to the console, and log it
# senddata(string): uses the specified string, handling multiple lines properly
# senddata(string, alt): displays/logs a different string, useful for hiding passwords
# 	Note that this usage is *not* compatible with multi-line input
def senddata(tosend, alt = False):
	
	conn.send(tosend, alt)

# logdata(string): Puts the string in the log file, along with a timestamp
# Seperates multi-line input automatically

def logdata(data):
	print(data)
	if options.logging:
		try:	
			with open('log.' + conn.host, 'a', encoding = 'utf-8') as logfile:
				timestamp = time.strftime('[%y-%m-%d %H:%M:%S] ')
				logfile.write(timestamp + data + '\n')
				logfile.close()
		except: 
			print('!!!ERROR WITH LOG FILE!!!')
