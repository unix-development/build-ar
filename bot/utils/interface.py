#!/usr/bin/env python

import base64

def get_compressed_file(path):
   with open(path) as f:
      return " ".join(f.read().split())


def get_base64(path):
   with open(path, 'rb') as f:
      return base64.b64encode(f.read()).decode('utf8')
