#!/usr/bin/env python

import os
import time

from utils.editor import edit_file, extract
from utils.interface import get_compressed_file, get_base64
from utils.constructor import constructor

class new(constructor):
   table = ""

   content = \
      "<tr>" + \
         "<td><a href=\"$path\">$name</a></td>" + \
         "<td>$version</td>" + \
         "<td>$date</td>" + \
         "<td>$description</td>" + \
      "</tr>"

   def build(self):
      for package in self.packages:
         module = self.path_pkg + "/" + package

         try:
            file = open(module + "/PKGBUILD")
         except FileNotFoundError:
            continue

         description = extract(module, "pkgdesc")
         version = extract(module, "pkgver")
         name = extract(module, "pkgname")

         for path in os.listdir(self.path_mirror):
            if path.startswith(package + "-" + version + "-"):
               content = self.content
               date = time.strftime("%d %h %Y", \
                  time.gmtime(os.path.getmtime(self.path_mirror + "/" + path)))

               self.table += content \
                  .replace("$path", path) \
                  .replace("$name", name) \
                  .replace("$date", date) \
                  .replace("$version", version) \
                  .replace("$description", description)

      self.move_to_mirror()
      self.replace_variables()
      self.compress()

   def move_to_mirror(self):
      os.system("cp " + self.path_www + "/index.html " + self.path_mirror)

   def replace_variables(self):
      for line in edit_file(self.path_mirror + "/index.html"):
         line = line.replace("$content", self.table)
         line = line.replace("$path", self.config("url"))
         line = line.replace("$database", self.config("database"))
         line = line.replace("images/logo.png", "data:image/png;base64," + get_base64(self.path_www + "/images/logo.png"))

         if line.strip() == "<link rel=\"stylesheet\" href=\"css/main.css\">":
            line = "<style type=\"text/css\">"
            line += get_compressed_file(self.path_www + "/css/main.css")
            line += "</style>"

         print(line)

   def compress(self):
      content = get_compressed_file(self.path_mirror + "/index.html")

      with open(self.path_mirror + "/index.html", "w") as f:
          f.write(content)
