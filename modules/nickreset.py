#!/usr/bin/python3

enabled = False


import options
import time


def register(r):
	r.addlistener('nick', resetnick)


def resetnick(e):
		# If the nick of the person whose nick is being changed
		# matches ours, reset it.
		if e.nick == options.NICK:
			send('NICK %s\n' % (options.NICK))
