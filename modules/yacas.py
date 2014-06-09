#!/usr/bin/python

enabled = 1


from subprocess import PIPE,Popen
import time
import os

def register(r):
	r.registerfunction('math', math)

def math(msg):
	# This plugin DOESN'T use our syscmd function, because we
	# want to be able to limit execution time to 3 seconds
	if msg.getlevel(msg.nick) > -1: # Change this to 0 if you want to make people register to use this command
		mathstuff = ' '.join(msg.cmd[1:])
		mathstuff = mathstuff.rstrip()
		echoout = Popen(['echo', mathstuff], stdout = PIPE)
		yacasstuff = Popen(['yacas','-c','-f'], stdin = echoout.stdout, stdout = PIPE)
		status = yacasstuff.poll()
		stime = time.time()
		#print "finished"
		#print yacasstuff.poll()
		while status == None:
			status = yacasstuff.poll()
			ctime = time.time()
			#print 'stime '+str(stime)
			#print 'ctime '+str(ctime)
			if (stime + 3) < ctime:
				os.kill(yacasstuff.pid, 9)
				return 'PRIVMSG ' + channel + ' :Error: maximum time for calculation exceeded.'
		cmdresult = yacasstuff.communicate()[0].decode()
		out = cmdresult.rstrip()
		return(out)
	else:
		return('Please register to use this feature.')

def help_math(cmd):
	return('Yacas math plugin. Enter yacas commands as you would normally do. Execution time of the program is limited to 2 seconds. Usage: math <expression>.' )
