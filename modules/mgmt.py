#!/usr/bin/python3

# Moving some more basic commands out of the main bot
import config

def register(r):
	r.registerfunction('part', partFunc)
	r.registerfunction('join', joinFunc)
	r.registerfunction('dcd', dcdFunc)


def partFunc(msg):
	if msg.hasPriv(msg.nick, 'chanMgmt', 20):
		channel = msg.cmd[1]
		msg.conn.partChannel(channel)
		return('Left channel %s' %channel)
	else:
		return('%s: %s' %(msg.nick, config.privrejectadmin))

def joinFunc(msg):
	if msg.hasPriv(msg.nick, 'chanMgmt', 20):
		channel = msg.cmd[1]
		msg.conn.joinChannel(channel)
		return('Joined channel %s' %channel)
	else:
		return('%s: %s' %(msg.nick, config.privrejectadmin))
		

def dcdFunc(e):
	cm = e.bot.chanMap
	for entry in cm.values():
		out = 'Members of %s: %s' % (entry.chanName, ', '.join(map(str, entry.userMap.values())))
		e.showdbg(out)
	return 'Dumped'
