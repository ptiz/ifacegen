# Created by Evgeny Kamyshanov on March, 2014
# Copyright (c) 2013-2014 BEFREE Ltd. 

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

from ifaceparser import *
import argparse
import sys
import types
import os
from collections import OrderedDict
from string import Template

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
	fileOut.write('- (instancetype)init')
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
	fileOut.write('- (instancetype)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error')
	if not implementation:
		fileOut.write(';\n')

def writeOBJCTypeInitDataDeclaration( fileOut, implementation ):
	fileOut.write('- (instancetype)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error')
	if not implementation:
		fileOut.write(';\n')

def writeOBJCTypeDeclarationCategory( fileOut, genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return
	
	fileOut.write("\n@interface " + genType.name + " (" + category + ")\n")

	fileOut.write('- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error;\n')
	fileOut.write('- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;\n')

	writeOBJCTypeInitDictDeclaration( fileOut, implementation = False )
	writeOBJCTypeInitDataDeclaration( fileOut, implementation = False )	

	fileOut.write("@end;\n");

def writeOBJCTypeDeclaration( fileOut, genType, baseOnly ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return
	
	if genType.baseType is not None:
		fileOut.write("\n@interface " + genType.name + ": " + genType.baseType.name + "\n")
	else:
		fileOut.write("\n@interface " + genType.name + ": NSObject\n")

	if not baseOnly:
		fileOut.write('- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error;\n')
		fileOut.write('- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;\n')

	writeOBJCTypeInitDeclaration( fileOut, genType, implementation = False )

	if not baseOnly:	
		writeOBJCTypeInitDictDeclaration( fileOut, implementation = False )
		writeOBJCTypeInitDataDeclaration( fileOut, implementation = False )	

	for fieldName in genType.fieldNames():
		fieldType = genType.fieldType(fieldName)
		if isinstance( fieldType, GenListType ):
			fileOut.write("@property (nonatomic) " + assumeOBJCType( fieldType ) + fieldType.ptr + '/*' + assumeOBJCType( fieldType.itemType ) + '*/' + " " + genType.fieldAlias( fieldName ) + ";\n")
		else:
			fileOut.write("@property (nonatomic) " + assumeOBJCType( fieldType ) + fieldType.ptr + " " + genType.fieldAlias(fieldName) + ";\n")
	fileOut.write("@end;\n");

def writeOBJCMethodDeclarationArguments( fileOut, formalType, argDecoration, prefix ):
	for argName in formalType.fieldNames():
		argType = formalType.fieldType(argName)
		argAlias = formalType.fieldAlias(argName)
		typeStr = assumeOBJCType( argType )
		fileOut.write( prefix + capitalizeFirstLetter( argAlias ) + ":(" + typeStr + argType.ptr + ")" + argAlias );
		prefix = argDecoration + "and"
	return prefix

def writeOBJCMethodDeclaration( fileOut, method, implementation ):
	argDecoration = " "

	argCount = 0
	if method.customRequestTypes is not None:
		argCount += len(method.customRequestTypes)
	if method.requestJsonType is not None:
		argCount += len(method.requestJsonType.fieldNames())

	if argCount > 1:
		argDecoration = "\n\t\t"

	if method.responseType is not None:
		if isinstance( method.responseType, GenListType ):
			fileOut.write("- (" + assumeOBJCType( method.responseType ) + method.responseType.ptr + '/*' + assumeOBJCType( method.responseType.itemType ) + '*/' + ")" + method.name )			
		else:		
			fileOut.write("- (" + assumeOBJCType( method.responseType ) + method.responseType.ptr + ")" + method.name )
	else:
		fileOut.write("- (void)" + method.name )
	
	pref = "With"

	if method.prefix is None:
		fileOut.write( pref + "Prefix:(NSString*)prefix")
		pref = argDecoration + "and"		

	for customRequestParamKey in method.customRequestTypes.keys():
		pref = writeOBJCMethodDeclarationArguments( fileOut, method.customRequestTypes[customRequestParamKey], argDecoration, pref )

	if method.requestJsonType is not None:
		pref = writeOBJCMethodDeclarationArguments( fileOut, method.requestJsonType, argDecoration, pref )

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
		return formatNSNumberStr.format( levelTmpVar, objcRetTypeStr, '0', 'NSNumber*', 'intValue' )
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

class ReturnedOBJCTypeContext:
	def __init__( self, fileOut, level, varCounter ):
		self.fileOut = fileOut
		self.level = level
		self.varCounter = varCounter

def unwindReturnedTypeToOBJC( objcDictName, outType, outArgName, tmpVarName, ctx, recursive=True ):

	if isinstance( outType, GenIntegralType ):
		if outArgName is None:
			#return ( decorateOBJCReturnedType( tmpVarName, objcDictName, outType ) ) #TODO: fix this strange 'objcDictName' behavior in case of lists unwind
			return objcDictName;
		else:
			return ( decorateOBJCReturnedType( tmpVarName, '[' + objcDictName +  ' objectForKey:@"' + outArgName + '"]', outType ) )

	if isinstance( outType, GenComplexType ):
		objCResType = assumeOBJCType( outType )
		currentDictName = objcDictName

		if not recursive:
			if outArgName is not None and outArgName != 'self':
				return ( '[[%s alloc] initWithDictionary:%s[@"%s"] error:error]' % (objCResType, currentDictName, outArgName) )
			else:
				return ( '[[%s alloc] initWithDictionary:%s error:error]' % (objCResType, currentDictName) )

		resName = '%s%d' % (outType.name, ctx.varCounter)
		ctx.varCounter += 1

		if outArgName is None or outArgName != 'self':
			ctx.fileOut.write('\t'*ctx.level + objCResType + outType.ptr + ' ' + resName + ';\n')
		else:		
			resName = 'self'

		if outArgName is not None and outArgName != 'self':
			currentDictName = '%s%s%d' % (objcDictName, capitalizeFirstLetter( outArgName ), ctx.varCounter)
			ctx.varCounter += 1
			ctx.fileOut.write('\t'*ctx.level + 'NSDictionary* ' + currentDictName + ' = [' + objcDictName + ' objectForKey:@"' + outArgName + '"];\n')
			ctx.fileOut.write('\t'*ctx.level + 'if ( ' + currentDictName + ' != nil && ![' + currentDictName + ' isEqual:[NSNull null]] && [' + currentDictName + ' isKindOfClass:NSDictionary.class]) {\n')
			ctx.level += 1
 			ctx.fileOut.write( '\t'*ctx.level + resName + ' = [' + objCResType + ' new];\n' )
 		elif outArgName != 'self':
 			ctx.fileOut.write( '\t'*ctx.level + resName + ' = [' + objCResType + ' new];\n' )

#TODO: uncomment after optional arguments appear
#			errMsg = '@"Can`t parse answer from server in ' + outArgName + '"'
#			fileOut.write('\tif ( ' + currentDictName + ' != nil ) {\n\t\tNSLog(' + errMsg +  ');\n')
#			fileOut.write('\t\t*error = [self errorWithMessage:' + errMsg + '];\n')
#			fileOut.write('\t\treturn nil;\n\t}\n')

		for fieldKey in outType.allFieldNames():
			outField = outType.fieldType(fieldKey)
			
			ctx.level += 1			
			value = unwindReturnedTypeToOBJC( currentDictName, outField, fieldKey, tmpVarName, ctx, recursive=False )
			ctx.fileOut.write('\t'*ctx.level + resName + '.' + outType.fieldAlias(fieldKey) + ' = ' + value + ';\n')
			ctx.level -= 1			

		if outArgName is not None and outArgName != 'self':
			ctx.fileOut.write('\t'*ctx.level + '}\n')

		return resName

	if isinstance( outType, GenListType ):
		if outArgName is None:
			currentArrayName = objcDictName
		else:
			currentArrayName = '%s%s%d' % (objcDictName, capitalizeFirstLetter( outArgName ), ctx.varCounter )
			ctx.varCounter += 1
			ctx.fileOut.write('\t'*ctx.level + 'NSArray* ' + currentArrayName + ' = [' + objcDictName + ' objectForKey:@"' + outArgName + '"];\n')

		objCResType = assumeOBJCType( outType )
		if outArgName is not None:
			resName = '%s%d' % ( outArgName, ctx.varCounter )
		else:
			resName = 'array%d' % ctx.varCounter
		ctx.varCounter += 1

		ctx.fileOut.write('\t'*ctx.level + 'NSMutableArray* ' + resName + ';\n')

		ctx.fileOut.write('\t'*ctx.level + 'if ( ' + currentArrayName + ' != nil && ![' + currentArrayName + ' isEqual:[NSNull null]] && [' + currentArrayName + ' isKindOfClass:NSArray.class]) {\n')
		ctx.level += 1

		ctx.fileOut.write('\t'*ctx.level + resName + ' = [NSMutableArray arrayWithCapacity:[' + currentArrayName + ' count]];\n')
		ctx.fileOut.write('\t'*ctx.level + 'for ( id item in ' + currentArrayName + ') {\n' )
		
		ctx.level += 1
		item = unwindReturnedTypeToOBJC( 'item', outType.itemType, None, tmpVarName, ctx, recursive=False )
		ctx.fileOut.write( '\t'*(ctx.level+1) + '[' + resName + ' addObject:' + item + '];\n' )
		ctx.fileOut.write('\t'*ctx.level + '}\n' )
		ctx.level -= 1

		ctx.fileOut.write('\t'*ctx.level + '}\n')
		ctx.level -= 1		

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

def unwindInputTypeToOBJC( fileOut, inputType, inputArgName, level, recursive=True ):
		if isinstance( inputType, GenIntegralType ):
			fileOut.write( decorateOBJCInputType( inputArgName, inputType ) )
	
		elif isinstance( inputType, GenComplexType ):
			if not recursive:
				fileOut.write( '[%s dictionaryWithError:error]' % inputArgName )
				return

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
				unwindInputTypeToOBJC( fileOut, fieldType, objcStatement, level+1, recursive=False )

			fileOut.write("\n" + '\t'*level + "}")

		elif isinstance( inputType, GenListType ):
			if isinstance( inputType.itemType, GenIntegralType ):
				fileOut.write( 'NULLABLE(' + inputArgName + ')' )
			else:
				fileOut.write('^NSArray*(NSArray* inArr) {\n' + '\t'*level + 'NSMutableArray* resArr = [NSMutableArray arrayWithCapacity:[inArr count]];\n')
				fileOut.write('\t'*level + '\tfor ( ' + assumeOBJCType(inputType.itemType) + inputType.itemType.ptr + ' inObj in inArr ) {\n' ) 
				fileOut.write('\t'*level + '\t\t[resArr addObject:')
				unwindInputTypeToOBJC( fileOut, inputType.itemType, 'inObj', level+2, recursive=False )
				fileOut.write( '];\n' + '\t'*level + '\t}\n' + '\t'*level + '\treturn resArr; } ( ' + inputArgName + ' )' )

def writeOBJCTypeImplementationMethods( fileOut, genType ):

	fileOut.write('- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error {')
	fileOut.write('\n\treturn ')
	unwindInputTypeToOBJC( fileOut, genType, 'self', 2 )
	fileOut.write(';\n}\n')

	fileOut.write("""- (NSData*)dumpWithError:(NSError* __autoreleasing*)error {
	NSDictionary* dict = [self dictionaryWithError:error];
	if (*error) return nil;
	else return [NSJSONSerialization dataWithJSONObject:[self dictionaryWithError:error] options:jsonFormatOption error:error];
}
""")

	fileOut.write('- (void)readDictionary:(NSDictionary*)dict withError:(NSError* __autoreleasing*)error {\n')
	fileOut.write('\tid tmp;\n')
	unwindReturnedTypeToOBJC( 'dict', genType, 'self', tmpVarName='tmp', ctx=ReturnedOBJCTypeContext( fileOut, level=0, varCounter=1) )
	fileOut.write('}\n')

	writeOBJCTypeInitDictDeclaration( fileOut, implementation = True )
	fileOut.write(""" {
	if ( dictionary == nil ) return nil;
	if (self = [super init]) {
		[self readDictionary:dictionary withError:error];
		if ( error && *error != nil ) self = nil;
	}
	return self;
}
""")
	
	writeOBJCTypeInitDataDeclaration( fileOut, implementation = True )
	fileOut.write(""" {
	if ( jsonData == nil ) return nil;
	if (self = [super init]) {
		NSDictionary* dict = [NSJSONSerialization JSONObjectWithData:jsonData options:NSJSONReadingAllowFragments error:error];
		if ( error && *error != nil ) { self = nil; return nil; }
		[self readDictionary:dict withError:error];
		if ( error && *error != nil ) self = nil;
	}
	return self;
}
""")

def writeOBJCTypeImplementation( fileOut, genType, baseOnly ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return

	fileOut.write('\n@implementation %s\n' % genType.name)

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

	if not baseOnly:
		writeOBJCTypeImplementationMethods( fileOut, genType )

	fileOut.write("@end\n")

def writeOBJCTypeImplementationCategory( fileOut, genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return
	fileOut.write('\n@implementation %s(%s)\n' % ( genType.name, category ))
	writeOBJCTypeImplementationMethods( fileOut, genType )
	fileOut.write("@end\n")

def getOBJCEmptyValueForType( emptyValueType ):
	if emptyValueType is None:
		return ''
	if isinstance( emptyValueType, GenListType ) or isinstance( emptyValueType, GenComplexType ):
		return 'nil'
	if emptyValueType.sType == "bool":
		return 'NO'
	if emptyValueType.sType == "int32" or emptyValueType.sType == "int64":
		return '0'
	if emptyValueType.sType == "double":
		return '0.0'
	return 'nil'	
			
def writeOBJCMethodCustomRequestParam( fileOut, customRequestParamName, customRequestParam ):
	paramSelectorName = makeAlias( 'set_' + customRequestParamName )
	fileOut.write('\tif (![transport respondsToSelector:@selector(' + paramSelectorName + ':)]) {\n\t\tassert("Transport does not respond to selector ' + paramSelectorName + ':");\n\t} ')
	fileOut.write('else {\n\t\t[transport performSelector:@selector(' + paramSelectorName + ':) withObject:')
	unwindInputTypeToOBJC( fileOut, customRequestParam, None, 3)
	fileOut.write('\n\t\t];\n\t}\n')

def writeOBJCMethodImplementation( fileOut, method ):

	emptyReturnString = '\t\treturn %s;\n\t}\n' % getOBJCEmptyValueForType(method.responseType)

	writeOBJCMethodDeclaration( fileOut, method, implementation = True )

	fileOut.write(" {\n")

	tmpVarName = "tmp"
	fileOut.write('\tid ' + tmpVarName + ';\n')

	for customRequestParamKey in method.customRequestTypes.keys():
		writeOBJCMethodCustomRequestParam( fileOut, customRequestParamKey, method.customRequestTypes[customRequestParamKey] )

	methodPrefix = "prefix"
	if method.prefix is not None:
		methodPrefix = '@"' + method.prefix + '"'

	if method.requestJsonType is not None:		
		fileOut.write("\tNSDictionary* inputDict = ")
		unwindInputTypeToOBJC( fileOut, method.requestJsonType, None, 2 )
		
		fileOut.write(";\n")

		fileOut.write("\tNSData* inputData = [NSJSONSerialization dataWithJSONObject:inputDict options:jsonFormatOption error:error];\n")
		fileOut.write('\tif ( ![transport writeAll:inputData prefix:' + methodPrefix + ' error:error] ) {\n')
	else:
		fileOut.write('\tif ( ![transport writeAll:nil prefix:' + methodPrefix + ' error:error] ) {\n')

	# fileOut.write('\t\tNSLog(@"' + method.name + ': server call failed, %@", *error);\n')

	if method.responseType is None:
		fileOut.write('\t\treturn;\n\t}\n')		
		fileOut.write('}\n')
		return
	else:
		fileOut.write( emptyReturnString )

	fileOut.write('\tNSData* outputData = [transport readAll];\n\tif ( outputData == nil ) {\n')
	fileOut.write( emptyReturnString )

	outputName = 'output'
	outputStatement = 'id ' + outputName

	fileOut.write('\t' + outputStatement + ' = [NSJSONSerialization JSONObjectWithData:outputData options:NSJSONReadingAllowFragments error:error];\n');
	fileOut.write('\tif ( error && *error != nil ) {\n' + emptyReturnString)

	retVal = unwindReturnedTypeToOBJC( outputName, method.responseType, method.responseArgName, tmpVarName, ReturnedOBJCTypeContext( fileOut, level=1, varCounter=1) )

	fileOut.write('\treturn ' + retVal + ';\n')	
	fileOut.write("}\n\n")

def writeObjCIfaceHeader( fileOut, inputName ):
	declaration = """
#import <Foundation/Foundation.h>
#import "IFTransport.h"
"""
	fileOut.write(declaration)

def writeObjCIfaceHeaderCategory( fileOut, inputName ):
	declaration = Template("""
#import "$inName.h"
""")
	fileOut.write(declaration.substitute(inName=inputName))

def writeObjCIfaceImports( fileOut, importNames ):
	for name in importNames:
		fileOut.write('#import "%s.h"\n' % name)

def writeObjCIfaceDeclaration( fileOut, inputName, baseOnly ):
	fileOut.write( '\n@interface %s: NSObject\n' % inputName )
	if not baseOnly:
		fileOut.write('- (instancetype)initWithTransport:(id<IFTransport>)transport NS_DESIGNATED_INITIALIZER;\n')

def writeObjCIfaceDeclarationCategory( fileOut, inputName, category ):
	fileOut.write( '\n@interface %s (%s)\n' % (inputName, category) )

def writeObjCIfaceFooter( fileOut, inputName ):
	fileOut.write("\n@end")

def writeObjCImplHeader( fileOut, inputName, baseOnly ):
	fileOut.write( '#import "%s.h"\n\n' % inputName )
	if baseOnly: 
		return

	declaration = """\
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused"
#pragma clang diagnostic ignored "-Wundeclared-selector"

#define NULLABLE( s ) (s == nil ? [NSNull null] : s)
static const NSUInteger jsonFormatOption = 
#ifdef DEBUG
	NSJSONWritingPrettyPrinted;
#else
	0;
#endif

"""
	fileOut.write( declaration )

def writeObjCImplDeclaration( fileOut, inputName ):
	declaration = Template("""
@interface $inName() {
	id<IFTransport> transport;
}
@end

@implementation $inName
- (instancetype)initWithTransport:(id<IFTransport>)trans {
	if ( self = [super init] ) {
		transport = trans;
	}
	return self;
}
- (NSError*)errorWithMessage:(NSString*)msg {
	return [NSError errorWithDomain:NSStringFromClass([self class]) code:0 userInfo:@{NSLocalizedDescriptionKey: msg}];
}
""")
	fileOut.write(declaration.substitute(inName=inputName))

def writeObjCImplFooter( fileOut, inputName ):
	fileOut.write("\n@end")	

def writeObjCFooter( fileOut ):
	fileOut.write('\n#pragma clang diagnostic pop\n')

def writeWarning( fileOut, inputName ):
	declaration = """\
/**
 * @generated
 *
 * AUTOGENERATED. DO NOT EDIT! 
 *
 */

"""
	fileOut.write(declaration)

def findDependenciesUnresolved( typeSet, typeToCheck ):
	unresolved = []
	if isinstance( typeToCheck, GenComplexType ):
		for fieldName in typeToCheck.allFieldNames():
			fieldType = typeToCheck.fieldType(fieldName)
			if isinstance( fieldType, GenComplexType ) and ( fieldType.name not in typeSet ):
				unresolved.append( fieldType )
	return unresolved

def writeObjCForwardingDeclaration( fileOut, forwardingType ):
	fileOut.write('\n@class ' + forwardingType.name + ';\n')

def writeObjCImplementation( genDir, category, module ):

	if not os.path.exists( genDir ):
	    os.makedirs( genDir )

	objCIface = open( os.path.join( genDir, module.name + ".h" ), "wt" )
	objCImpl = open( os.path.join( genDir, module.name + ".m" ), "wt" )
	
	if category is not None:
		objCIfaceCategory = open( os.path.join( genDir, '%s+%s.h' % (module.name, category) ), "wt" )
		objCImplCategory = open( os.path.join( genDir, '%s+%s.m' % (module.name, category) ), "wt" )

	writeWarning( objCIface, None )
	writeWarning( objCImpl, None )

	if category is not None:
		writeWarning( objCIfaceCategory, None )
		writeWarning( objCImplCategory, None )

	writeObjCIfaceHeader( objCIface, module.name )
	writeObjCIfaceImports( objCIface, module.importedModuleNames )
	writeObjCImplHeader( objCImpl, module.name, baseOnly = (category is not None) )

	if category is not None:
		writeObjCIfaceHeaderCategory( objCIfaceCategory, module.name )
		writeObjCImplHeader( objCImplCategory, '%s+%s' % (module.name, category), baseOnly = False )

	alreadyDeclaredTypes = set( module.importedTypeList.keys() )
	for genTypeName in module.typeList.keys():
		alreadyDeclaredTypes.add( genTypeName )
		currentType = module.typeList[genTypeName]
		for forwardingType in findDependenciesUnresolved( alreadyDeclaredTypes, currentType):
			writeObjCForwardingDeclaration( objCIface, forwardingType )
		writeOBJCTypeDeclaration( objCIface, currentType, baseOnly = (category is not None) )
		writeOBJCTypeImplementation( objCImpl, currentType, baseOnly = (category is not None) )		
		if category is not None:
			writeOBJCTypeDeclarationCategory( objCIfaceCategory, currentType, category )
			writeOBJCTypeImplementationCategory( objCImplCategory, currentType, category )

	if len( module.methods ) == 0:
		writeObjCFooter( objCImpl )
		return

	writeObjCIfaceDeclaration( objCIface, module.name, baseOnly = (category is not None) )
	if category is not None:
		writeObjCIfaceDeclarationCategory( objCIfaceCategory, module.name, category )
	else:
		writeObjCImplDeclaration( objCImpl, module.name )

	for method in module.methods:
		writeOBJCMethodDeclaration( objCIface, method, implementation = False )
		writeOBJCMethodImplementation( objCImpl, method )

	writeObjCIfaceFooter( objCIface, module.name )
	writeObjCImplFooter( objCImpl, module.name )

	writeObjCFooter( objCImpl )

