PyGLoo
======

Pure Python runtime OpenGL function loader / API wrapper

Basic Usage
-----------

Get an OpenGL context (Maya users: you already have one). `import pygloo`. Call `pygloo.init()`, which returns an object that contains the loaded OpenGL function pointers (hold on to this!). OpenGL enums / macro constants are avaliable as e.g. `pygloo.GL_VERSION`. Ideally, `init()` should only be called once per context, but nothing should break if it is called multiple times. The functions returned by `init()` _must only_ be used on the context that was active when it was called. `glGetError()` is called automagically after every other OpenGL function; if it signals an error a Python exception is raised.

Building
--------

The script `makepygloo.py` reads `api/gl.xml` and creates `pygloo.py`, which is the module that provides the OpenGL API wrapper. In unix land, the up-to-date GL api specification can be obtained by
`svn co --username anonymous --password anonymous https://cvs.khronos.org/svn/repos/ogl/trunk/doc/registry/public/api/ api`.

Details
-------

PyGLoo uses the ctypes module to load the OpenGL DLL and to retrieve the API entry points. The OpenGL datatypes are provided as aliases to ctypes types. The loaded functions are ctypes function pointers, with the argument and return types correctly set. As interaction with ctypes is necessary to use these functions, some familiarity is recommended. Of particular interest in the documentation are the sections on arrays, pointers and type conversions starting
[here](https://docs.python.org/2/library/ctypes.html#arrays).

ctypes will happily convert function arguments from python types (e.g. integer to `GLuint` and string to `char *`), and will even convert ctypes objects into pointers. If a function takes a pointer as an output argument, then an appropriate ctypes object should be manually created for that. Return values will also be converted back into Python types where possible. It must be noted, however, that some OpenGL functions do not take to this well. For instance
`glGetString()` returns a `GLubyte *`, which is not the same as `char *` so ctypes will not convert it to a string. In this case, the ctypes function `cast()` can be used like so: `cast(gl.glGetString(GL_VERSION), c_char_p).value`. ctypes appears to have no notion of const-ness.

As I do not believe an equivalent exists in ctypes itself, PyGLoo includes the helper function `c_array()` which takes a ctypes type and a flat iterable and produces a ctypes array of the specified type and correct size, initialized with (correctly converted) data from the iterable. This array can then be passed directly to functions that take the corresponding pointer type. A contrived example:
`gl.glBufferData(GL_ARRAY_BUFFER, 4 * sizeof(GLfloat), c_array(GLfloat, [1, 2, 3, 4]), GL_STATIC_DRAW)`.

Currently for Windows and Linux. Designed to circumvent Maya being shit.

Title: PyGLoo (Python + GLEW, but unrelated to GLEW itself)

Potential Use in Maya
---------------------

Disclaimer: As I have been having trouble getting anything to draw with OpenGL in Maya on Windows (although I _can_ load the functions and call them in the script editor), I haven't really been able to test this.

The draw method of a locator node subclass that draws a single line using PyGLoo might look something like this:

```python
import pygloo
from pygloo import *

gl = pygloo.init()

def draw(self, view, path, style, status): 
	
	view.beginGL() 
	
	gl.glBegin(GL_LINES)
	gl.glVertex3f(0.0, -0.5, 0.0)
	gl.glVertex3f(0.0, 0.5, 0.0)
	gl.glEnd()
	
	view.endGL()
```


