from setuptools import setup, find_packages
import sys

if sys.version_info[0] < 3 or sys.version_info[1] < 5:
    sys.exit('Sorry, Python < 3.5 is not supported')

setup(name='waybackscraper',
      version='0.2',
      description='Scrapes a website archives on the wayback machine using asyncio.',
      author='Arthur Brenaut',
      author_email='arthur.brenaut@gmail.com',
      packages=find_packages(),
      install_requires=[
          'aiohttp',
          'lxml'
      ],
      zip_safe=False)
