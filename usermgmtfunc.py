# Account management. 
# Supports querying and modifying levels and passwords, as well as adding
# new users. 
# TODO: Split the granting/denying logic here into separate functions
def userMgmtFunc(self, msg):
	
	if not(hasPriv(msg.nick, 'acctMgmt', 20)):
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
					authEntry = getAuth(name)
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
					authEntry = getAuth(name)
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
					authEntry = getAuth(name)
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
						authEntry = getAuth(name)
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
						authEntry = getAuth(name)
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
						authEntry = getAuth(name)
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
						authEntry = getAuth(name)
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
			

