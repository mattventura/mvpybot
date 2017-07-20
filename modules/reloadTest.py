#!/usr/bin/python3

# Deprecated file for testing

enabled = False


def register(r):
	print('I am being registered')
	r.addlistener('privmsg', reloadTestLs)


def reloadTestLs(e):
	e.showdbg('Testing this module')
