#!/usr/bin/python3


def splitLines(s):
	return s.split('\n')


# Decorator to call a function once for each line in the
# original input
def splitCall(func):
	def inner(self, data, *args, **kwargs):
		lines = splitLines(data)
		for line in lines:
			if len(line) > 0:
				func(self, line, *args, **kwargs)

	return inner
