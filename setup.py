#!/usr/bin/env python2

# Shoebot setup script
#
# python setup.py install', or
#    python setup.py --help' for more options
#

from __future__ import print_function

import glob
import os
import platform
import shutil
import sys
import textwrap

here = os.path.dirname(os.path.abspath(__file__))

try:
    from setuptools import setup
    from setuptools import Command as CleanBaseCommand
except ImportError:
    from distutils.core import setup
    from distutils.command import clean as CleanBaseCommand


class CleanCommand(CleanBaseCommand):
    """Custom clean command to tidy up the project root."""
    CLEAN_FILES = './build ./dist ./*.pyc ./*.tgz ./*.egg-info'.split(' ')

    user_options = []

    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        global here

        for path_spec in self.CLEAN_FILES:
            # Make paths absolute and relative to this path
            abs_paths = glob.glob(os.path.normpath(os.path.join(here, path_spec)))
            for path in [str(p) for p in abs_paths]:
                if not path.startswith(here):
                    # Die if path in CLEAN_FILES is absolute + outside this directory
                    raise ValueError("%s is not a path inside %s" % (path, here))
                print('removing %s' % os.path.relpath(path))
                shutil.rmtree(path)

long_description = textwrap.dedent("""
    Shoebot is a pure Python graphics robot: It takes a Python script as input,
    which describes a drawing process, and outputs a graphic in a common open
    standard format (SVG, PDF, PostScript, or PNG). It has a simple text editor
    GUI, and scripts can describe their own GUIs for controlling variables
    interactively. Being pure Python, it can also be used as a Python module,
    a plugin for Python-scriptable tools such as Inkscape, and run from the
    command line.
""")

# the following libraries will not be installed
EXCLUDE_LIBS = ['lib/sbopencv', 'lib/sbopencv/blobs']

for lib in EXCLUDE_LIBS:
    # get subdirs of excluded libs
    for root, dir, files in list(os.walk(lib))[1:]:
        EXCLUDE_LIBS.append(root)

# dir globbing approach taken from Mercurial's setup.py
datafiles = [(os.path.join('share/shoebot/', root), [os.path.join(root, file_)
                                                     for file_ in files]) for root, dir, files in os.walk('examples')]
datafiles.append(('share/pixmaps', ['assets/shoebot-ide.png']))
datafiles.append(('share/shoebot/data', ['assets/kant.xml']))
datafiles.append(('share/applications', ['assets/shoebot-ide.desktop']))

datafiles.extend([(os.path.join('share/shoebot/', root), [os.path.join(root, file_)
                                                          for file_ in files]) for root, dir, files in
                  os.walk('locale')])

# include all libs EXCEPT the ones mentioned in EXCLUDE_LIBS

datafiles.extend([(os.path.join('share/shoebot/', root) ,[os.path.join(root, file_)
for file_ in files]) for root,dir,files in os.walk('lib') if root not in EXCLUDE_LIBS])


# Also requires one of 'vext.gi' or 'pgi'
BASE_REQUIREMENTS=[
    "setuptools>=15.0.1",  #

    "cairocffi>=0.6",
    #"meta==0.4.1",
    "meta",
    "numpy==1.9.1",
    "Pillow==2.8.1",
]


# requirements to run examples
EXAMPLE_REQUIREMENTS=[
  "fuzzywuzzy==0.5.0",   # sbaudio
  "planar",       # examples
  "PySoundCard==0.5.0",  # sbaudio
]

def requirements(with_pgi=None, with_examples=True, debug=True):
    """
    Build requirements based on flags

    :param with_pgi: Use 'pgi' instead of 'gi' - False on CPython, True elsewhere
    :param with_examples:
    :return:
    """
    reqs = list(BASE_REQUIREMENTS)
    if with_pgi is None:
        is_pypy = '__pypy__' in sys.builtin_module_names
        is_jython = platform.system == 'Java'
        if is_pypy or is_jython:
            with_pgi = True
        else:
            with_pgi = False

    if debug:
        print('setup options: ')
        print('with_pgi:      ', 'yes' if with_pgi else 'no')
        print('with_examples: ', 'yes' if with_examples else 'no')
    if with_pgi:
        reqs.append("pgi")
        if debug:
            print("warning, as of April 2015 typography does not work with pgi")
    else:
        reqs.append("vext>=0.3.8")    # TODO - shouldn't be needed..
        reqs.append("vext.gi>=0.1.3")
    if with_examples:
        reqs.extend(EXAMPLE_REQUIREMENTS)

    if debug:
        print('')
        print('')
        for req in reqs:
            print(req)
    return reqs


setup(name="shoebot",
      version="1.1.1",
      description="Vector graphics scripting application",
      long_description=long_description,
      author="Ricardo Lafuente",
      author_email="r@sollec.org",
      license='GPL v3',
      url="http://shoebot.net",
      cmdclass={
          'clean': CleanCommand,
      },
      packages=[
          "shoebot",
          "shoebot.core",
          "shoebot.data",
          "shoebot.gui",
          "shoebot.io",
          "shoebot.grammar",
          "shoebot.grammar.nodebox-lib",
          "shoebot.grammar.nodebox-lib.nodebox",
          "shoebot.grammar.nodebox-lib.nodebox.graphics",
          "shoebot.grammar.nodebox-lib.nodebox.geo"
      ],
      data_files=datafiles,
      setup_requires=["setuptools>=15.0.1"],
      install_requires=requirements(debug="install" in sys.argv),
      entry_points={
          "console_scripts": [
             "sbot=shoebot.run:main",
             "shoebot-ide=shoebot.gui.ide:main"
          ],
          "gui_scripts": "shoebot-ide=shoebot.gui.ide:main"
      }
)
