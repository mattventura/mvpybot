#!/usr/bin/python

enabled = False


def register(r):
	r.registerfunction('testfunc', simpleTestFunc)


def simpleTestFunc(msg):
	return('PRIVMSG %s :This is a simple function\n' % (msg.channel))
