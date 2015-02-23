#!/usr/bin/python3

enabled = 0

def register(r):
	r.registerfunction("mynewfunc", newfunction)



def newfunction():
	return "PRIVMSG #bots :Hello"
