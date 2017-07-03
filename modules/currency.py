#!/usr/bin/python

enabled = False
timeBetweenFlush = 60
default_accumInterval = 30
default_balancePerInterval = 1
userBalanceList = 'modules/currency_data/%s.json'
channelConfig = {
    '#mainchannel': {'name': 'dollars', 'perInterval': 5},
    '#alias': {'shared': '#mainchannel'},
    '#otherchannel': {'name': 'donuts'}
}


import json
import time
import random
import sys


channelObjects = {}


def register(r):
    for configItem in channelConfig.items():
        addChannelConfig(r, configItem)

    r.addlistener('periodic', accumulateAll)
    for chanObj in channelObjects.values():
        # Messy, should point to specific channel method
        r.registerfunction(chanObj.currencyName, balance)

    r.registerfunction('forceacc', accumulateAll)
    #r.registerfunction('forceflush', flushBalances)
    #r.registerfunction('forceload', loadBalances)
    r.registerfunction('gamble', gamble)


def accumulateAll(e):
    for chanObj in channelObjects.values():
        chanObj.accumulate()


def addChannelConfig(botinst, configTuple):

    channelName, config = configTuple
    try:
        aliasOf = config['shared']
    except KeyError:
        pass
    else:
        try:
            aliasedChannel = channelObjects[aliasOf]
            aliasedChannel.addAlias(channelName)
            channelObjects[channelName] = aliasedChannel
            return
        except KeyError:
            raise Exception("Error adding alias for channel %s. Check that the channel you are trying to alias is already configured." % channelName)

    channelObjects[channelName] = ChannelCurrency(botinst, channelName, **config)

class ChannelCurrency:

    def __init__(self, botinst, channel, name, accumInterval=default_accumInterval, perInterval=default_balancePerInterval, filepath=None):
        self.botinst = botinst
        self.channel = channel
        self.currencyName = name
        self.accumInterval = accumInterval
        self.perInterval = perInterval
        if filepath is None:
            self.filepath = userBalanceList % channel
        else:
            self.filepath = filepath
        self.lastAccumTime = time.time()
        self.lastFlushTime = time.time()
        self.aliases = []
        self.loadBalances()
        
    def addAlias(self, newAlias):
        self.aliases.append(newAlias)

    def accumulate(self):
        allusers = set(self.botinst.getUsersInChannel(self.channel))
        for channel in self.aliases:
            for user in self.botinst.getUsersInChannel(channel):
                allusers.add(user)

        fullIntervals = self.timeSinceAcc() // self.accumInterval
        adjustmentAmount = int(fullIntervals * self.perInterval)

        for user in allusers:
            self.adjustUserBalance(user, adjustmentAmount)

        self.lastAccumTime += fullIntervals * self.accumInterval
        if self.timeSinceFlush() > timeBetweenFlush:
            self.flushBalances()

    def timeSinceAcc(self):
        return time.time() - self.lastAccumTime

    def loadBalances(self):
        try:
            with open(self.filepath, 'r') as f:
                self.balanceCache = json.load(f)
        except IOError:
            self.botinst.showErr("Couldn't load balances.")
            self.botinst.reportErr(sys.exc_info())
            self.balanceCache = {}

    def flushBalances(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.balanceCache, f)
        self.lastFlushTime = time.time()

    def timeSinceFlush(self):
        return time.time() - self.lastFlushTime

    def getBalanceForUser(self, user):
        try:
            return self.balanceCache[user]
        except KeyError:
            self.balanceCache[user] = 0
            return 0

    def setBalanceForUser(self, user, new):
        self.balanceCache[user] = int(new)

    def adjustUserBalance(self, user, adj):
        old = self.getBalanceForUser(user)
        new = old + adj
        self.setBalanceForUser(user, new)
        

    def __del__(self):
        self.flushBalances()
#e.bot.showdbg("Accumulate %s %s %s %s" % (fullIntervals, adjustmentAmount, timeSinceAcc(), allUsers))


def getChanObjForMsg(e):
    return channelObjects[e.channel]


def balance(e):
    try:
        channel = getChanObjForMsg(e)
    except KeyError:
        return "This channel does not have currency"
    else:
        return "%s has %s %s" % (e.nick, channel.getBalanceForUser(e.nick), channel.currencyName)


def gamble(e):

    try:
        channel = getChanObjForMsg(e)
    except KeyError:
        return "This channel does not have currency"

    if len(e.cmd) != 2:
        return 'How to gamble: !gamble <amount>'

    try:
        amount = int(e.cmd[1])
    except:
        return 'How to gamble: !gamble <amount>'

    if amount <= 0:
        return 'How to gamble: !gamble <amount>'
        

    user = e.nick

    curBal = channel.getBalanceForUser(user)
    if amount > curBal:
        return '%s: You only have %s %s, you can\'t gamble that many!' % (user, curBal, channel.currencyName)

    roll = random.randint(0, 100)

    if roll < 60:
        channel.adjustUserBalance(user, amount * -1)
        out = '%s rolled %s and lost %s %s. ' % (user, roll, amount, channel.currencyName)

    elif roll < 90:
        channel.adjustUserBalance(user, amount)
        out = '%s rolled %s and won %s %s. ' % (user, roll, amount, channel.currencyName)

    elif roll < 100:
        winnings = amount * 2
        channel.adjustUserBalance(user, winnings)
        out = '%s rolled %s and won %s %s. ' % (user, roll, winnings, channel.currencyName)
    
    else:
        winnings = amount * 5
        channel.adjustUserBalance(user, winnings)
        out = '%s rolled a perfect 100 and won %s %s. ' % (user, winnings, channel.currencyName)
    
    nbStr = 'Your new balance is %s. ' % channel.getBalanceForUser(user)

    return out + nbStr

    


