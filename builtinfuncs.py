import sys
import config
# Account management. 
# Supports querying and modifying levels and passwords, as well as adding
# new users. 
# TODO: Split the granting/denying logic here into separate functions
def userMgmtFunc(self, msg):
	
	if not(self.hasPriv(msg.nick, 'acctMgmt', 20)):
		return(config.privrejectgeneric)
	
	if len(msg.cmd) == 1:
		return('''This function requires more arguments. See 'help user' for details.''')

	# Make a copy since we'll be changing this
	args = msg.cmd[1:]
	argsFull = args # Just in case

	# First part: -u for user or -n for nick
	# -n can only work when the user is logged in
	# -u should be able to work any timet
	if args[0][0:2] == '-u':
		user = True
	elif args[0][0:2] == '-n':
		user = False
	else:
		return('''Incorrect syntax. See 'help user' for details. ''')
	
	if len(args[0]) > 2:
		name = args[0][2:]
		args = args[1:]
	else:
		name = args[1]
		args = args[2:]

	if len(args) < 1:
		return('''This function requires more arguments. See 'help user' for details.''')
		
	# Actions: level, privs/priv
	if args[0] == 'level':
		action = 0
		args = args[1:]
	elif args[0] == 'privs' or args[0] == 'priv':
		action = 1
		args = args[1:]
	elif args[0] == 'add':
		action = 2
	else:
		return('''Action must be 'add', 'level' or 'privs'.''')


	if action == 0:
		if len(args) == 0:
			return('Not enough arguments.')
		elif args[0] == 'get':
			if user:
				try:
					authEntry = userLookup(name)
				except UserNotFound:
					return('That user was not found')
				level = authEntry.level
				return('User %s is level %s' %(name, str(level)))
			else:	
				try:
					authEntry = self.getAuth(name)
				except UserNotFound:
					return('That user was not found')
				level = authEntry.level
				return('User %s is level %s' %(name, str(level)))

		elif args[0] == 'set':
			try:
				newLevel = int(args[1])
			except:
				return('Level must be an integer.')
			if user:
				try:
					chgUserLvl(name, newLevel)
				except UserNotFound:
					return('User not found')
				return('''Changed level for user '%s' to %s. ''' %(name, str(newLevel)))

			else:
				try:
					authEntry = self.getAuth(name)
				except UserNotFound:
					return('User not found.')

				authEntry.level = newLevel

				try:
					chgUserLvl(authEntry.authName, newLevel)
				except:
					return('''Changed level for user, but couldn't update file.''')

				return('''Changed level for nick '%s' to %s. ''' %(name, str(newLevel)))

		else:
			return('''Action must be 'get' or 'set'.''')
					
				
	if action == 1:
		if len(args) == 0:
			return('Not enough arguments.')		
		elif args[0] == 'get':
			try:
				if user:
					authEntry = userLookup(name)

				else:
					authEntry = self.getAuth(name)
			except UserNotFound:
				return('User not found.')

			return('User %s has privileges: %s. ' %(name, formatPerms(authEntry.grant, authEntry.deny, ', ')))


		if args[0] == 'clear':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except UserNotFound:
						return('User not found.')
					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						elif i in deny:
							deny.remove(i)
					try:
						chgUserPrivs(name, grant, deny)
					except UserNotFound:
						return('User was found initially, but not when updating.')
					return('Cleared privilege(s) from user %s.' %name)

				else:
					try:
						authEntry = self.getAuth(name)
					except UserNotFound:
						return('User not found.')
						

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						elif i in deny:
							deny.remove(i)

					try:
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Cleared privilege(s), but could not update file.')
						
					return('''Cleared privilege(s) for nick '%s'.''' %name)
							

					
			else:
				if user:
					try:
						chgUserPrivs(name, set(), set())
					except UserNotFound:
						return('User not found.')

					return('Cleared special privileges for user %s.' %name)

				else:
					try:
						authEntry = self.getAuth(name)
					except UserNotFound:
						return('Could not find that nick.')
						
					authEntry.grant = set()
					authEntry.deny = set()
					try:
						chgUserPrivs(authEntry.authName, set(), set())
					except UserNotFound:
						return('Cleared special privileges for nick, but could not update file.')
					return('Cleared special privileges for nick %s.' %name)

		if args[0] == 'grant':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except UserNotFound:
						return('User not found.')
						
					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in deny:
							deny.remove(i)
						grant.add(i)
					try: 
						chgUserPrivs(name, grant, deny)
					except UserNotFound:
						return('User was found initially but not while updating')
					return('Changed privilege(s) for user %s.' %name)
				else:
					try:
						authEntry = self.getAuth(name)
					except UserNotFound:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in deny:
							deny.remove(i)
						grant.add(i)

					try: 
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Changed privileges, but could not update file.')
					return('''Changed privileges for nick '%s'.''' %name)

			else:				
				return('Not enough arguments.')
	
		if args[0] == 'deny':
			
			if args[1:]:
				if user:
					try:
						authEntry = userLookup(name)
					except:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						deny.add(i)
					try:
						chgUserPrivs(name, grant, deny)
					except:
						Raise(Exception('User was found initially, but not when updating.'))

					return('Changed privilege(s) for user %s.' %name)
				else:
					try:
						authEntry = self.getAuth(name)
					except UserNotFound:
						return('User not found.')

					grant = authEntry.grant
					deny = authEntry.deny
					for i in args[1:]:
						if i in grant:
							grant.remove(i)
						deny.add(i)

					try:
						chgUserPrivs(authEntry.authName, grant, deny)
					except UserNotFound:
						return('Changed privileges, but could not update file.')
					
					return('''Changed privileges for nick '%s'.''' %name)

			else:				
				return('Not enough arguments.')

	if action == 2:
		if conn.userAuth:
			return('To add users in explicit auth mode, user the register command.')
		else:
			try:
				addUser(name)
			except UserAlreadyExistsError:
				return('Error: User already exists')
			return('Added user %s' %name)
			

# Module management function
def modFunc(self, msg):
	
	global listenerregistry
	global helpregistry
	global funcregistry
	global library_dict

	if (len(msg.cmd) > 1):
		# Reload looks at existing modules and reloads them
		# You can also specify a specific module to reload
		if msg.cmd[1] == 'reload':
			if self.hasPriv(msg.nick, 'modules', 20):
				# User did not specify which module(s) to reload, so reload them all
				if len(msg.cmd) == 2:
					
					errored = []
					for modName in self.library_dict:
						try:
							if self.reloadByName(modName):
								pass
							else:
								# If the reload was unsuccessful, report it. 
								errored.append(modName)

						except:
							# Put it on the error stack so we can actually see what went wrong 
							self.reportErr(sys.exc_info())
							errored.append(modName)
					self.showdbg('Reloaded all modules')
					out = 'PRIVMSG %s :Reloaded all modules. ' %(msg.channel)
					# Tell the user about errors
					if errored:
						out += 'The following modules encountered errors: '
						for modName in errored:
							out += modName + ', '
						out = out[:-2] + '. '
				else:
					found = []
					notFound = []
					errored = []
					# If the user specifies moduels to reload, look for just those 
					# specific modules and reload them. 
					for modName in msg.cmd[2:]: 
						
						if modName in self.library_dict:
							
							try: 
								if self.reloadByName(modName):
									pass
								else:
									errored.append(modName)
								found.append(modName)
								

							except:
								self.reportErr(sys.exc_info())
								errored.append(modName)

						# If the module could not be found, keep track of that. 
						else:
							notFound.append(modName)
					
					# Tell the user which were successful, which were not found, 
					# and which encountered errors. 
					out = 'PRIVMSG %s :' %msg.channel
					if found:
						out += 'Successfully reloaded: '
						for modName in found:
							out += modName + ', '
						out = out[:-2] + '. '

					if notFound:
						out += 'Could not find: '
						for modName in notFound:
							out += modName + ', '
						out = out[:-2] + '. '
					
					if errored:
						out += 'Encountered errors with: '
						for modName in errored:
							out += modName + ', '
						out = out[:-2] + '. '

			else: 
				out = 'PRIVMSG %s :%s' %(msg.channel, config.privrejectgeneric)

		# Rescan essentially redoes the original module scanning process
		# Note that this doesn't necessarily reload a module. 
		# If you add or remove a module, you will need to rescan. 
		# If you change a module, you will need to reload. 
		elif msg.cmd[1] == 'rescan':
			if self.hasPriv(msg.nick, 'modules', 20):
				showdbg('Rescan requested')
				# Clear out old registries
				self.funcregistry = {}
				self.listenerregistry = {}
				self.helpregistry = {}
				self.library_list = []
				self.library_dict = {}
				for f in os.listdir(os.path.abspath("modules")):
					pname, fileext = os.path.splitext(f)
					if fileext == '.py':
						module = __import__(pname)
						library_list.append(module)
						library_dict[pname] = module
						if hasattr(module,'register') and getattr(module, 'enabled', 1):
							r = self
							getattr(module, 'register')(r)
				self.showdbg('Rescan complete')
				# Success (hopefully)
				out = 'PRIVMSG %s :Rescanned' %(msg.channel) 
			else: 
				out = 'PRIVMSG %s :%s' %(msg.channel, config.privrejectgeneric)
		# Prints a list of functions or listeners
		elif msg.cmd[1] == 'show':
			if not(self.hasPriv(msg.nick, 'showmods', 3)):
				return(config.privrejectgeneric)
			# If no criteria specified, print enabled/active modules. 
			if len(msg.cmd) == 2:
				out = 'PRIVMSG %s :Currently active modules: ' %(msg.channel)
				for item in self.library_dict:
					if getattr(self.library_dict[item], 'enabled', True):
						out += str(item) + ', '
				out = out[:-2]
			
			if len(msg.cmd) == 3:

				# Request to see disabled addons
				if (msg.cmd[2] == 'disabled'):
					out = 'PRIVMSG %s :Currently inactive modules: ' %(msg.channel)
					activemods = [name for name, mod in self.library_dict.items()\
					              if not getattr(mod, 'enabled', True)]
					out += ', '.join(activemods)

				# Request to see all mods, regardless of status
				if (msg.cmd[2] == 'allmods'):
					out = 'PRIVMSG %s :All mods: ' %(msg.channel)
					out += ', '.join(self.library_dict.keys())

				# See functions, by the name that the user actually uses to call them. 
				if (msg.cmd[2] == 'functions'):
					out = 'PRIVMSG %s :Currently active (non builtin) commands: ' %(msg.channel)
					out += ', '.join(self.funcregistry.keys())
				
				# See listeners, including the type of event it listens for
				if (msg.cmd[2] == 'listeners'):
					out = 'PRIVMSG %s :Currently active (non builtin) listeners: ' %(msg.channel)
					items = []
					for evtype, listeners in self.listenerregistry.items():
						for listener in listeners:
							function = listener[1]
							fstr = str(function)
							fstr = fstr.split(' ')[1]
							items.append('%s (%s)' %(fstr, evtype))
					out += ', '.join(items)

				# See custom help texts
				if (msg.cmd[2] == 'help'):
					out = 'PRIVMSG %s :Currently active (non builtin) help: ' %(msg.channel)
					out += ', '.join(helpregistry)

		else:
			out = 'Not a valid argument'


	else:
		out = 'PRIVMSG %s :Wrong number of arguments. Usage: modules action [arguments] ' %(msg.channel)

	return(out)
