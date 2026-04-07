from setuptools import setup

setup(name='cbpi4-LevelSensorPumpActor',
      version='0.0.1',
      description='CraftBeerPi Plugin',
      author='Anton Wolf',
      author_email='anton.wolf3@gmail.com',
      url='',
      include_package_data=True,
      package_data={
        # If any package contains *.txt or *.rst files, include them:
      '': ['*.txt', '*.rst', '*.yaml'],
      'cbpi4-LevelSensorPumpActor': ['*','*.txt', '*.rst', '*.yaml']},
      packages=['cbpi4-LevelSensorPumpActor'],
     )