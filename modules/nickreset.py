#!/usr/bin/python3

# This is a nick protection plugin. 
# The bot may or may not react well to having its nick forcibly changed, 
# so this module changes it back if that happens. 
# Keep in mind that if a server/net admin changed the bot's name, 
# it was probably for a reason. 

enabled = 0
import options
import builtins
import time

def register(r):
	r.addlistener('nick', resetnick)
	

def resetnick(e):
		if e.nick == builtinss.NICK:
		#print 'Resetting nick'
			send('NICK %s\n' %(builtins.NICK))

