import classes
import unittest
import newbot

class DummyBot:
	getlevel = object()
	nick = object()
	syscmd = object()
	getlevel = object()
	class conn:
		send = object()
	getLevelStr = object()
	levelToStr = object()
	showdbg = object()
	showErr = object()
	hasPriv = object()


class LineToEventTests(unittest.TestCase):

	def setUp(self):

		self.dummybotinstance = DummyBot()

	def get_line_event(self, line):
		return classes.lineEvent(self.dummybotinstance, line)

	def test_unknown_event_type(self):

		bot = self.dummybotinstance
		line = 'FOO bar baz'
		le = classes.lineEvent(bot, line)
		self.assertIsInstance(le, classes.UnknownEvent)
		self.assertEqual(le.etype, 'bar')

	def test_ping(self):
		bot = self.dummybotinstance
		line = 'PING 12345'
		le = classes.lineEvent(bot, line)
		self.assertIsInstance(le, classes.PingEvent)
		import pdb
		#pdb.set_trace()
		self.assertEqual(le.etype, 'ping')
		self.assertEqual(le.target, '12345')

	def test_error(self):
		bot = self.dummybotinstance
		line = 'ERROR something went wrong'
		le = classes.lineEvent(bot, line)
		self.assertIsInstance(le, classes.ErrorEvent)
		self.assertEqual(le.etype, 'error')
		self.assertEqual(le.linesplit, ['ERROR', 'something', 'went', 'wrong'])

	def test_join(self):
		bot = self.dummybotinstance
		line = ':mvpybot!othername@foo.bar.com JOIN :#channel-test'
		le = classes.lineEvent(bot, line)
		self.assertIsInstance(le, classes.JoinEvent)
		self.assertEqual(le.etype, 'join')
		self.assertEqual(le.nick, 'mvpybot')
		self.assertEqual(le.user, 'othername')
		self.assertEqual(le.host, 'foo.bar.com')
		self.assertEqual(le.channel, '#channel-test')

	def test_part(self):
		bot = self.dummybotinstance
		line = ':mvpybot!othername@foo.bar.com PART :#channel-test'
		le = classes.lineEvent(bot, line)
		self.assertIsInstance(le, classes.PartEvent)
		self.assertEqual(le.etype, 'part')
		self.assertEqual(le.nick, 'mvpybot')
		self.assertEqual(le.user, 'othername')
		self.assertEqual(le.host, 'foo.bar.com')
		self.assertEqual(le.channel, '#channel-test')

	def test_nick(self):
		le = self.get_line_event(':foo!foo@foo.bar.com NICK newname')
		self.assertIsInstance(le, classes.NickEvent)
		self.assertEqual(le.etype, 'nick')
		self.assertEqual(le.newNick, 'newname')

	def test_quit(self):
		le = self.get_line_event(':foo!foo@foo.bar.com QUIT :asdf')
		self.assertIsInstance(le, classes.QuitEvent)
		self.assertEqual(le.etype, 'quit')
		self.assertEqual(le.reason, 'asdf')
		# Same, without leading colons
		le = self.get_line_event('foo!foo@foo.bar.com QUIT asdf')
		self.assertIsInstance(le, classes.QuitEvent)
		self.assertEqual(le.etype, 'quit')
		self.assertEqual(le.reason, 'asdf')

	def test_privmsg(self):
		le = self.get_line_event(':person!person@cool.website.com PRIVMSG #bigchannel :a message  and some  spaces')
		self.assertIsInstance(le, classes.PrivmsgEvent)
		self.assertEqual(le.etype, 'privmsg')
		self.assertEqual(le.channel, '#bigchannel')
		self.assertEqual(le.message, 'a message  and some  spaces')
		self.assertEqual(le.nick, 'person')
		self.assertFalse(le.isPrivate)

	def test_privmsg_private(self):
		le = self.get_line_event(':person!person@cool.website.com PRIVMSG person :a message  and some  spaces')
		self.assertIsInstance(le, classes.PrivmsgEvent)
		self.assertEqual(le.etype, 'privmsg')
		self.assertEqual(le.channel, 'person')
		self.assertEqual(le.message, 'a message  and some  spaces')
		self.assertEqual(le.nick, 'person')
		self.assertTrue(le.isPrivate)
