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
   ssh_command = 'ssh -i ./deploy_key ' \
      '-p {port} ' \
      '-q {user}@{host} ' \
      '[[ -d {path} ]] && ' \
      'echo 1 || echo 0'

   assert output(ssh_command \
      .replace('{port}', str(repository['ssh']['port'])) \
      .replace('{user}', repository['ssh']['user']) \
      .replace('{host}', repository['ssh']['host']) \
      .replace('{path}', repository['ssh']['path'])) \
      .strip() == '1', \
      'SSH connection could not be established.'

def main(argv):
   if len(argv) == 1:
      if argv[0] == 'repository':
         test_repository()
      elif argv[0] == 'ssh':
         test_ssh()

if __name__ == '__main__':
   main(sys.argv[1:])
