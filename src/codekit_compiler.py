#!/usr/bin/env python
# encoding: utf-8
# vim: set expandtab ts=2 sw=2
# The MIT License (MIT)
#
# Copyright (c) 2015 Mads Sülau Jørgensen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Find the newest version at https://github.com/madssj/codekit-compiler

import os
import json
import subprocess
import tempfile

# the types from codekit
TYPE_LESS = 1
TYPE_CSS = 16
TYPE_JAVASCRIPT = 64
TYPE_HTM = 8192
TYPE_JPG = 16384
TYPE_PNG = 32768

LESSC = 'node_modules/.bin/lessc'

LESSC_OPTIONS = [
  '--clean-css=--s1 --advanced --compatibility=ie8',
]

UGLIFYJS = 'node_modules/.bin/uglifyjs'

CWD = os.getcwd()

def handle_less(inname, inpath, outname, outpath, options):
  def get_autoprefixer_config():
      autoprefixer_config = config['projectSettings']['autoprefixerBrowserString']

      # fix an issue with less-plugin-autoprefixer which should be fixed in PR#12
      import re
      return re.sub("\s*,\s*", ",", autoprefixer_config)

  global config

  # make a copy of the options so we can alter them
  less_options = list(LESSC_OPTIONS)

  if options.get('shouldRunAutoprefixer', 0) == 1:
    less_options.append('--autoprefix=%s' % get_autoprefixer_config())

  subprocess.call([LESSC] + less_options + [inpath, outpath])

def handle_javascript(inname, inpath, outname, outpath, options):
  global config

  append_files = []
  manual_imports = config.get('manualImportLinks', {}).get(inname)

  if manual_imports:
    append_files = [CWD + f['linkedFileAbbreviatedPath']
      for f in sorted(manual_imports, key=lambda x: x['position'])
    ]

  indir = os.path.dirname(inpath)
  tmpfile = tempfile.NamedTemporaryFile()

  for filename in append_files:
    tmpfile.write(open(os.path.join(indir, filename.strip())).read() + ";\n")

  tmpfile.write(open(inpath).read())
  tmpfile.flush()

  with open(outpath, 'w') as out:
    subprocess.call([UGLIFYJS, tmpfile.name], stdout=out)

handler_map = {
  TYPE_LESS: handle_less,
  TYPE_JAVASCRIPT: handle_javascript,
}

config = json.load(open('config.codekit'))

files = dict(
  (k, v) for k,v in config['files'].iteritems() if not v['ignore'] and v['outputPathIsSetByUser']
)

for filename, options in files.iteritems():
  inpath = options['inputAbbreviatedPath']
  outpath = options['outputAbbreviatedPath']
  filetype = options['fileType']

  handler = handler_map.get(filetype)

  if handler:
    print "handling", inpath, ">", outpath

    handler(inpath, CWD + inpath, outpath, CWD + outpath, options)
  else:
    print "no handler for file", filename
