from setuptools import setup

setup(name='mosquito',
      project_name='mosquito',
      version = '1.2.1',
      description = 'News aggregator',
      url = 'https://github.com/livelace/mosquito',
      author = 'Oleg Popov',
      author_email = 'o.popov@livelace.ru',
      license = 'BSD',
      packages = ['mosquito', 'mosquito.plugins'],
      entry_points = {
                    'console_scripts': [
                                        'mosquito=mosquito.__main__:main'
                                        ],
                    }
      )
