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

def fmt(text):
	return(text)

def help_join():
	return fmt('The bot will join the specified channel. Usage: join #channel')

def help_part():
	return fmt('The bot will part the specified channel. Usage: part #channel')



def help_user():
	return fmt('Look up a user\'s information. Usage: user <username>. ')

def help_auth():
	return fmt('Authenticate using your username and password. Usage: auth <username> <password>. ')

help_authenticate = help_auth

def help_level():
	return fmt('Find your user level. This command takes no arguments. ')

def help_deauth():
	return fmt('De-authenticate yourself. This command takes no arguments. ')

def help_register():
	return fmt('Register a new account. Usage: register <username> <password>. ')

def help_modules():
	return fmt('Shows currently loaded modules. Modules that are loaded but disabled will still be shown.' )

def help_reload():
	return fmt('Reloads a module. Usage: reload <module>. ')

