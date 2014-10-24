#!/bin/env python
#
# Script to make PyGLoo, the pure python runtime GL function-loader.
# Interaction with ctypes is necessary to use loaded functions.
# Currently for Windows and Linux.
#
# In unix land, the up-to-date GL api specification can be obtained by
# svn co --username anonymous --password anonymous https://cvs.khronos.org/svn/repos/ogl/trunk/doc/registry/public/api/ api
#
# Designed to circumvent Maya being shit.
#
# Title: PyGLoo (Python + GLEW, but unrelated to GLEW itself)
#
# @author Ben Allen
#

#
# WARNING: using lxml or html5lib with bs4 can break things
#

import os
from bs4 import BeautifulSoup

# main version number
version = '0.0.0'

# parse the api specification
soup = BeautifulSoup(open('./api/gl.xml'))

# open output file
out = open('./pygloo.py', 'w')

# generic part
header = '''
#
# PyGLoo
#
# Python GL runtime function loader
# Interaction with ctypes is necessary to use loaded functions.
# Currently for Windows and Linux.
#
# Designed to circumvent Maya being shit.
#
# Title: PyGLoo (Python + GLEW, but unrelated to GLEW itself)
#
# @author Ben Allen
#

import os
import platform
import ctypes

__version__ = ''' + repr(version) + '''

# class to contain the loaded function pointers
class Context(object):
	pass
# }

print 'PyGLoo: initializing GL library...'

# function for making functions
if os.name == 'nt':
	FUNCTYPE = ctypes.WINFUNCTYPE
	print 'PyGLoo: using stdcall on win32'
elif os.name == 'posix':
	FUNCTYPE = ctypes.CFUNCTYPE
	print 'PyGLoo: using cdecl on posix'
else:
	FUNCTYPE = ctypes.CFUNCTYPE
	print 'PyGLoo: Warning: unknown OS, guessing cdecl'
# }

# function for making pointers
POINTER = ctypes.POINTER

# load the GL dll and function-loading-function
_libgl = None
_getProcAddress = None
if os.name == 'nt':
	print 'PyGLoo: loading opengl32.dll on win32'
	_libgl = ctypes.windll.LoadLibrary('opengl32')
	_getProcAddress = _libgl.wglGetProcAddress
elif os.name == 'posix':
	print 'PyGLoo: loading libGL.so on posix'
	_libgl = ctypes.cdll.LoadLibrary('libGL.so')
	_getProcAddress = _libgl.glXGetProcAddress
else:
	print 'PyGLoo: Warning: unknown OS, guessing libGL.so'
	_libgl = ctypes.cdll.LoadLibrary('libGL.so')
	_getProcAddress = _libgl.glXGetProcAddress
# }
_getProcAddress.restype = FUNCTYPE(None)
_getProcAddress.argtypes = (ctypes.c_char_p,)

def _wrapGetProcAddress(name):
	return _getProcAddress(ctypes.create_string_buffer(str(name)))
# }

print 'PyGLoo: initialized GL library'

print 'PyGLoo: initializing type system...'

# mappings for fixed bitwidth integral types
_int_types = [ctypes.c_byte, ctypes.c_short, ctypes.c_int, ctypes.c_long, ctypes.c_longlong]
_uint_types = [ctypes.c_ubyte, ctypes.c_ushort, ctypes.c_uint, ctypes.c_ulong, ctypes.c_ulonglong]
_ints_by_size = dict({(ctypes.sizeof(T), T) for T in _int_types})
_uints_by_size = dict({(ctypes.sizeof(T), T) for T in _uint_types})

# primary GL types
GLenum = _uints_by_size[4]
GLboolean = _uints_by_size[1]
GLbitfield = _uints_by_size[4]
GLvoid = None
GLbyte = _ints_by_size[1]
GLshort = _ints_by_size[2]
GLint = _ints_by_size[4]
GLclampx = GLint
GLubyte = _uints_by_size[1]
GLushort = _uints_by_size[2]
GLuint = _uints_by_size[4]
GLsizei = GLint
GLfloat = ctypes.c_float
GLclampf = GLfloat
GLdouble = ctypes.c_double
GLclampd = GLdouble
GLeglImageOES = ctypes.c_void_p
GLchar = ctypes.c_char
GLcharARB = GLchar
GLhandleARB = GLuint
if platform.system() == 'Darwin':
	# ugh, mac os
	GLhandleARB = ctypes.c_void_p
# }
GLhalf = GLushort
GLhalfARB = GLhalf
GLfixed = GLint
GLintptr = _ints_by_size[ctypes.sizeof(ctypes.c_void_p)]
GLsizeiptr = GLintptr
GLint64 = _ints_by_size[8]
GLuint64 = _uints_by_size[8]
GLintptrARB = GLintptr
GLsizeiptrARB = GLsizeiptr
GLint64EXT = GLint64
GLuint64EXT = GLuint64

# this should work, right?
# struct __GLsync *
GLsync = ctypes.c_void_p

# i don't think these are easily supportable
# struct _cl_context
# struct _cl_event

# callbacks
GLDEBUGPROC = FUNCTYPE(GLvoid, GLenum, GLenum, GLuint, GLenum, GLsizei, ctypes.POINTER(GLchar), ctypes.c_void_p)
GLDEBUGPROCARB = GLDEBUGPROC
GLDEBUGPROCKHR = GLDEBUGPROC

# vendor extensions
GLDEBUGPROCAMD = FUNCTYPE(GLvoid, GLuint, GLenum, GLenum, GLsizei, ctypes.POINTER(GLchar), ctypes.c_void_p)
GLhalfNV = GLushort
GLvdpauSurfaceNV = GLintptr

print 'PyGLoo: initialized type system'
'''

# write the common (manually-created) stuff
out.write(header)

# write the enums
out.write('''
print 'PyGLoo: initializing enum definitions...'

''')
out.write('# enum definitions\n')
for enums in soup.registry.find_all('enums'):
	for enum in enums.find_all('enum'):
		name = enum['name']
		value = enum['value']
		out.write('{name} = {value}\n'.format(name=name, value=value))
	# }
# }
out.write('''
print 'PyGLoo: initialized enum definitions'
''')

# write the functions proper
out.write('''
# function definitions
def init():
	print 'PyGLoo: initializing function definitions...'
	gl = Context()
	
''')
for command in soup.registry.commands.find_all('command'):
	name = str(command.proto.find('name').string).strip()
	# if no (strictly) specified return type, use void and check for pointer
	rtype = 'GLvoid'
	if command.proto.ptype:
		# determine non-void return type
		rtype = str(command.proto.ptype.string).strip()
		if 'struct' in rtype:
			# can't deal with this, use void and hope for pointer
			rtype = 'GLvoid'
		# }
	# }
	# begin hackyness for pointer parsing
	for s in command.proto.stripped_strings:
		for c in s:
			if c == '*': rtype = 'POINTER({0})'.format(rtype)
		# }
	# }
	# argument types
	atypes = []
	for param in command.find_all('param'):
		# if no (strictly) specified type, use void and hope for pointer
		at = 'GLvoid'
		if param.ptype:
			# determine non-void argument type
			at = str(param.ptype.string).strip()
			if 'struct' in at:
				# can't deal with this, use void and hope for pointer
				at = 'GLvoid'
			# }
		# }
		# continue hackyness for pointer parsing
		for s in param.stripped_strings:
			for c in s:
				if c == '*': at = 'POINTER({0})'.format(at)
			# }
		# }
		atypes.append(at)
	# }
	# fix bad tuples for no-args
	# write the function
	out.write('''\tgl.{name} = _wrapGetProcAddress('{name}')\n'''.format(name=name))
	out.write('''\tgl.{name}.restype = {rtype}\n'''.format(name=name, rtype=rtype))
	if len(atypes) == 0:
		out.write('''\tgl.{name}.argtypes = ()\n'''.format(name=name))
	else:
		out.write('''\tgl.{name}.argtypes = ({atypes},)\n'''.format(name=name, atypes = ', '.join(atypes)))
	# }
# }
out.write('''
	
	print 'PyGLoo: initialized function definitions'
	return gl
# }

''')









































