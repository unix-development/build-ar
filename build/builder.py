#!/usr/bin/env python

import os
import sys
import json
import time
from package import *
from helper import *

def html():
   os.system('rm -rf ' + repository_path + '/{index.html,css,images}')

   table = ''
   remote_path = 'https://' + git_repository().rstrip('.git')

   for package in get_packages():
      module = packages_path + '/' + package
      description = extract(module, 'pkgdesc')
      version = extract(module, 'pkgver')
      name = extract(module, 'pkgname')

      for path in os.listdir(repository_path):
         if path.startswith(name + '-' + version + '-'):
            date = time.strftime('%d %h %Y', \
               time.gmtime(os.path.getmtime(repository_path + '/' + path)))

            content = \
               '<tr>' + \
                  '<td><a href="$path">$name</a></td>' + \
                  '<td>$version</td>' + \
                  '<td>$date</td>' + \
                  '<td>$description</td>' + \
               '</tr>'

            table += content \
               .replace('$path', path) \
               .replace('$name', name) \
               .replace('$date', date) \
               .replace('$version', version) \
               .replace('$description', description)

      os.system('cp -r ' + html_path + '/{index.html,css,images} ' + repository_path)

      for line in edit_file(repository_path + '/index.html'):
         line = line.replace('$database', repository['database'])
         line = line.replace('$remote_path', remote_path)
         line = line.replace('$path', repository['url'])
         line = line.replace('$content', table)
         print(line)

def create(database):
   if not os.path.exists(repository_path):
      os.makedirs(repository_path)

   sys.path.append(packages_path)

   for directory in get_packages():
      __import__(directory + '.package')
      os.chdir(packages_path + '/' + directory)
      module = sys.modules[directory + '.package']
      package = Package(module, directory)

   os.chdir(repository_path)
   os.system('repo-add ./' + database + '.db.tar.gz ./*.pkg.tar.xz')

def deploy():
   if is_travis():
      repository = git_repository()
      os.system('git push https://${GITHUB_TOKEN}@%s HEAD:master' % repository)

def config(setting):
   data = repository
   keys = setting.split('.')
   for key in keys:
      data = data[key]
   print(data)

def validate(case):
   if case == 'repository':
      assert repository['database'], \
         'Database must be defined.'
      assert repository['url'], \
         'Url must be defined.'
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

   elif case == 'ssh':
      script = 'ssh -i ./deploy_key -p $port -q $user@$host [[ -d $path ]] && echo 1 || echo 0'
      for key in repository['ssh']:
         value = repository['ssh'][key]
         script = script.replace(f'${key}', str(value))

      assert output(script) == '1', \
         'SSH connection could not be established.'

def main(argv):
   if len(argv) == 2:
      if argv[0] == 'create':
         create(argv[1])
      elif argv[0] == 'config':
         config(argv[1])
      elif argv[0] == 'validate':
         validate(argv[1])
   elif len(argv) == 1:
      if argv[0] == 'deploy':
         deploy()
      elif argv[0] == 'html':
         html()

if __name__ == '__main__':
   if os.getuid() == 0:
      print('This file needs to be not execute as root.')
      sys.exit(2)

   main(sys.argv[1:])
