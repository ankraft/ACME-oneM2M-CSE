from setuptools import setup

import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / 'README.md').read_text()

setup(
    name='ACME-oneM2M-CSE',
    version='2023.10.1',
    url='https://github.com/ankraft/ACME-oneM2M-CSE',
    author='Andreas Kraft',
    author_email='an.kraft@gmail.com',
    description='An open source CSE Middleware for Education',
    long_description=README,
    long_description_content_type='text/markdown',
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.10',
    ],
    #packages=find_packages(),
    packages=[ 'acme' ],
	exclude=('tests',),
    include_package_data=True,
	install_requires=[
		'cbor2',
		'flask',
		'flask-cors',
		'InquirerPy',
		'isodate',
		'paho-mqtt',
		'plotext',
        'python3-dtls',
		'rdflib',
		'requests', 
		'rich', 
        'shapely',
		'textual',
		'textual-plotext',
		'tinydb',
		'waitress',
	],
    entry_points={
        'console_scripts': [
            'acme-cse=acme.__main__:main',
        ]
    },
)
