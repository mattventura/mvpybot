#!/usr/bin/python

enabled = 1

import config

def register(r):
	r.registerfunction('modErrTest', modErrTest)

def modErrTest(msg):
	
	if not(msg.hasPriv(msg.nick, 'errors', 20)):
		return config.privrejectadmin

	else:
		raise(Exception('User requested an exception in this module'))
