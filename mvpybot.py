#!/usr/bin/python3

# New launcher for bot

import options
import config
import sys
import socket
import builtins
from imp import reload

global NICK

if len(sys.argv) >= 2:

	conn = options.connections[int(sys.argv[1])]
else:
	conn = options.connections[0]
	


host = conn.host
port = conn.port

builtins.host = host

builtins.errors = []


#cspass = conn.csp

#channels = conn.chans

# Connect the socket
#s = socket.socket() 
#s.connect((host, int(port)))

#initconn = 1

import newbot

connInst = conn

def mainloop():
	while True:


		botstatus = newbot.botmain(connInst)
		# Die
		if botstatus == 0:
			return 0
		# Restart
		if botstatus == 1:
			initconn = 0
		# Error
		if botstatus == 255:
			return 1
		# Reload
		if botstatus == 2:
			initconn = 0
			reload(newbot)



initconn = 1
mainloop()
