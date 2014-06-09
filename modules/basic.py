#!/usr/bin/python

# Moving some of the basic commands from the bot coree to here
import config

def register(r):
	r.registerfunction('say', say)
	r.registerfunction('raw', raw)
	r.registerfunction('uptime', uptime)
	r.registerfunction('hostname', hostname)
	r.registerfunction('free', free)
	r.registerfunction('echo', echo)

	r.addhelp('echo', help_echo)
	r.addhelp('free', help_free)
	r.addhelp('uptime', help_uptime)
	r.addhelp('say', help_say)
	r.addhelp('hostname', help_hostname)
	r.addhelp('raw', help_raw)





def say(msg):
	if msg.getlevel(msg.nick) >= 20:
		return('PRIVMSG %s :%s' %(msg.cmd[1], ' '.join(msg.cmd[2:])))
	else:
		return('PRIVMSG %s :%s: %s' %(msg.channel, msg.sender, config.privrejectadmin))

def raw(msg):
	if msg.getlevel(msg.nick) >= 20:
		return(' '.join(msg.cmd[1:]))
	else:
		return('PRIVMSG %s :%s: %s' %(msg.channel, msg.sender, config.privrejectadmin))
	

def uptime(msg):
	return('PRIVMSG $s :Uptime is %' %(msg.channel, msg.syscmd('uptime')))
	
def hostname(msg):
	return('PRIVMSG $s :Hostname is %' %(msg.channel, msg.syscmd('hostname')))
	
def free(msg):
	cmdresult = msg.syscmd('free')
	out = ''
	for line in cmdresult.split('\n')[:-1]:
		outadd = 'PRIVMSG %s :%s\n' %(msg.channel, line)
		out += outadd
	return(out)

def echo(msg):
	reply = ' '.join(msg.cmd[1:])
	return('PRIVMSG %s :%s: %s' %(msg.channel, msg.nick, reply))

def help_echo():
	return fmt('Echoes text back to the sender. Usage: echo <text>.')

def help_raw():
	return fmt('Send raw IRC commands to the server. Usage: raw <command>')

def help_uptime():
	return fmt('Display the server\'s uptime. ')

def help_say():
	return fmt('Say something in a channel. Usage: say #channel Message. ')

def help_free():
	return fmt('Display server\'s memory statistics.')

def help_hostname():
	return fmt('Display server\'s hostname.')


