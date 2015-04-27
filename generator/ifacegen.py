# Created by Evgeny Kamyshanov on March, 2014
# Copyright (c) 2013-2014 BEFREE Ltd.
# Modified by Evgeny Kamyshanov on March, 2015
# Copyright (c) 2014-2015 Evgeny Kamyshanov

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


from ifaceobjcgen import *
from ifaceswiftgen import *
import argparse
import sys
import os

def processIface( jsonFile, verbose, typeNamePrefix, outDir, category, genType ):

	if outDir is not None:
		genDir = os.path.abspath( outDir )

	if typeNamePrefix is not None:
		GenModule.namePrefix = typeNamePrefix
		GenType.namePrefix = typeNamePrefix

	module = parseModule( jsonFile )
	if module is None:
		print("Can't load module " + jsonFile)
		return

	if verbose:
		for genTypeKey in module.typeList.keys():
			print( str( module.typeList[genTypeKey] ) + '\n' )
		for method in module.methods:
			print( str( method ) + '\n' )

	if genDir is None:
		genDir = 'gen-objc'

	if genType is None or genType == 'objc':
		writeObjCImplementation( genDir, category, module )
	elif genType == 'swift':
		writeSwiftImplementation( genDir, category, module )
	else:
		print("Unknown generator: " + genType)


def main():
	parser = argparse.ArgumentParser(description='JSON-ObjC interface generator')
	
	parser.add_argument('rpcInput', metavar='I', type=unicode, nargs = '+', help = 'Input JSON RPC files')
	parser.add_argument('--prefix', type=unicode, action='store', required=False, help='Class and methods prefix')
	parser.add_argument('--verbose', action='store_true', required=False, help='Verbose mode')
	parser.add_argument('--gen', required=False, help="Type of generator. Use 'swift' or 'objc'")
	parser.add_argument('-o', '--outdir', action='store', required=False, help="Output directory name")
	parser.add_argument('--category', type=unicode, action='store', required=False, help='Generate a separate category files for de-/serialization methods')

	parsedArgs = parser.parse_args()
	if len(sys.argv) == 1:
		parser.print_help()
		return 0

	try:
		for rpcInput in parsedArgs.rpcInput:
			processIface( rpcInput, parsedArgs.verbose, parsedArgs.prefix, parsedArgs.outdir, parsedArgs.category, parsedArgs.gen )
	except Exception as ex:
		print( str(ex) )
		sys.exit(1)
	except:
		print( "Unexpected error:" + sys.exc_info()[0] )
		sys.exit(1)		

	return 0

#########

if __name__ == "__main__":
	main()
	