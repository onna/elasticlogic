from setuptools import setup

setup(
    name='elasticlogic',
    version='0.1',                          # Update the version number for new releases
    url='https://github.com/gitcarbs/elasticlogic',
    packages=['elasticlogic'],
    install_requires = [
        'python-dateutil',
        'pytest'
    ]
)