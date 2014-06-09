#!/usr/bin/python

def register(r):
	r.registerfunction('ping', ping)
	r.addhelp('ping', help_ping)

def ping(msg):
	outstuff = ''	
	if (len(msg.cmd) != 3):
		return('PRIVMSG %s :Incorrect usage. Syntax: ping (4|6) <address>.' %(msg.channel))
	else:
		if msg.cmd[1] == '4' or msg.cmd[1] == '6':
			if msg.cmd[1] == '4':
					
				output = msg.syscmd(['ping','-c','5','-i','0.2',msg.cmd[2]])
								
			
			else:

				output = msg.syscmd(['ping6','-c','5','-i','0.2',msg.cmd[2]])
			
			outsplit = output.split('\n')
			outparts = outsplit[-3:-1]
			for part in outparts:
				outstuff += 'PRIVMSG %s :%s\n' %(msg.channel, part)
			return(outstuff)
		else:
			return('PRIVMSG %s :Error: protocol must be either 4 or 6\n' %msg.channel)


def help_ping(cmd):
	return('Pings an internet address. Usage: ping (4|6) <address>. Only displays summary. ' )
