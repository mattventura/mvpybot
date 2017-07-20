#!/usr/bin/python3

enabled = False


def register(r):
	r.registerfunction("mynewfunc", newfunction)


def newfunction():
	"""
	Example of a very basic function
	"""
	return "Hello"
