#
#	hashcreds.py
#
#	(c) 2025 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
""" Hash credentials to be stored in credentials files. 
"""

if __name__ == '__main__':
	import hmac, hashlib, sys
	if len(sys.argv) != 3:
		print('Usage: python3 hashcreds.py <password or token> <secret key>')
		sys.exit(1)
	print(hmac.new(sys.argv[2].encode(), msg=sys.argv[1].encode(), digestmod=hashlib.sha256).digest().hex())