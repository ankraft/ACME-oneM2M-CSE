#
#	hashcreds.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Hash credentials to be stored in credentials files. 
"""

if __name__ == '__main__':
	import hashlib, sys
	if len(sys.argv) != 2:
		print('Usage: python3 hashcreds.py <password or token>')
		sys.exit(1)
	print(hashlib.sha256(sys.argv[1].encode()).hexdigest())
