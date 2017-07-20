#!/usr/bin/python3

enabled = True

from modules.joinalerts_config import alerts as raw_alerts

import options
import time

alerts = {k.lower(): v for k, v in raw_alerts.items()}


def register(r):
	r.addlistener('join', joinalerts)


def joinalerts(e):

	try:
		alert = alerts[e.nick.lower()]
	except KeyError:
		# No alert for this person
		return
	else:
		e.conn.privmsg(e.channel, alert)
