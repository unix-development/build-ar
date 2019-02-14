#!/usr/bin/env python

if __name__ == "__main__":
   if os.getuid() == 0:
      sys.exit("This file needs to be not execute as root.")
