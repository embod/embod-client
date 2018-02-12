from setuptools import setup
setup(
  name = 'embod_client',
  packages = ['embod_client'], # this must be the same as the name above
  version = '0.0.3',
  description = 'Client library for controlling agents in embod.ai environments',
  author = 'Chris Bamford',
  author_email = 'chris.bamford@embod.ai',
  url = 'https://github.com/embod/embod_client', # use the URL to the github repo
  #download_url = 'https://github.com/embod/embod_client/archive/0.1.tar.gz', # I'll explain this in a second
  keywords = ['embod', 'environment', 'agents'], # arbitrary keywords
  classifiers = [],
  install_requires = [
    "websockets>=4.0.1",
    "numpy>=1.13.1",
  ]
)