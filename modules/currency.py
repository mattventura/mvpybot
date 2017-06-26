#!/usr/bin/python

enabled = True
timeBetweenFlush = 60
userBalanceList = 'modules/currency.json'

import json
import time
import random

currencyName = "trashcans"


lastFlushTime = time.time()
lastAccumTime = time.time()


accumInterval = 30
balancePerInterval = 1


balanceCache = {}


def register(r):
	global botinst
	botinst = r
	loadBalances()
	r.addlistener('periodic', accumulate)
	r.registerfunction(currencyName, balance)
	r.registerfunction('forceacc', accumulate)
	r.registerfunction('forceflush', flushBalances)
	r.registerfunction('forceload', loadBalances)
	r.registerfunction('gamble', gamble)



def accumulate(e):
	global lastAccumTime
	allUsers = set()
	for channel in e.bot.getChannels():
		for user in e.bot.getUsersInChannel(channel):
			allUsers.add(user)

	fullIntervals = timeSinceAcc() // accumInterval
	adjustmentAmount = int(fullIntervals * balancePerInterval)

	for user in allUsers:
		adjustUserBalance(user, adjustmentAmount)

	lastAccumTime += fullIntervals * accumInterval

	#e.bot.showdbg("Accumulate %s %s %s %s" % (fullIntervals, adjustmentAmount, timeSinceAcc(), allUsers))
	if timeSinceFlush() > 5:
		flushBalances()


def timeSinceAcc():
	return time.time() - lastAccumTime


def balance(e):
	return "%s has %s %s" % (e.nick, getBalanceForUser(e.nick), currencyName)


def gamble(e):
	if len(e.cmd) != 2:
		return 'How to gamble: !gamble <amount>'

	try:
		amount = int(e.cmd[1])
	except:
		return 'How to gamble: !gamble <amount>'

	if amount <= 0:
		return 'How to gamble: !gamble <amount>'
		

	user = e.nick

	curBal = getBalanceForUser(user)
	if amount > curBal:
		return '%s: You only have %s %s, you can\'t gamble that many!' % (user, curBal, currencyName)

	roll = random.randint(0, 100)

	if roll < 60:
		adjustUserBalance(user, amount * -1)
		out = '%s rolled %s and lost %s %s. ' % (user, roll, amount, currencyName)

	elif roll < 90:
		adjustUserBalance(user, amount)
		out = '%s rolled %s and won %s %s. ' % (user, roll, amount, currencyName)

	elif roll < 100:
		winnings = amount * 2
		adjustUserBalance(user, winnings)
		out = '%s rolled %s and won %s %s. ' % (user, roll, winnings, currencyName)
	
	else:
		winnings = amount * 5
		adjustUserBalance(user, winnings)
		out = '%s rolled a perfect 100 and won %s %s. ' % (user, winnings, currencyName)
	
	nbStr = 'Your new balance is %s. ' % getBalanceForUser(user)

	return out + nbStr

	


def loadBalances():
	global balanceCache
	try:
		with open(userBalanceList, 'r') as f:
			balanceCache = json.load(f)
	except IOError:
		r.showErr("Couldn't load balances.")
		r.reportErr(sys.exc_info())
		balanceCache = {}


def flushBalances():
	global lastFlushTime
	with open(userBalanceList, 'w') as f:
		json.dump(balanceCache, f)
	lastFlushTime = time.time()


def timeSinceFlush():
	return time.time() - lastFlushTime


def getBalanceForUser(user):
	try:
		return balanceCache[user]
	except KeyError:
		balanceCache[user] = 0
		return 0


def setBalanceForUser(user, new):
	balanceCache[user] = int(new)


def adjustUserBalance(user, adj):
	old = getBalanceForUser(user)
	new = old + adj
	setBalanceForUser(user, new)
	
