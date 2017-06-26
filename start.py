#!/usr/bin/python3


import time


import options
import os

from subprocess import PIPE,Popen

proclist = []

for servernum in range(len(options.connections)):
	proclist.append([Popen(['./mvpybot.py',str(servernum)]),servernum])

try:
	while True:
		pass
		time.sleep(1);
		for n in range(0,len(proclist)):
			#print "n="+str(n)
			#print proclist[n][0].poll()
			if proclist[n][0].poll() != None:
				#print "Poll true"
				servernum = proclist[n][1]
				proclist.pop(n)
				time.sleep(5)
				proclist.append([Popen(['./mvpybot.py',str(servernum)]),servernum])

except KeyboardInterrupt:
	for process in proclist:
		os.kill(process[0].pid,9)
