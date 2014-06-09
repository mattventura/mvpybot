#!/usr/bin/python

enabled = 0

import random

quoteFilePath = 'modules/quotesList'

def register(r):
	r.registerfunction('quote', quote)
	r.addhelp('quote', help_quote)

def quote(msg):
	if (len(msg.cmd) == 1):
		return('PRIVMSG %s :%s\n' %(msg.channel, randomQuote()))
	elif (len(msg.cmd) == 2):
		try: 
			num = int(msg.cmd[1])
			return('PRIVMSG %s :%s\n' %(msg.channel, getQuote(num)))
		except:
			return('PRIVMSG %s :Syntax error. Usage: quote <number>.\n' %msg.channel)
	elif msg.cmd[1] == 'add':
		if cmd[2][0] == '.':
			return('PRIVMSG %s :The quote cannot start with a period.' %msg.channel)
		else:
			return('PRIVMSG %s :%s\n' %(msg.channel, addQuote(' '.join(msg.cmd[2:]))))
	else:
		return('PRIVMSG %s :Syntax error. See help for usage info.\n' %msg.channel)

def addQuote(q):
	try:
		with open(quoteFilePath, 'a') as f:
			f.write(q + '\n')
			return('Added quote.')
	except IOError:
		return('Error writing quote to file.')

def getQuote(i):
	try:
		with open(quoteFilePath, 'r') as f:
			lines = f.readlines()
			if len(lines) == 0:
				return('No quotes in database.')
			else:
				try: 
					return(lines[i])
				except IndexError:
					return('Invalid quote ID')
	except IOError:
		return('Error opening quotes file.')

def randomQuote():
	try:
		with open(quoteFilePath, 'r') as f:
			lines = f.readlines()
			if len(lines) == 0:
				return('No quotes in database.')
			else:
				try: 
					return(lines[random.randint(0, len(lines) - 1)])
				except IndexError:
					return('Invalid quote ID')
	except IOError:
		return('Error opening quotes file.')

	
		

		


def help_quote(cmd):
	return('Quotations db. Usage: quote; quote <number>; quote add <quote>.')
