#python
from ifaceparser import *
import argparse
import sys
import types
import os
from collections import OrderedDict

variableCounter = 0
def newVariableCounter():
	global variableCounter
	oldVariableCounter = variableCounter
	variableCounter += 1
	return oldVariableCounter

def assumeOBJCType( genType ):
	if isinstance( genType, GenIntegralType ):
		t = genType.sType
		if t == "string":
			return "NSString"
		if t == 'bool':
			return "BOOL";
		if t == "int32":
			return "int32_t";
		if t == "int64":
			return "int64_t";
		if t == "double":
			return "double_t";
		if t == "raw":
			return "NSDictionary";
		if t == "rawstr":
			return "NSDictionary";
	if isinstance( genType, GenComplexType ):
		return genType.name
	if isinstance( genType, GenListType ):
		return 'NSArray';
	return "_ERROR_"

##############

def writeOBJCTypeSuperInitDeclaration( fileOut, superType ):
	fileOut.write('[super init')
	prefx = "With"
	for fieldName in superType.allFieldNames():
		fieldType = superType.fieldType( fieldName )
		fieldAlias = superType.fieldAlias( fieldName )
		fileOut.write( prefx + capitalizeFirstLetter( fieldAlias ) + ':' + fieldAlias )
		if prefx == "With":
			prefx = '\n' + '\t'*6 + 'and'
	fileOut.write(']')	

def writeOBJCTypeInitDeclaration( fileOut, genType, implementation ):
	fileOut.write('- (id)init')
	prefx = "With"
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		fileOut.write( prefx + capitalizeFirstLetter(fieldAlias) + ':(' + assumeOBJCType(fieldType) + fieldType.ptr + ')' + fieldAlias )
		if prefx == "With":
			prefx = '\n\tand'
	if not implementation:
		fileOut.write(';\n')

def writeOBJCTypeInitDictDeclaration( fileOut, implementation ):
	fileOut.write('- (id)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error')
	if not implementation:
		fileOut.write(';\n')

def writeOBJCTypeInitDataDeclaration( fileOut, implementation ):
	fileOut.write('- (id)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error')
	if not implementation:
		fileOut.write(';\n')

def writeOBJCTypeDeclaration( fileOut, genType, writeConstructors, writeDump ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return
	
	if genType.baseType is not None:
		fileOut.write("\n@interface " + genType.name + ": " + genType.baseType.name + "\n")
	else:
		fileOut.write("\n@interface " + genType.name + ": NSObject\n")

	if writeDump:
		fileOut.write("- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;\n")
	if writeConstructors:
		writeOBJCTypeInitDeclaration( fileOut, genType, implementation = False )
		writeOBJCTypeInitDictDeclaration( fileOut, implementation = False )
		writeOBJCTypeInitDataDeclaration( fileOut, implementation = False )	

	for fieldName in genType.fieldNames():
		fieldType = genType.fieldType(fieldName)
		if isinstance( fieldType, GenListType ):
			fileOut.write("@property (nonatomic) " + assumeOBJCType( fieldType ) + fieldType.ptr + '/*' + assumeOBJCType( fieldType.itemType ) + '*/' + " " + genType.fieldAlias( fieldName ) + ";\n")
		else:
			fileOut.write("@property (nonatomic) " + assumeOBJCType( fieldType ) + fieldType.ptr + " " + genType.fieldAlias(fieldName) + ";\n")
	fileOut.write("@end;\n");

def writeOBJCMethodDeclaration( fileOut, method, implementation ):
	argDecoration = " "
	if len(method.prerequestTypes) + len(method.requestTypes) > 1:
		argDecoration = "\n\t\t"

	if method.responseType is not None:
		if isinstance( method.responseType, GenListType ):
			fileOut.write("- (" + assumeOBJCType( method.responseType ) + method.responseType.ptr + '/*' + assumeOBJCType( method.responseType.itemType ) + '*/' + ")" + method.name )			
		else:		
			fileOut.write("- (" + assumeOBJCType( method.responseType ) + method.responseType.ptr + ")" + method.name )
	else:
		fileOut.write("- (void)" + method.name )
	
	pref = "With"

	prerequestFormalType = method.formalPrerequestType();
	requestFormalType = method.formalRequestType();

	if prerequestFormalType is not None:
		for argName in prerequestFormalType.fieldNames():
			argType = prerequestFormalType.fieldType(argName)
			argAlias = prerequestFormalType.fieldAlias(argName)
			typeStr = assumeOBJCType( argType )
			fileOut.write( pref + capitalizeFirstLetter( argAlias ) + ":(" + typeStr + argType.ptr + ")" + argAlias );
			pref = argDecoration + "and"

	if len(method.requestTypes) != 0:
		for argName in requestFormalType.fieldNames():
			argType = requestFormalType.fieldType(argName)
			argAlias = requestFormalType.fieldAlias(argName)
			typeStr = assumeOBJCType( argType )
			fileOut.write( pref + capitalizeFirstLetter( argAlias ) + ":(" + typeStr + argType.ptr + ")" + argAlias )
			pref = argDecoration + "and"

	fileOut.write( pref + "Error:(NSError* __autoreleasing*)error")

	if not implementation:
		fileOut.write(";\n\n");

def decorateOBJCReturnedType( levelTmpVar, objcRetTypeStr, retType ):
	formatNSNumberStr = '( {0} = {1}, [{0} isEqual:[NSNull null]] ? {2} : (({3}){0}).{4} )'
	formatNSStringStr = '( {0} = {1}, [{0} isEqual:[NSNull null]] ? nil : (NSString*){0} )'
	formatNSDictionaryStr = '( {0} = {1}, [{0} isEqual:[NSNull null]] ? nil : (NSDictionary*){0} )'
	formatRawNSDictionaryStr = '( {0} = {1}, [{0} isEqual:[NSNull null]] ? nil : [NSJSONSerialization JSONObjectWithData:[(NSString*){0} dataUsingEncoding:NSUTF8StringEncoding] options:NSJSONReadingAllowFragments error:&error] )'		
	if retType.sType == "bool":
		return formatNSNumberStr.format( levelTmpVar, objcRetTypeStr, 'NO', 'NSNumber*', 'boolValue' )
	if retType.sType == "int32":
		return formatNSNumberStr.format( levelTmpVar, objcRetTypeStr, '0', 'NSNumber*', 'integerValue' )
	if retType.sType == "int64":
		return formatNSNumberStr.format( levelTmpVar, objcRetTypeStr, '0L', 'NSNumber*', 'longLongValue' )
	if retType.sType == "double":
		return formatNSNumberStr.format( levelTmpVar, objcRetTypeStr, '0.0', 'NSNumber*', 'doubleValue' )
	if retType.sType == "string":
		return formatNSStringStr.format( levelTmpVar, objcRetTypeStr )
	if retType.sType == "raw":
		return formatNSDictionaryStr.format( levelTmpVar, objcRetTypeStr )
	if retType.sType == "rawstr":
		return formatRawNSDictionaryStr.format( levelTmpVar, objcRetTypeStr )
	return "ERROR";

def unwindReturnedTypeToOBJC( fileOut, objcDictName, outType, outArgName, level, tmpVarName ):

	if isinstance( outType, GenIntegralType ): 	
		if outArgName is None:
			#return ( decorateOBJCReturnedType( tmpVarName, objcDictName, outType ) ) #TODO: fix this strange 'objcDictName' behavior in case of lists unwind
			return objcDictName;
		else:
			return ( decorateOBJCReturnedType( tmpVarName, '[' + objcDictName +  ' objectForKey:@"' + outArgName + '"]', outType ) )

	if isinstance( outType, GenComplexType ):
		objCResType = assumeOBJCType( outType )
		currentDictName = objcDictName
		resName = outType.name + str( newVariableCounter() )	

		if outArgName is None or outArgName != 'self':
			fileOut.write('\t'*level + objCResType + outType.ptr + ' ' + resName + ';\n')
		else:		
			resName = 'self'

		if outArgName is not None and outArgName != 'self':
			currentDictName = objcDictName + capitalizeFirstLetter( outArgName ) + str( newVariableCounter() )
			fileOut.write('\t'*level + 'NSDictionary* ' + currentDictName + ' = [' + objcDictName + ' objectForKey:@"' + outArgName + '"];\n')
			fileOut.write('\t'*level + 'if ( ' + currentDictName + ' != nil && ![' + currentDictName + ' isEqual:[NSNull null]]) {\n')
			level += 1
 			fileOut.write( '\t'*level + resName + ' = [' + objCResType + ' new];\n' )
 		elif outArgName != 'self':
 			fileOut.write( '\t'*level + resName + ' = [' + objCResType + ' new];\n' )

#TODO: uncomment after optional arguments appear
#			errMsg = '@"Can`t parse answer from server in ' + outArgName + '"'
#			fileOut.write('\tif ( ' + currentDictName + ' != nil ) {\n\t\tNSLog(' + errMsg +  ');\n')
#			fileOut.write('\t\t*error = [self errorWithMessage:' + errMsg + '];\n')
#			fileOut.write('\t\treturn nil;\n\t}\n')

		for fieldKey in outType.allFieldNames():
			outField = outType.fieldType(fieldKey)
			value = unwindReturnedTypeToOBJC( fileOut, currentDictName, outField, fieldKey, level+1, tmpVarName )
			fileOut.write('\t'*level + resName + '.' + outType.fieldAlias(fieldKey) + ' = ' + value + ';\n')

		if outArgName is not None and outArgName != 'self':
			level -= 1
			fileOut.write('\t'*level + '}\n')

		return resName

	if isinstance( outType, GenListType ):
		if outArgName is None:
			currentArrayName = objcDictName
		else:
			currentArrayName = objcDictName + capitalizeFirstLetter( outArgName ) + str( newVariableCounter() )
			fileOut.write('\t'*level + 'NSArray* ' + currentArrayName + ' = [' + objcDictName + ' objectForKey:@"' + outArgName + '"];\n')

		objCResType = assumeOBJCType( outType )
		if outArgName is not None:
			resName = outArgName + str(level)
		else:
			resName = "array" + str(level)

		fileOut.write('\t'*level + 'NSMutableArray* ' + resName + ';\n')

		fileOut.write('\t'*level + 'if ( ' + currentArrayName + ' != nil && ![' + currentArrayName + ' isEqual:[NSNull null]]) {\n')
		level += 1

		fileOut.write('\t'*level + resName + ' = [NSMutableArray arrayWithCapacity:[' + currentArrayName + ' count]];\n')

		fileOut.write('\t'*level + 'for ( id item in ' + currentArrayName + ') {\n' )
		item = unwindReturnedTypeToOBJC( fileOut, 'item', outType.itemType, None, level+1, tmpVarName )
		fileOut.write( '\t'*(level+1) + '[' + resName + ' addObject:' + item + '];\n' )
		fileOut.write('\t'*level + '}\n' )

		level -= 1
		fileOut.write('\t'*level + '}\n')

		return resName
					
def decorateOBJCInputType( objcInpTypeStr, inpType ):
	prefix = "NULLABLE("
	suffix = ")"
	if inpType.sType == 'bool':
		prefix = '[NSNumber numberWithBool:'
		suffix = "]"
	if inpType.sType == 'int32':
		prefix = '[NSNumber numberWithInt:'
		suffix = ']'
	if inpType.sType == 'int64':
		prefix = '[NSNumber numberWithLongLong:'
		suffix = ']'
	if inpType.sType == 'double':
		prefix = '[NSNumber numberWithDouble:'
		suffix = ']'
	if inpType.sType == 'rawstr':
		prefix = '[[NSString alloc] initWithData:[NSJSONSerialization dataWithJSONObject:'
		suffix =  ' options:jsonFormatOption error:error] encoding:NSUTF8StringEncoding]'
	return prefix + objcInpTypeStr + suffix

def unwindInputTypeToOBJC( fileOut, inputType, inputArgName, level  ):
		if isinstance( inputType, GenIntegralType ):
			fileOut.write( decorateOBJCInputType( inputArgName, inputType ) )
	
		elif isinstance( inputType, GenComplexType ):
			fileOut.write( "@{\n" )
	
			firstArgument = True
			for argName in inputType.allFieldNames():
				if not firstArgument:
					fileOut.write(",\n")
				firstArgument = False

				fileOut.write( '\t'*level + '@"' + argName + '" : ')
				fieldType = inputType.fieldType(argName)
				objcStatement = inputType.fieldAlias(argName)
				if inputArgName is not None:
					objcStatement = inputArgName + '.' + inputType.fieldAlias(argName)
				unwindInputTypeToOBJC( fileOut, fieldType, objcStatement, level+1 )

			fileOut.write("\n" + '\t'*level + "}")

		elif isinstance( inputType, GenListType ):
			if isinstance( inputType.itemType, GenIntegralType ):
				fileOut.write( 'NULLABLE(' + inputArgName + ')' )
			else:
				fileOut.write('^NSArray*(NSArray* inArr) {\n' + '\t'*level + 'NSMutableArray* resArr = [NSMutableArray arrayWithCapacity:[inArr count]];\n')
				fileOut.write('\t'*level + '\tfor ( ' + assumeOBJCType(inputType.itemType) + inputType.itemType.ptr + ' inObj in inArr ) {\n' ) 
				fileOut.write('\t'*level + '\t\t[resArr addObject:')
				unwindInputTypeToOBJC( fileOut, inputType.itemType, 'inObj', level+2 )
				fileOut.write( '];\n' + '\t'*level + '\t}\n' + '\t'*level + '\treturn resArr; } ( ' + inputArgName + ' )' )

def writeOBJCTypeImplementation( fileOut, genType, writeConstructors, writeDump ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return		
	fileOut.write("\n@implementation " + genType.name + "\n") 
	
	if writeDump:
		fileOut.write("- (NSData*)dumpWithError:(NSError* __autoreleasing*)error {\n")
		fileOut.write("\tNSDictionary* outDict = ")
		unwindInputTypeToOBJC( fileOut, genType, 'self', 2 )
		fileOut.write(";\n")
		fileOut.write("\treturn [NSJSONSerialization dataWithJSONObject:outDict options:jsonFormatOption error:error];\n}\n")

	if writeConstructors:
		writeOBJCTypeInitDeclaration( fileOut, genType, implementation = True )
		fileOut.write('{\n')
		if genType.baseType is not None:
			fileOut.write('\tif (self = ')
			writeOBJCTypeSuperInitDeclaration( fileOut, genType.baseType )
			fileOut.write(') {\n')
		else:
			fileOut.write('\tif (self = [super init]) {\n')
		
		for fieldName in genType.fieldNames():
			field = genType.fieldType(fieldName)
			fieldAlias = genType.fieldAlias(fieldName)
			fileOut.write('\t\t_' + fieldAlias + ' = ' + fieldAlias + ';\n' )
		fileOut.write('\t}\n\treturn self;\n}\n')

		fileOut.write('- (void)readDictionary:(NSDictionary*)dict {\n')
		fileOut.write('\tid tmp; NSError* error;\n')
		unwindReturnedTypeToOBJC( fileOut, 'dict', genType, 'self', level=1, tmpVarName='tmp' )
		fileOut.write('}\n')

		writeOBJCTypeInitDictDeclaration( fileOut, implementation = True )
		fileOut.write('{\n')
		fileOut.write('\tif ( dictionary == nil ) return nil;\n')	
		fileOut.write('\tif (self = [super init]) {\n')
		fileOut.write('\t\t[self readDictionary:dictionary];\n')
		fileOut.write('\t}\n\treturn self;\n}\n')

		writeOBJCTypeInitDataDeclaration( fileOut, implementation = True )
		fileOut.write('{\n')
		fileOut.write('\tif ( jsonData == nil ) return nil;\n')		
		fileOut.write('\tif (self = [super init]) {\n')
		fileOut.write('\t\tNSDictionary* dict = [NSJSONSerialization JSONObjectWithData:jsonData options:NSJSONReadingAllowFragments error:error];\n');
		fileOut.write('\t\tif ( *error != nil ) {\n\t\t\treturn nil;\n\t\t}\n')		
		fileOut.write('\t\t[self readDictionary:dict];\n')
		fileOut.write('\t}\n\treturn self;\n}\n')

	fileOut.write("@end\n")
						
def writeOBJCMethodImplementation( fileOut, method ):
	writeOBJCMethodDeclaration( fileOut, method, implementation = True )
	fileOut.write(" {\n")

	tmpVarName = "tmp"
	fileOut.write('\tid ' + tmpVarName + ';\n')

	prerequestFormalType = method.formalPrerequestType();
	requestFormalType = method.formalRequestType();

	pref = "\t\t"
	if prerequestFormalType is not None:
		fileOut.write('\t[transport setRequestParams:@{\n')
		for argName in prerequestFormalType.fieldNames():
			arg = prerequestFormalType.fieldType(argName)
			argAlias = prerequestFormalType.fieldAlias(argName)
			fileOut.write( pref + '@"' + argName + '" : ' + decorateOBJCInputType( argAlias, arg ) )
			pref = ',\n\t\t'
		fileOut.write('\n\t}];\n')

	if requestFormalType is not None:		
		fileOut.write("\tNSDictionary* inputDict = ")
		unwindInputTypeToOBJC( fileOut, method.formalRequestType(), None, 2 )
		
		fileOut.write(";\n")

		fileOut.write("\tNSData* inputData = [NSJSONSerialization dataWithJSONObject:inputDict options:jsonFormatOption error:error];\n")
		fileOut.write('\tif ( ![transport writeAll:inputData prefix:@"' + method.prefix + '" error:error] ) {\n')
	else:
		fileOut.write('\tif ( ![transport writeAll:nil prefix:@"' + method.prefix + '" error:error] ) {\n')

	# fileOut.write('\t\tNSLog(@"' + method.name + ': server call failed, %@", *error);\n')

	if method.responseType is None:
		fileOut.write('\t\treturn;\n\t}\n')		
		fileOut.write('}\n')
		return
	else:
		fileOut.write('\t\treturn nil;\n\t}\n')

	fileOut.write('\tNSData* outputData = [transport readAll];\n\tif ( outputData == nil ) {\n')
	# fileOut.write('\t\tNSLog(@"' + method.name + ': empty answer");\n\t\treturn nil;\n\t}\n')
	fileOut.write('\t\treturn nil;\n\t}\n')

	outputName = 'output'

	outputStatement = 'NSDictionary* ' + outputName;
	if isinstance( method.responseType, GenListType ):
		outputStatement = 'NSArray* ' + outputName

	fileOut.write('\t' + outputStatement + ' = [NSJSONSerialization JSONObjectWithData:outputData options:NSJSONReadingAllowFragments error:error];\n');
	fileOut.write('\tif ( *error != nil ) {\n\t\treturn nil;\n\t}\n')

	retVal = unwindReturnedTypeToOBJC( fileOut, outputName, method.responseType, method.responseArgName, 1, tmpVarName )

	fileOut.write('\treturn ' + retVal + ';\n')	
	fileOut.write("}\n\n")

def writeObjCIfaceHeader( fileOut, inputName ):
	fileOut.write("\n#import <Foundation/Foundation.h>\n")
	fileOut.write('#import "IFTransport.h"\n')

def writeObjCIfaceImports( fileOut, importNames ):
	for name in importNames:
		fileOut.write('#import "%s.h"\n' % name)

def writeObjCIfaceDeclaration( fileOut, inputName ):
	fileOut.write("\n@interface " + inputName + ": NSObject\n")
	fileOut.write("\n- (id)initWithTransport:(id<IFTransport>)transport;\n\n")

def writeObjCIfaceFooter( fileOut, inputName ):
	fileOut.write("\n@end")

def writeObjCImplHeader( fileOut, inputName ):
	fileOut.write('#import "' + inputName + '.h"\n')
	fileOut.write("#define NULLABLE( s ) (s == nil ? [NSNull null] : s)\n");
	fileOut.write('static const NSUInteger jsonFormatOption = \n#ifdef DEBUG\nNSJSONWritingPrettyPrinted;\n#else\n0;\n#endif\n')
	fileOut.write('\n#pragma clang diagnostic push\n#pragma clang diagnostic ignored "-Wunused"\n\n')

def writeObjCImplDeclaration( fileOut, inputName ):
	fileOut.write("\n@interface " + inputName + "() {\n\tid<IFTransport> transport;\n}\n@end\n")
	fileOut.write("\n@implementation " + inputName + "\n")
	fileOut.write("\n- (id)initWithTransport:(id<IFTransport>)trans {\n")
	fileOut.write("\tif ( self = [super init] ) {\n\t\ttransport = trans;\n\t}\n\treturn self;\n}\n")
	fileOut.write('- (NSError*)errorWithMessage:(NSString*)msg {\n')
	fileOut.write('\tNSDictionary* errData = [NSDictionary dictionaryWithObject:msg forKey:NSLocalizedDescriptionKey];\n')
	fileOut.write('\treturn [NSError errorWithDomain:NSStringFromClass([self class]) code:0 userInfo:errData];\n}\n')	

def writeObjCImplFooter( fileOut, inputName ):
	fileOut.write("\n@end")	

def writeObjCFooter( fileOut ):
	fileOut.write('\n#pragma clang diagnostic pop\n')

def writeWarning( fileOut, inputName ):
	fileOut.write("/**\n")
	fileOut.write(" * @generated\n *\n")
	fileOut.write(" * AUTOGENERATED. DO NOT EDIT.\n *\n")
	fileOut.write(" */\n\n")


#####################################

def processJSONIface( jsonFile, typeNamePrefix, outDir ):

	if outDir is not None:
		genDir = os.path.abspath( outDir )

	if typeNamePrefix is not None:
		GenType.namePrefix = typeNamePrefix
		GenMethod.namePrefix = typeNamePrefix

	module = parseModule( jsonFile )
	if module is None:
		print "Can't load module " + jsonFile;
		return

	if not os.path.exists( genDir ):
	    os.makedirs( genDir )

	objCIface = open( os.path.join( genDir, module.name + ".h" ), "wt" )
	objCImpl = open( os.path.join( genDir, module.name + ".m" ), "wt" )

	writeWarning( objCIface, None )
	writeWarning( objCImpl, None )

	writeObjCIfaceHeader( objCIface, module.name )
	writeObjCIfaceImports( objCIface, module.importedModuleNames )

	writeObjCImplHeader( objCImpl, module.name )			

	for genTypeKey in module.typeList.keys():
		writeAll = ( genTypeKey in module.structs )							
		writeOBJCTypeDeclaration( objCIface, module.typeList[genTypeKey], writeDump=writeAll, writeConstructors=writeAll )
		writeOBJCTypeImplementation( objCImpl, module.typeList[genTypeKey], writeDump=writeAll, writeConstructors=writeAll )

	if len( module.methods ) != 0:
		writeObjCIfaceDeclaration( objCIface, module.name )
		writeObjCImplDeclaration( objCImpl, module.name )
		objCIface.write("\n/* methods */\n\n")
		objCImpl.write("\n/* implementation */\n\n")	

	for method in module.methods:
		writeOBJCMethodDeclaration( objCIface, method, implementation = False )
		writeOBJCMethodImplementation( objCImpl, method )

	if len( module.methods ) != 0:
		writeObjCIfaceFooter( objCIface, module.name )
		writeObjCImplFooter( objCImpl, module.name )

	writeObjCFooter( objCImpl )

def main():
	parser = argparse.ArgumentParser(description='JSON-ObjC interface generator')
	
	parser.add_argument('rpcInput', metavar='I', type=unicode, nargs = '+', help = 'Input JSON RPC files')
	parser.add_argument('--prefix', action='store', required=False, help='Class and methods prefix')
	parser.add_argument('-o', '--outdir', action='store', default="gen-objc", required=False, help="Output directory name")

	parsedArgs = parser.parse_args()
	if len(sys.argv) == 1:
	    parser.print_help()
	    return 0

	try:
		for rpcInput in parsedArgs.rpcInput:
			processJSONIface( rpcInput, parsedArgs.prefix, parsedArgs.outdir )
	except Exception as ex:
		print( str(ex) )
		sys.exit(1)

	return 0

#########

if __name__ == "__main__":
	main()
	