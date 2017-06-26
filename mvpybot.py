#!/usr/bin/python3

# New launcher for bot

import options
import config
import sys
import socket
#import builtins
import sharedstate
from imp import reload

global NICK

if len(sys.argv) >= 2:
	conn = options.connections[int(sys.argv[1])]
else:
	conn = options.connections[0]

host = conn.host
port = conn.port

sharedstate.host = host

sharedstate.errors = []


import newbot

connInst = conn


def mainloop():

	while True:

		bot = newbot.Bot(connInst)
		botstatus = bot.BotMain(conn)
		# Die
		if botstatus == 0:
			return 0
		# Restart
		if botstatus == 1:
			pass
		# Error
		if botstatus == 255:
			return 1
		# Reload
		if botstatus == 2:
			import builtinfuncs
			reload(builtinfuncs)
			import classes
			reload(classes)
			reload(newbot)


mainloop()
