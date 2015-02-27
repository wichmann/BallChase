# BallChase
Simple ball chase game developed in Python with Cocos2d.

## License
BallChase is released under the GNU General Public License v2 or newer.

## Requirements
BallChase runs under Python 2.7 (cpython and pypy) and Python 3.4. It requires
pyglet and Cocos2d.

## Known problems
BallChase has problems on some computers with Intel graphics chipsets, e.g.
the Mobile Intel 4 Series Express Chipset Family. The error can be solved by
changing one line in the pyglet library (pyglet/gl/lib.py, line 102):

-        if error:
+        if error and error != 1286:

With this change an OpenGL error (Invalid Framebuffer Operation) is simply
ignored and the program works as expected.

## Third party software
BallChase includes parts of or links with the following software packages and 
programs, so give the developers lots of thanks sometime! 

* soundex.py originally from http://www.partiallydisassembled.net/make_me/ and
  modified later for the tetrico game from cocos2d project.
* some image and sound files from the tetrico game (cocos2d project)
