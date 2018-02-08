from distutils.core import setup
setup(
  name = 'embod-client',
  packages = ['embod-client'], # this must be the same as the name above
  version = '0.0.1',
  description = 'Client library for controlling agents in embod.ai environments',
  author = 'Chris Bamford',
  author_email = 'chris.bamford@embod.ai',
  url = 'https://github.com/embod/embod-client', # use the URL to the github repo
  download_url = 'https://github.com/embod/embod-client/archive/0.1.tar.gz', # I'll explain this in a second
  keywords = ['embod', 'environment', 'agents'], # arbitrary keywords
  classifiers = [],
)