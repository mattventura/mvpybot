#!/usr/bin/python3

# Contains help text for many builtin commands

enabled = True


def register(r):
	r.addhelp('join', help_join)
	r.addhelp('part', help_part)
	r.addhelp('user', help_user)
	r.addhelp('auth', help_auth)
	r.addhelp('authenticate', help_auth)
	r.addhelp('level', help_level)
	r.addhelp('deauth', help_deauth)
	r.addhelp('register', help_register)
	r.addhelp('modules', help_modules)
	r.addhelp('reload', help_reload)
	r.addhelp('pass', help_pass)
	r.addhelp('passwd', help_passwd)
	r.addhelp('errtest', help_errtest)
	r.addhelp('err', help_err)
	r.addhelp('user', help_user)
	r.addhelp('perm', help_user)


def fmt(text):
	return(text)


def help_join(cmd):
	return fmt('The bot will join the specified channel. Usage: join #channel')


def help_part(cmd):
	return fmt('The bot will part the specified channel. Usage: part #channel')


def help_user(cmd):
	return fmt('Look up a user\'s information. Usage: user <username>. ')


def help_auth(cmd):
	return fmt('Authenticate using your username and password. Usage: auth <username> <password>. ')


def help_level(cmd):
	return fmt('Find your user level. This command takes no arguments. ')


def help_deauth(cmd):
	return fmt('De-authenticate yourself. This command takes no arguments. ')


def help_register(cmd):
	return fmt('Register a new account. Usage: register <username> <password>. ')


def help_modules(cmd):

	if len(cmd.cmd) == 1:
		return('Shows/manages modules. Usage: modules (show|reload|rescan). See the help texts for each command for more info.')

	else:
		if cmd.cmd[1] == 'show':
			return("Shows loaded modules. By default, shows enabled modules. Use 'allmods' to see all. Usage: modules show [allmods|disabled|functions|listeners|help].")
		elif cmd.cmd[1] == 'reload':
			return('Reloads all modules or specific modules. Usage: modules reload [mod1] [mod2] ...')
		elif cmd.cmd[1] == 'rescan':
			return('Rescans the module directory. This is needed to get newly installed modules to work without fully restarting the bot. Usage: modules rescan')
		else:
			return('Unrecognized argument. Usage: help modules (show|reload|rescan).')


def help_errtest(cmd):
	return('''Generates an exception to test the bot's error reporting capabilities.''')


def help_err(cmd):
	return('Displays or lists errors. With no arguments, displays stored error count. Usage: err [last|list|n] where n is an integer.')


def help_user(cmd):

	if len(cmd.cmd) == 1:
		return('''Manages users. Usage: user (-n|-u) <name> <action> [argument1] ...  -n selects a nickname, -u selects a username. See 'help user (priv|level|add)' for more info''')  # NOQA
	else:
		if cmd.cmd[1] == 'level':
			return('''Manages a user's level. Usage: 'level get' or 'level set <n>'. ''')
		elif cmd.cmd[1] == 'add':
			return('''Adds an implicit user. Usage: 'add <nickname>'. ''')
		elif cmd.cmd[1] == 'priv':
			return('''Manages special privileges. Usage 'priv get'|'priv clear'|'priv clear [privileges]'|'priv (grant deny) <privileges>'.''')
		else:
			return('Unrecognized argument. Usage: help user (level|add|priv)')


def help_reload(cmd):
	return fmt('Reloads a module. Usage: reload <module>. ')


def help_pass(cmd):
	return fmt('Change your own password. Usage: pass <password>. ')


def help_passwd(cmd):
	return fmt('''Change an arbitrary user's password. Usage: pass <username> <password>. ''')
