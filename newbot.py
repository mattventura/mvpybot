#!/usr/bin/python

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

def botmain(botsocket, conn, initconn):


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


	# Used for throttling of sending messages
	global lastMsgOut

	if conn.throttle:
		lastMsgOut = 0	

	# Our socket
	# It comes pre-connected
	s = botsocket 

	# logdata(string): Puts the string in the log file, along with a timestamp
	# Seperates multi-line input automatically

	def logdata(data):
		if options.logging:
			try:	
				with open('log.' + conn.host, 'a', encoding = 'utf-8') as logfile:
					timestamp = time.strftime('[%y-%m-%d %H:%M:%S] ')
					logfile.write(timestamp + data + '\n')
					logfile.close()
			except: 
				print('!!!ERROR WITH LOG FILE!!!')

	

	# Announce that we are logging
	logdata(time.strftime('---- [ Session starting at %y-%m-%d %H:%M:%S ] ----'))


	# senddata: Send data to the server, output it to the console, and log it
	# senddata(string): uses the specified string, handling multiple lines properly
	# senddata(string, alt): displays/logs a different string, useful for hiding passwords
	# 	Note that this usage is *not* compatible with multi-line input
	def senddata(tosend, alt = False):
			
		sendparts = tosend.split('\n')

		if (len(sendparts) > 2):
			for part in sendparts[:-1]:
				senddata(part + '\n')

		else:
			global lastMsgOut
			if conn.throttle:
				timeSinceLast = time.time() - lastMsgOut
				if timeSinceLast < conn.throttle:
					time.sleep(conn.throttle - timeSinceLast)
			
			s.sendall(tosend.encode())
			lastMsgOut = time.time()

			for part in sendparts:
				if len(part)>1:
					if alt:
						part = alt
					outstr = '(%s)< %s' %(host, part.rstrip())
					print(outstr)
						
					logdata(outstr)
				
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
				print(outstr)
				logdata(outstr)
	
	def showErr(toshow):
		for line in toshow.splitlines():
			if line:
				outstr = '(%s)! %s' %(conn.host, line.rstrip()) 
				print(outstr)
				logdata(outstr)
	
	showdbg('Initializing...')
	showdbg('Loading modules...')

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
	global authlist
	authlist = []

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
	# Class definitions

	# Define our message class (Not used anymore)
	class message:
		line = ""

	# This is the class used for when an external function needs to
	# be called. This stuff gets mostly pre-processed so the contructor
	# doesn't do much. 
	class cmdMsg:
		def __init__(self, channel, nick, botnick, cmd, syscmd, run, senddata, showdbg):
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

	# Same thing with this. 
	class helpCmd: 
		def __init__(self, channel, cmd):
			self.channel = channel
			self.cmd = cmd

	# Not much to do here, just passing in some useful functions
	class periodic:
		def __init__(self, socket, conninfo, senddata, numlevel, getlevel):
			self.socket = socket
			self.conninfo = conninfo
			self.sendata = senddata
			self.numlevel = numlevel
			self.getlevel = getlevel

	# This is the big one. This is what gets passed to listeners. 
	# Here, the constructor actually does stuff. 
	# To-do: NICK events
	class lineEvent:
		def __init__(self, line, socket, conninfo, senddata, numlevel, getlevel):
			self.line = line.rstrip()
			self.socket = socket
			self.conninfo = conninfo
			self.senddata = senddata
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
		def __init__(self, nick, authName, level):
			self.nick = nick
			self.authName = authName
			self.level = level

		def rename(self, newNick):
			self.nick = newNick

		def chgLvl(self, newLevel):
			self.level = newLevel
		

	class asUser:
		def __init__(self, nick, level):
			self.nick = nick
			self.authName = nick
			self.level = level

		def chgLvl(self, newLevel):
			self.level = newLevel
			
	funcregistry = {}
	listenerregistry = {}
	helpregistry = {}

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

	library_list = []
	library_dict = {}
	for file in os.listdir(os.path.abspath("modules")):
		pname, fileext = os.path.splitext(file)
		if fileext == '.py':
			try:
				module = __import__(pname)
			except:
				showErr('Error importing plugin ' + pname)
				showErr(traceback.format_exc())
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
					showErr(traceback.format_exc())
	
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
			showErr(traceback.format_exc())
			return(False)
			

		if getattr(module, 'enabled', True):
			
			try:
				getattr(module, 'register')(regs)
				return(True)
			except:
				showErr('Error registering module %s' %modName)
				showErr(traceback.format_exc())
				return(False)

		else:
			return(True)
			

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
					authlist.append(asUser(lineParts[0], int(lineParts[1])))
		except IOError:
			showErr('Error loading implicit auth list.')
			return 255
		except: 
			showErr('Unknown error while loading implicit auth list.')
			return 255
		
	
	# Legacy stuff
	host = conn.host
	port = conn.port

	# More legacy stuff
	builtins.host = host


	# Legacy variable names
	cspass = conn.csp
	channels = conn.chans

	

	line = ' '

	tosend = ' '
	# The variable initconn tells us if we need to do a full connection (True) 
	# or if we get to re-use it (False)
	if initconn:

		# If we have a password, send it first 
		if conn.password:
			senddata('PASS %s\n' %(conn.password), 'PASS <censored>')
		# Tell the server the nick
		senddata('NICK %s\n' %(options.NICK)) 
		line = s.recv(1024).decode()
		dispdata(line)
		time.sleep(1)
		s.settimeout(5)
		# Some servers have some anti-exploit stuff enabled, where you
		# have to respond to a ping really early on to make sure you're real. 
		try:
			line = s.recv(1024).decode()
			dispdata(line)
			if (line.find('PING') == 0):
				pingValue = line.split(" ")[1]
				senddata("PONG " + pingValue)
		except:
			pass
			

		# Send the USER line
		senddata(conn.userString + '\n')  

		s.settimeout(60)

		# Try to wait until we know we're connected
		while (line.find('001')<1):
			line = s.recv(1024).decode()
			dispdata(line)

	showdbg('Connected')

	if initconn:
		# Identify with nickserv.
		if cspass:
			out = 'PRIVMSG nickserv identify ' + cspass + '\n'
			senddata(out)

		# Join channels.
		for chan in channels:
			out = 'JOIN ' + chan + '\n'
			senddata(out)

		showdbg('Joined channels')

	# For if we're reloading, this tries to reload the old auth list
	def loadauthlist():
		return builtins.authlist	

	# We only do this if we're using explicit authentication
	if conn.userAuth:
		try:
			authlist = loadauthlist()
		except:
			# This is a fix for stuff

			authlist = []


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

			try: 
				# Test command
				if (run == 'test'):
					out = 'PRIVMSG ' + channel + ' :' + sender + ': test'

				# Join a channel
				if (run == 'join'):
					if (getlevel(sender) >= 20):
						channel = cmd[1]
						out='JOIN ' + channel
					else:
						out = 'PRIVMSG ' + channel + ' : ' + sender + ': '+config.privrejectadmin

				# Leave a channel
				if (run == 'part'):
					if (getlevel(sender) >= 20):
						channel = cmd[1]
						out = 'PART ' + channel
					else:
						out = 'PRIVMSG ' + channel + ' : ' + sender + ': ' + config.privrejectadmin
			
				# Gets the level of a user stored in the auth file. 
				# Note that this does NOT tell you what level a currently-connected
				# user is (unless using implicit auth). 
				if (run == 'user'):
					if (len(cmd) != 2):
						out = 'PRIVMSG ' + channel + ' :Incorrect usage. Usage: user <username>'
					else:
						if conn.userAuth:
							username = cmd[1]
							f = open('users')
							for line in f.readlines():
								line = line.rstrip()
								if line.find(username) != -1:
									linesplit = line.split(' ')
									username = linesplit[0]
									password = linesplit[1]
									level    = int(linesplit[2])
									levelStr = levelToStr(level)

									if levelStr[0] in ('a', 'e', 'i', 'o', 'u'):
										article = 'an'
									else:
										article = 'a'

									out = 'PRIVMSG ' + channel + ' :' + username + ' is level ' + str(level) + ' (' + article + ' ' + levelStr + '). '

									
										

							f.close()

						else:
							username = cmd[1]
							f = open('ausers')
							for line in f.readlines():
								line = line.rstrip()
								if line.find(username) != -1:
									linesplit = line.split(' ')
									username = linesplit[0]
									level    = linesplit[1]
									out = 'PRIVMSG ' + channel + ' :' + username + ' is a ' + level
							f.close()

				# Explicit auth only: Authenticate with your username and password
				# Obviously you shouldn't type this in a channel, only PM
				# 'auths' is the same but doesn't send a reply on success. 
				if ((run == 'auth') or (run == 'authenticate') or (run == 'auths')):
					if not(conn.userAuth):
						out = 'PRIVMSG ' + channel + ' :' + config.simpleAuthNotice
	
					elif len(cmd) != 3:
						out = 'PRIVMSG ' + channel + ' :Incorrect syntax. Usage: auth <username> <pass>'

					else:
						if isprivate == 1:
							if getlevel(sender) > 0:
								out = 'PRIVMSG %s :You are already authenticated. If you would like to change accounts, you can deauth first and try again.' %(channel)
							else:
								iname = cmd[1].rstrip()
								ipass = cmd[2].rstrip()
								f = open('users')
								correct = 0
								found = 0
								showdbg( iname + ' is attempting to authenticate.' )
								for line in f.readlines():
									line = line.rstrip()
									linestuff = line.split(' ')
									if linestuff[0].find(iname) != -1:
										found = 1
										linesplit = line.split(' ')
										fpass = linesplit[1]
										flevel = int(linesplit[2])
										if ipass == fpass:
											correct = 1
										elif ('HASH:' + sha(ipass.encode()).hexdigest()) == fpass:
											correct = 1

								if found == 1:
									if correct == 1:
										if run == 'auths':
											out = '(none)'
										else:
											out = 'PRIVMSG ' + channel + ' :Correct'
										showdbg(iname + " is authenticated")
										authlist.append(aUser(sender, iname, flevel))
										#print authlist

									else:
										out = 'PRIVMSG ' + channel + ' :Incorrect'
										showdbg(iname + " failed to authenticate")

								else:
									out='PRIVMSG ' + channel + ' :Not found'
									showdbg(iname + "was not found in the users file")

						else:
							out='PRIVMSG ' + channel + ' :' + sender + ': Use this function with /msg, don\'t use it in a channel.'
				# Gets your current level
				if (run == 'level'):
					if (len(cmd) == 1):
						lNick = sender
					else:
						lNick = cmd[1]
					level = getlevel(lNick)
					rlevel = levelToStr(level)
					out = 'PRIVMSG ' + channel + ' :' + lNick + ' is level ' + str(level) + ' (' + rlevel + ').'

				# Log off
				if (run == 'deauth'):
					if not(conn.userAuth):
						out = 'PRIVMSG ' + channel + ' :' + config.simpleAuthNotice
					else: 
						found = 0
						iname = sender
						if getLevelStr(iname) != 'none':
							for i in authlist:
								
								
								alname = i.nick
								if alname == iname:
									authlist.remove(i)
									found = 1
							if found:
								out = 'PRIVMSG '+channel+' :Deauthenticated'
							else:
								out = 'PRIVMSG '+channel+' :An error has occured'
						else:
							out = 'PRIVMSG '+channel+' :You are not authenticated.'

				# Explicit auth only: register for an account
				if (run == 'register'):
			
					if not(conn.userAuth):
						out = 'PRIVMSG ' + channel + ' :' + config.simpleAuthNotice
					else: 
	
						if (len(cmd) != 3):
							out = 'PRIVMSG ' + channel + ' :Incorrect syntax. Usage: register username password'
						else:
							with open('users', 'r') as f:
								valid = 1
								for line in f:
									linestuff = line.split(' ')
									if cmd[1] == linestuff[0]:
										valid = 0
										out = 'PRIVMSG ' + channel + ' :Account already exists'
								
						if valid == 1:
							with open('users', 'a') as f:
								fileout = cmd[1] + ' HASH:' + sha(cmd[2].encode()).hexdigest() + ' 3\n'
								f.write(fileout)
								out = 'PRIVMSG ' + channel + ' :Registered. You can now authenticate. '
						else:
							out = 'PRIVMSG ' + channel + ' :Account already exists.'
						

				if (run == 'authdump'):
					
					if not(conn.userAuth):
						out = 'PRIVMSG ' + channel + ' :' + config.simpleAuthNotice

					else:
						if getlevel(sender) >= 20:
							
							out = 'PRIVMSG ' + channel + ' :Auth list dumped to console'
							showdbg('Dumping auth list...')
							for i in authlist:
								showdbg(i.nick + '; ' + i.authName + '; ' + str(i.level))
						else:
							out = 'PRIVMSG ' + channel + ' :' + sender + ': ' + config.privrejectadmin 


				if (run == 'authinfo'):
					
					if not(conn.userAuth):
						out = 'PRIVMSG ' + channel + ' :' + config.simpleAuthNotice

					else:
						if getlevel(sender) >= 20:
							authItem = authlist[0]
							out = 'PRIVMSG ' + channel + ' :Auth dump: ' + authItem.nick + '; ' + authItem.authName + '; ' + str(authItem.level) + '; ' + str(len(authlist))
						else:
							out = 'PRIVMSG ' + channel + ' :' + sender + ': ' + config.privrejectadmin 



	

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
					if (getlevel(sender) >= 20):
						showdbg('Restart requested')
						out = 'PRIVMSG ' + channel + ' :Restarting...'
						return {'action': "restart"}
					else:
						out='PRIVMSG ' + channel + ' :' + config.privrejectadmin
				if (run == 'die'):
					if (getlevel(sender) >= 20):
						showdbg('Stop requested')
						out = 'PRIVMSG ' + channel + ' :Stopping...'
						return {'action': "die"}
					else:
						out='PRIVMSG ' + channel + ' :' + config.privrejectadmin
				if (run == 'reload'):
					if (getlevel(sender) >= 20):
						showdbg('Reload requested')

						out = 'PRIVMSG ' + channel + ' :Reloading...'
						return {'action': "reload"}
					else:
						out = 'PRIVMSG ' + channel + ' :' + config.privrejectadmin

				# Generates a dummy error to test error-reporting capabilities. 
				if (run == 'errtest'):
					if (getlevel(sender) >= 20):
						showdbg('Error test requested')
						senddata('PRIVMSG ' + channel + ' :Error generated. Check the console.\n')
						time.sleep(2)
						raise(Exception("User-requested error"))
					else:
						out = 'PRIVMSG ' + channel + ' :' + config.privrejectadmin

				# Modules management
				if (run == 'modules'):
					if (len(cmd) > 1):
						# Reload looks at existing modules and reloads them
						# You can also specify a specific module to reload
						if cmd[1] == 'reload':
							if getlevel(sender) >= config.reqprivlevels['modules']:
								global library_dict
								if len(cmd) == 2:	
									
									errored = []
									for modName in library_dict:
										try:
											if reloadByName(modName):
												pass
											else:
												errored.append(modName)

										except:
											showErr(traceback.format_exc())
											errored.append(modName)
									showdbg('Reloaded all modules')
									out = 'PRIVMSG %s :Reloaded all modules. ' %(channel)
									if errored:
										out += 'The following modules encountered errors: '
										for modName in errored:
											out += modName + ', '
										out = out[:-2] + '. '
								else:
									found = []
									notFound = []
									errored = []
									for modName in cmd[2:]: 
										
										if modName in library_dict:
											
											try: 
												if reloadByName(modName):
													pass
												else:
													errored.append(modName)
												found.append(modName)
												

											except:
												showErr(traceback.format_exc())
												errored.append(modName)

										else:
											notFound.append(modName)
									
									out = 'PRIVMSG %s :' %channel
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
								out = 'PRIVMSG %s :%s' %(channel, config.privrejectgeneric)

						# Rescan essentially redoes the original module scanning process
						# Note that this doesn't necessarily reload a module. 
						if cmd[1] == 'rescan':
							if getlevel(sender) >= config.reqprivlevels['modules']: 
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
								out = 'PRIVMSG %s :Rescanned' %(channel) 
							else: 
								out = 'PRIVMSG %s :%s' %(channel, config.privrejectgeneric)
						# Prints a list of functions or listeners
						if cmd[1] == 'show':
							if len(cmd) == 2:
								out = 'PRIVMSG %s :Currently active modules: ' %(channel)
								for item in library_dict:
									if getattr(library_dict[item], 'enabled', True):
										out += str(item) + ', '
								out = out[:-2]
							
							if len(cmd) == 3:

								if (cmd[2] == 'disabled'):
									out = 'PRIVMSG %s :Currently active modules: ' %(channel)
									for item in library_dict:
										if not(getattr(library_dict[item], 'enabled', True)):
											out += str(item) + ', '
									out = out[:-2]

								if (cmd[2] == 'allmods'):
									out = 'PRIVMSG %s :Currently active modules: ' %(channel)
									for item in library_dict:
										out += str(item) + ', '
									out = out[:-2]	

								if (cmd[2] == 'functions'):
									out = 'PRIVMSG %s :Currently active (non builtin) commands: ' %(channel)
									for item in list(funcregistry):
										
										out += str(item)+', '
									out = out[:-2]
								
								if (cmd[2] == 'listeners'):
									out='PRIVMSG %s :Currently active (non builtin) listeners: ' %(channel)
									for evtype in list(listenerregistry):
										for listener in listenerregistry[evtype]:
											function = listener[1]
											fstr = str(function)
											fstr = fstr.split(' ')[1]
											out += '%s (%s), ' %(fstr, evtype)
									out = out[:-2]

								if (cmd[2] == 'help'):
									out = 'PRIVMSG %s :Currently active (non builtin) help: ' %(channel)
									for item in list(helpregistry):
										out += str(item)+', '
									out = out[:-2]
	
					else:
						out = 'PRIVMSG %s :Wrong number of arguments. Usage: modules action [arguments] ' %(channel)


				# The help system. Essentially a mini version of the command system. 
				if (run == 'help'):
					
			
					if len(cmd) == 1:
						out = 'PRIVMSG ' + channel + ' :' + config.defaulthelp + ' Use help <command> for help on a particular command. To use a command either say ' + options.NICK + ': <command> or ' + options.cmdprefix + 'command.\n'
					else:
						cmd[1] = cmd[1].rstrip()
						handled = 0

						if handled == 1:
							out = 'PRIVMSG ' + channel + ' :' + helpmsg
						else:
							if cmd[1] in helpregistry:
								item = helpregistry[cmd[1]]
								l = item[0]
								
								handled = 1
								target = item[1]
								
								out = target(helpCmd(channel, cmd[1:]))
								if out.find('PRIVMSG') == -1:
									out = 'PRIVMSG ' + channel + ' :' + out


							if handled == 1:
								pass
							else:
								out = 'PRIVMSG ' + channel + ' :Either that command does not exist, or help has not been written.'
			except:
				showErr(traceback.format_exc())

				out = 'PRIVMSG ' + channel + ' :An unspecified error has occurred'
			
			nodata = False
			try: 		
				if out == '(none)':
					nodata = True
			except:
				pass
			if nodata:
				return {}
			
			
			if True:
				if (out):				
					senddata(out + '\n')

			# Try to run a module function since we didn't find an appropriate builtin
				else:
					if run in funcregistry:
						target = funcregistry[run]
						l = target[0]
						# Pass all this stuff in via our msgObj object
						msgObj = cmdMsg(channel, sender, options.NICK, cmd, syscmd, run, senddata, showdbg)
						try: 
							out = target[1](msgObj)
							if (out.split(' ')[0] != 'PRIVMSG'):
								out = 'PRIVMSG %s :%s\n' %(channel, out)
						except:
							showErr(traceback.format_exc())
							


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
						showErr(traceback.format_exc())

		# This function only returns stuff if we need to signal the main loop to exit. 
		return {}

	# main loop
	s.settimeout(5) # This sets the max time to wait for data
	# Note that this will also affect how often periodics are run

	while 1:
		linebuffer = False
		try:
			linebuffer = s.recv(1024).decode()
			if not(linebuffer):
				# Check if there was a socket error. If there was, tell the wrapper that. 
				logdata(time.strftime('---- [ Session closed at %y-%m-%d %H:%M:%S ] ---- (Reason: lost connection)'))
				return 255
	
		
		except socket.error:
			pass

		except:
			pass
		

		while linebuffer and linebuffer[-1] != '\n':
			linebuffer += s.recv(1024).decode()
			

		# If we got no damage from the server, run periodics
		if not(linebuffer):
			type = "periodic"
			if type in listenerregistry:
				for function in listenerregistry[type]:
					l = function[0]
					target = function[1]
					periodicObj = periodic(s, conn, senddata, numlevel, getlevel)
					try:
						target(periodicObj)
					except:
						showErr(traceback.format_exc())
	

				time.sleep(1)

		# What to do if we did get data
		else:
			# If the server dumped a bunch of lines at once, split them
			lines = linebuffer.split('\n')
			while len(lines) > 1:	 
				line = lines[0]		
				lines.pop(0)
				try:
					e = lineEvent(line, s, conn, senddata, getlevel, getlevel)
				except:
					showdbg('Failed basic line parsing! Line: ' + line)
					showErr(traceback.format_exc())
				
					

				dispdata(line)

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
						showErr(traceback.format_exc())
	

				# Respond to pings
				if e.type == 'ping':
					out = 'PONG ' + e.target + '\n'
					senddata(out)

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
								showErr(traceback.format_exc())
	
					# Also run listeners who hook onto 'any'
					if 'any' in listenerregistry:
						for function in listenerregistry['any']:
							l = function[0]
							target = function[1]

							try:
								target(e)
							except:
								showErr(traceback.format_exc())

			
