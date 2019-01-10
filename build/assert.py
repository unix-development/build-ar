#!/usr/bin/env python

import sys
from helper import *

def test_repository():
   assert repository['database'], \
      'Database must be defined.'

   assert repository['git']['name'], \
      'Git name must be defined.'

   assert repository['git']['email'], \
      'Git email must be defined.'

   assert repository['ssh']['user'], \
      'SSH user must be defined.'

   assert repository['ssh']['host'], \
      'SSH host must be defined.'

   assert repository['ssh']['path'], \
      'SSH path must be defined.'

   assert repository['ssh']['port'], \
      'SSH port must be defined.'

   assert type(repository['ssh']['port']) is int, \
      'SSH port must be an integer.'

def test_ssh():
   command = 'ssh -i ./deploy_key -p {0} -q {1}@{2} [[ -d {3} ]] && echo 1 || echo 0'
   ssh = [ \
      repository['ssh']['port'], \
      repository['ssh']['user'], \
      repository['ssh']['host'], \
      repository['ssh']['path'] \
   ]

   assert output(command.format(*ssh).strip()).strip() == '1', \
      'SSH connection could not be established.'

def main(argv):
   if len(argv) == 1:
      if argv[0] == 'repository':
         test_repository()
      elif argv[0] == 'ssh':
         test_ssh()

if __name__ == '__main__':
   main(sys.argv[1:])
