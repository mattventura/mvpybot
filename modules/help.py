#!/usr/bin/python

#In an attempt to slim down the main executable, I have moved
#all the help texts to this file.

enabled = 1

def register(r):
	r.addhelp('join', help_join)
	r.addhelp('part', help_part)
	r.addhelp('user', help_user)
	r.addhelp('auth', help_auth)
	r.addhelp('authenticate', help_authenticate)
	r.addhelp('level', help_level)
	r.addhelp('deauth', help_deauth)
	r.addhelp('register', help_register)
	r.addhelp('modules', help_modules)
	r.addhelp('reload', help_reload)
	r.addhelp('pass', help_pass)
	r.addhelp('passwd', help_passwd)

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

help_authenticate = help_auth

def help_level(cmd):
	return fmt('Find your user level. This command takes no arguments. ')

def help_deauth(cmd):
	return fmt('De-authenticate yourself. This command takes no arguments. ')

def help_register(cmd):
	return fmt('Register a new account. Usage: register <username> <password>. ')

def help_modules(cmd):
	return fmt('Shows currently loaded modules. Modules that are loaded but disabled will still be shown.' )

def help_reload(cmd):
	return fmt('Reloads a module. Usage: reload <module>. ')

def help_pass(cmd):
	return fmt('Change your own password. Usage: pass <password>. ')

def help_passwd(cmd):
	return fmt('''Change an arbitrary user's password. Usage: pass <username> <password>. ''')


