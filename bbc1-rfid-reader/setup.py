import subprocess
from os import path
from setuptools import setup
from setuptools.command.install import install


here = path.abspath(path.dirname(__file__))

with open('README.rst') as f:
    readme = f.read()


class MyInstall(install):
    def run(self):
        try:
            pass

        except Exception as e:
            print(e)
            exit(1)

        else:
            install.run(self)


bbc1_requires = [
                    'py-bbclib>=1.6'
                ]

bbc1_packages = [
                 'bbc1',
                 'bbc1.lib'
                ]

bbc1_commands = []

bbc1_classifiers = [
                    'Development Status :: 4 - Beta',
                    'Programming Language :: Python :: 3.8',
                    'Topic :: Software Development'
                   ]

setup(
    name='bbc1-rfid-reader',
    version='0.2',
    description='RFID reader drivers for BBc-1',
    long_description=readme,
    url='https://github.com/beyond-blockchain',
    author='beyond-blockchain.org',
    author_email='office@beyond-blockchain.org',
    license='Apache License 2.0',
    classifiers=bbc1_classifiers,
    cmdclass={'install': MyInstall},
    packages=bbc1_packages,
    scripts=bbc1_commands,
    install_requires=bbc1_requires,
    zip_safe=False)


# end of setup.py
