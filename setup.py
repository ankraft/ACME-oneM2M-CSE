from setuptools import setup

import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / 'README.md').read_text()

setup(
    name='ACME-oneM2M-CSE',
    version='0.10.0',
    url='https://github.com/ankraft/ACME-oneM2M-CSE',
    author='Andreas Kraft',
    author_email='an.kraft@gmail.com',
    description='An open source CSE Middleware for Education',
    long_description=README,
    long_description_content_type='text/markdown',
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.8',
    ],
    #packages=find_packages(),
    packages=[ 'acme' ],
	exclude=('tests',),
    include_package_data=True,
	install_requires=[
		'cbor2',
		'flask',
		'InquirerPy',
		'isodate',
		'paho-mqtt',
		'plotext',
		'requests', 
		'rich', 
		'tinydb',
		#'package1 @ git+https://github.com/CITGuru/PyInquirer.git@9d598a53fd17a9bc42efff33183cd2d141a5c949'
	],
    entry_points={
        'console_scripts': [
            'acme-cse=acme.__main__:main',
        ]
    },
)
