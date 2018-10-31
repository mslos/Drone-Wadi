from setuptools import setup, find_packages

setup(name='data-mule',
      version='0.1.0',
      description='Companion computer avionics package for Mission Mule Data Mule',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
      ],
      url='https://github.com/missionmule/data-mule',
      author='Zane Mountcastle',
      author_email='zane@missionmule.com',
      packages=['avionics'],
      python_requires='>=3.6',
      setup_requires=['nose', 'rednose'],
      install_requires=[
          'dronekit',
          'geopy',
          'pymavlink==2.0.6',
          'paramiko',
          'pyserial',
          'pytest-runner'
      ],
      tests_require='pytest',
      test_suite='avionics/tests',
      zip_safe=False)
