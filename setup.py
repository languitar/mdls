from setuptools import find_packages, setup


setup(
    name='mdls',
    version='0.1.0',

    description='A language server for markdown',
    author='Johannes Wienke',
    author_email='languitar@semipol.de',
    license='LGPLv3',

    package_dir={
        '': 'src',
    },
    packages=find_packages('src'),

    install_requires=[
        'loggerbyclass',
        'python-jsonrpc-server',
        'mistletoe',
    ],

    entry_points={
        'console_scripts': [
            'mdls = mdls:main',
        ],
    }
)
