#!/usr/bin/python3

enabled = 1
import options
import time

def register(r):
	r.addlistener('join', joinalerts)
	

def joinalerts(e):

	alerts = {"nick_goes_here" : "Attention: nick_goes_here has entered the channel!" }

	#print 'Running'
	#print lineparts
	#print lineparts[1]
	#print lineparts[0].split('!')[0][1:]
	for i in alerts:
		if i.lower() == e.nick.lower():
			senddata('PRIVMSG %s :%s\n' %(e.channel, alerts[i]))
	

