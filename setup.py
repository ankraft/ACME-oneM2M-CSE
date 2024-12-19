from setuptools import setup, find_packages

import pathlib, os, time

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / 'tools/pypi/README.md').read_text()

# Find directories that are modules and have __init__.py
directories = [d for d,n,f in os.walk('acmecse') if '__init__.py' in f]
print(directories)

setup(
	name='acmecse-dev',
	version=time.strftime("%Y%m%d%H%M%S"),

	# name='acmecse',
	# version='2024.10',


	author='Andreas Kraft',
	author_email='an.kraft@gmail.com',
	classifiers=[
		'License :: OSI Approved :: BSD License',
		'Programming Language :: Python :: 3.10',
	],
	description='An open source CSE Middleware for Education',
	entry_points={
		'console_scripts': [
			'acmecse=acmecse.__main__:main',
		]
	},
	include_package_data=True,
	install_requires=[
		'cachetools',
		'coapthon3-acme-cse',
		'cbor2',
		'flask',
		'flask-cors',
		'InquirerPy',
		'isodate',
		'paho-mqtt>=2.0.0',
		'plotext',
		'psycopg2-binary',
		'pyperclip',
		#'python3-dtls',
		'rdflib',
		'requests', 
		'rich', 
		'shapely',
		'textual>=1.0.0',
		# 'textual[syntax]',
		'textual-plotext',
		'tinydb',
		'waitress',
		'websockets',
	],
	license='BSD',
	long_description=README,
	long_description_content_type='text/markdown',
	packages = directories,
	#package_dir={'acmecse': 'acmecse'},
	url='https://acmecse.net',
)
