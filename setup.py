# public-domain

from setuptools import setup, find_packages

setup(
  name='nonblocking',
  version='0.1.0',
  description='Nonblocking stream reads using Queue and a pump thread',
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  url='https://github.com/xloem/nonblocking',
  keywords=[],
  classifiers=[
    'Programming Language :: Python :: 3',
    'License :: Public Domain'
    'Operating System :: OS Independent',
  ],
  packages = find_packages(),
  install_requires=[
    'six>=1.16.0',
  ],
)
