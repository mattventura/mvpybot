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


cspass = conn.csp

channels = conn.chans

# Connect the socket
s = socket.socket() 
s.connect((host, int(port)))

initconn = 1

import newbot



def mainloop():
	while True:
		try:
			initconn
		except:
			initconn = 1

		botstatus = newbot.botmain(s, conn, initconn)
		if botstatus == 0:
			return 0
		if botstatus == 1:
			initconn = 0
		if botstatus == 255:
			return 1
		if botstatus == 2:
			initconn = 0
			reload(newbot)



initconn = 1
mainloop()
