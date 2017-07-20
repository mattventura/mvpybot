#!/usr/bin/python3


def register(r):
	r.registerfunction('mylevel', mylevel)


def mylevel(e):
	return("PRIVMSG " + e.channel + " :" + e.nick + ": Your level is " + e.getLevelStr(e.nick) + '\n')
