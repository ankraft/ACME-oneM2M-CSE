from setuptools import setup, find_packages

setup(
    name='ACME-oneM2M-CSE',
    version='0.7.0',
    url='https://github.com/ankraft/ACME-oneM2M-CSE',
    author='Andreas Kraft',
    author_email='an.kraft@gmail.com',
    description='An open source CSE Middleware for Education',
    packages=find_packages(),
	install_requires=[
		'cbor2',
		'flask',
		'isodate', 
		'psutil',  
		'requests', 
		'rich', 
		'tinydb',
		#'package1 @ git+https://github.com/CITGuru/PyInquirer.git@9d598a53fd17a9bc42efff33183cd2d141a5c949'
	],
)
	#dependency_links=[
		#'git+https://github.com/CITGuru/PyInquirer.git@9d598a53fd17a9bc42efff33183cd2d141a5c949' 
    #]
