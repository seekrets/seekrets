from setuptools import setup
import os
import codecs

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open
    return codecs.open(os.path.join(here, *parts), 'r').read()


setup(
    name='Seekrets',
    version='0.1.0',
    url='https://github.com/seekrets',
    author='nir0s',
    author_email='nir36g@gmail.com',
    license='LICENSE',
    description='Search for secrets in git repositories',
    long_description=read('README.rst'),
    packages=[
        'seekrets',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'seekrets = seekrets.seekrets:main',
        ]
    },
    install_requires=[
        "sh==1.11",
        "click==6.6",
        "gitpython",
        "git-url-parse",
    ]
)
