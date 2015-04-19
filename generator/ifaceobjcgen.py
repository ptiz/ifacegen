# Created by Evgeny Kamyshanov on Feb-Mar, 2015
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

from ifaceparser import *
import argparse
import sys
import types
import os
from collections import OrderedDict
from string import Template

def OBJCAssumeType( genType ):
	if isinstance( genType, GenIntegralType ):
		t = genType.sType
		integralTypeMap = { "string": "NSString", "bool": "BOOL", "int32": "int32_t", "int64": "int64_t", "double": "double_t", "raw": "NSDictionary", "rawstr": "NSDictionary" }
		if t in integralTypeMap:
			return integralTypeMap[t]
	if isinstance( genType, GenComplexType ):
		return genType.name
	if isinstance( genType, GenListType ):
		return 'NSArray';
	return "_ERROR_"

def OBJCHTTPEnumFromName( httpMethodName ):
	httpMethodMap = { "get": "IFHTTPMETHOD_GET", "head": "IFHTTPMETHOD_HEAD", "post": "IFHTTPMETHOD_POST", "put": "IFHTTPMETHOD_PUT", "delete": "IFHTTPMETHOD_DELETE" }
	if httpMethodName in httpMethodMap:
		return httpMethodMap[httpMethodName]
	return "_ERROR_"

def OBJCDecorateTypeForDict( objcTypeStr, genType ):
	template = Template('($objcTypeStr == nil ? [NSNull null] : $objcTypeStr)')
	if genType.sType == 'bool' or genType.sType == 'int32' or genType.sType == 'int64' or genType.sType == 'double':
		template = Template('@($objcTypeStr)')
	if genType.sType == 'rawstr':
		template = Template('[[NSString alloc] initWithData:[NSJSONSerialization dataWithJSONObject:$objcTypeStr options:jsonFormatOption error:error] encoding:NSUTF8StringEncoding]')
	return template.substitute( objcTypeStr=objcTypeStr )

def OBJCDecorateTypeFromJSON( genType, varValue ):
	templateNSNumberStr = Template('( tmp = $tmpVarValue, [tmp isEqual:[NSNull null]] ? $emptyVal : ((NSNumber*)tmp).$selector )')
	templateNSStringStr = Template('( tmp = $tmpVarValue, [tmp isEqual:[NSNull null]] ? nil : (NSString*)tmp )')
	templateNSDictionaryStr = Template('( tmp = $tmpVarValue, [tmp isEqual:[NSNull null]] ? nil : (NSDictionary*)tmp )')
	templateNSArrayStr = Template('( tmp = $tmpVarValue, [tmp isEqual:[NSNull null]] ? nil : (NSArray*)tmp )')
	templateRawNSDictionaryStr = Template('( tmp = $tmpVarValue, [tmp isEqual:[NSNull null]] ? nil : [NSJSONSerialization JSONObjectWithData:[(NSString*)tmp dataUsingEncoding:NSUTF8StringEncoding] options:NSJSONReadingAllowFragments error:&error] )')
	if isinstance( genType, GenListType ):
		return templateNSArrayStr.substitute( tmpVarValue=varValue )
	if not isinstance( genType, GenIntegralType ):
		return "ERROR"
	if genType.sType == "bool":
		return templateNSNumberStr.substitute( tmpVarValue=varValue, emptyVal='NO', selector='boolValue' )
	if genType.sType == "int32":
		return templateNSNumberStr.substitute( tmpVarValue=varValue, emptyVal='0', selector='intValue' )
	if genType.sType == "int64":
		return templateNSNumberStr.substitute( tmpVarValue=varValue, emptyVal='0L', selector='longLongValue' )
	if genType.sType == "double":
		return templateNSNumberStr.substitute( tmpVarValue=varValue, emptyVal='0.0', selector='doubleValue' )
	if genType.sType == "string":
		return templateNSStringStr.substitute( tmpVarValue=varValue )
	if genType.sType == "raw":
		return templateNSDictionaryStr.substitute( tmpVarValue=varValue )
	if genType.sType == "rawstr":
		return templateRawNSDictionaryStr.substitute( tmpVarValue=varValue )
	return "ERROR";

def OBJCEmptyValForType( genType ):
	if isinstance( genType, GenIntegralType ) and genType.sType == "bool":
		return 'NO'
	if len(genType.ptr) == 0:
		return '0'
	return 'nil'

def OBJCAppendIfNotEmpty( list, strItem ):
	if strItem is not None and len(strItem) > 0:
		list.append( strItem )

def isModuleDependsOnHTTPTransport( module ):
	for method in module.methods:
		if method.httpMethod is not None:
			return True
	return False

############################
# Header declaration
############################

def OBJCArgList( genType ):
	template = Template('$arg:($argType$argTypePtr)$argAlias')
	argList = []
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		argList.append( template.substitute( arg=capitalizeFirstLetter(fieldAlias), argType=OBJCAssumeType(fieldType), argTypePtr=fieldType.ptr, argAlias=fieldAlias ) )
	return '\n\tand'.join(argList)

def OBJCTypeInitDeclaration( genType ):
	return Template('- (instancetype)initWith$argList').substitute( argList=OBJCArgList( genType ) )

def OBJCTypeSerializersDeclarationList( genType ):
	return """\
- (instancetype)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error;
- (instancetype)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error;
- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error;
- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;"""

def OBJCTypePropertyList( genType ):
	template = Template('@property (nonatomic) $propType$propTypePtr $propAlias;')
	listTemplate = Template('@property (nonatomic) $propType$propTypePtr/*$itemType*/ $propAlias;')
	propList = []
	for fieldName in genType.fieldNames():
		fieldType = genType.fieldType(fieldName)
		if isinstance( fieldType, GenListType ):
			propList.append( listTemplate.substitute(propType=OBJCAssumeType( fieldType ), propTypePtr=fieldType.ptr, itemType=OBJCAssumeType( fieldType.itemType ), propAlias=genType.fieldAlias( fieldName )) )
		else:
			propList.append( template.substitute(propType=OBJCAssumeType( fieldType ), propTypePtr=fieldType.ptr, propAlias=genType.fieldAlias( fieldName )) )
	return '\n'.join(propList)

def OBJCTypeDeclaration( genType, serializersListGenerator ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	
	baseTypeName = 'NSObject'
	if genType.baseType is not None:
		baseTypeName = genType.baseType.name

	template = Template("""\
@interface $typeName: $baseTypeName
$init;
$serializers
$properties
@end
""")

	return template.substitute(typeName=genType.name, baseTypeName=baseTypeName, init=OBJCTypeInitDeclaration( genType ), serializers=serializersListGenerator( genType ), properties=OBJCTypePropertyList( genType ))

def OBJCCategoryTypeDeclaration( genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''

	template = Template("""\
@interface $typeName($category)
$serializers
@end
""")
	return template.substitute( typeName=genType.name, category=category, serializers=OBJCTypeSerializersDeclarationList( genType ) )

def OBJCTypeForwardingDeclaration( genType ):
	return '@class %s;\n' % genType.name;

def OBJCImportList( module ):
	template = Template('#import "$modImport.h"\n')
	importList = ''
	for name in module.importedModuleNames:
		importList += template.substitute(modImport=name)
	return importList

def OBJCFindDependenciesUnresolved( typeSet, typeToCheck ):
	unresolved = []
	if isinstance( typeToCheck, GenComplexType ):
		for fieldName in typeToCheck.allFieldNames():
			fieldType = typeToCheck.fieldType(fieldName)
			if isinstance( fieldType, GenComplexType ) and ( fieldType.name not in typeSet ):
				unresolved.append( fieldType )
	return unresolved

def OBJCTypeDeclarationList( module, serializersListGenerator ):
	declList = []
	alreadyDeclaredTypes = set( module.importedTypeList.keys() )
	for genTypeName in module.typeList.keys():
		currentType = module.typeList[genTypeName]
		alreadyDeclaredTypes.add( genTypeName )
		for forwardingType in OBJCFindDependenciesUnresolved( alreadyDeclaredTypes, currentType ):
			declList.append( OBJCTypeForwardingDeclaration( forwardingType ) )
		OBJCAppendIfNotEmpty( declList, OBJCTypeDeclaration( currentType, serializersListGenerator ) )
	return '\n'.join( declList )

def OBJCCategoryTypeDeclarationList( module, category ):
	declList = []
	for genTypeName in module.typeList.keys():
		currentType = module.typeList[genTypeName]
		OBJCAppendIfNotEmpty( declList, OBJCCategoryTypeDeclaration( currentType, category ) )
	return '\n'.join( declList )

#TODO: make a column if there are more than 2 args in the declaration
def OBJCRPCMethodDeclaration( method ):
	template = Template('- ($responseType)${methodName}With$argList')
	argList = []

	if method.prefix is None:
		argList.append('Prefix:(NSString*)prefix')
	for customRequestType in method.customRequestTypes.values():
		argList.append( OBJCArgList( customRequestType ) )
	if method.requestJsonType is not None:
		argList.append( OBJCArgList( method.requestJsonType ) )

	argList.append('Error:(NSError* __autoreleasing*)error')

	argListStr = '\n\tand'.join(argList)

	responseType = 'void'
	if method.responseType is not None:
		responseType = "%s%s" % ( OBJCAssumeType(method.responseType), method.responseType.ptr )

	return template.substitute( responseType=responseType, methodName=method.name, argList=argListStr )

def OBJCRPCMethodList( module ):
	methodList = []
	for method in module.methods:
		methodList.append( OBJCRPCMethodDeclaration( method ) )
	return ';\n'.join(methodList)

def OBCRPCDeclaration( module ):
	if len(module.methods) == 0:
		return ''

	template = Template("""\
@interface $rpcClientName: IFServiceClient
$methods;
@end
""")
	return template.substitute( rpcClientName=module.name, methods=OBJCRPCMethodList( module ) )

OBJCGeneratedWarning = """\
/**
 * @generated
 *
 * AUTOGENERATED. DO NOT EDIT! 
 *
 */"""

OBJCHeaderIFImports = """\
#import "IFServiceClient.h"
"""
OBJCHeaderTemplate = Template("""\
$generatedWarning

#import <Foundation/Foundation.h>
$IFImportList$importList
$typeDeclarationList
$rpcDeclaration
""")

def OBJCHeader( module ):
	return OBJCHeaderTemplate.substitute( generatedWarning=OBJCGeneratedWarning, IFImportList=OBJCHeaderIFImports, importList=OBJCImportList( module ), typeDeclarationList=OBJCTypeDeclarationList( module, OBJCTypeSerializersDeclarationList ), rpcDeclaration=OBCRPCDeclaration( module ) )

def OBJCHeaderForCategory( module ):
	return OBJCHeaderTemplate.substitute( generatedWarning=OBJCGeneratedWarning, IFImportList='', importList=OBJCImportList( module ), typeDeclarationList=OBJCTypeDeclarationList( module, lambda genType: '' ),  rpcDeclaration='' )

def OBJCCategoryHeader( module, category ):
	template = Template("""\
$generatedWarning

#import "$moduleName.h"

$typeDeclarationList
""")
	return template.substitute( generatedWarning=OBJCGeneratedWarning, moduleName=module.name, typeDeclarationList=OBJCCategoryTypeDeclarationList( module, category ) )

############################
# Implementation module
############################

def OBJCTypeFieldInitList( genType ):
	template = Template('\t\t_$fieldAlias = $fieldAlias;')
	fieldList = []
	for fieldName in genType.fieldNames():
		field = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		fieldList.append( template.substitute( fieldAlias=fieldAlias ) )
	return '\n'.join( fieldList )

def OBJCTypeMethodActualArgList( genType ):
	argList = []
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType( fieldName )
		fieldAlias = genType.fieldAlias( fieldName )
		argList.append( '%s:%s' % ( capitalizeFirstLetter( fieldAlias ), fieldAlias ) )
	return '\n\t\t\t\t\t\tand'.join( argList )

def OBJCTypeInitImplList( genType ):
	baseTemplate = Template("""
$declaration {
	if (self=[super init]) {
$fieldInitList
	}
	return self;
}""")

	superTemplate = Template("""
$declaration {
	if (self = [super initWith$actualArgList]) {
$fieldInitList
	}
	return self;
}""")
	if genType.baseType is not None:
		return superTemplate.substitute( declaration=OBJCTypeInitDeclaration( genType ), actualArgList=OBJCTypeMethodActualArgList( genType.baseType ), fieldInitList=OBJCTypeFieldInitList( genType ) )
	return baseTemplate.substitute( declaration=OBJCTypeInitDeclaration( genType ), fieldInitList=OBJCTypeFieldInitList( genType ) )

def OBJCUnwindTypeToDict( genType, objcArgName, level, recursive=True ):
	if isinstance( genType, GenIntegralType ):
		return OBJCDecorateTypeForDict( objcArgName, genType )

	elif isinstance( genType, GenComplexType ):
		if not recursive:
			return '[%s dictionaryWithError:error]' % objcArgName

		fieldTemplate = Template('$tabLevel@"$argName":$argValue')
		fieldList = []

		for argName in genType.allFieldNames():
			fieldType = genType.fieldType(argName)
			objcStatement = genType.fieldAlias(argName)
			if objcArgName is not None:
				objcStatement = '%s.%s' % ( objcArgName, genType.fieldAlias(argName) )
			fieldList.append( fieldTemplate.substitute( tabLevel='\t'*level, argName=argName, argValue=OBJCUnwindTypeToDict( fieldType, objcStatement, level+1, recursive=False ) ) )

		return Template('@{\n$fieldList\n$tabLevel}').substitute( fieldList=',\n'.join(fieldList), tabLevel='\t'*(level-1) )

	elif isinstance( genType, GenListType ):
		if isinstance( genType.itemType, GenIntegralType ):
			return Template('($objcArgName == nil ? [NSNull null] : $objcArgName)').substitute(objcArgName=objcArgName)
		else:
			arrayTemplate = Template("""\
^NSArray*(NSArray* inArr) {
${tabLevel}NSMutableArray* resArr = [NSMutableArray arrayWithCapacity:[inArr count]];
${tabLevel}for($objcType$objcTypePtr inObj in inArr) { [resArr addObject:$argValue]; }
${tabLevel}return resArr; } ($objcArgName)""")
			return arrayTemplate.substitute( tabLevel='\t'*level, objcType=OBJCAssumeType(genType.itemType), objcTypePtr=genType.itemType.ptr, argValue=OBJCUnwindTypeToDict( genType.itemType, 'inObj', level+2, recursive=False ), objcArgName=objcArgName )

def OBJCListTypeFromDictionary( genType, objcDataGetter, level ):
	listTypeTemplate = Template("""\
^NSArray*(id inObj) {
${tabLevel}\tNSMutableArray* items;
${tabLevel}\tif ( inObj == nil ||  [inObj isEqual:[NSNull null]] || ![inObj isKindOfClass:NSArray.class]) return nil;
${tabLevel}\tNSArray* inArr = (NSArray*)inObj;
${tabLevel}\titems = [NSMutableArray arrayWithCapacity:inArr.count];
${tabLevel}\tfor ( id item in inArr ) { id tmp; [items addObject:$itemObj]; }
${tabLevel}\treturn items;
${tabLevel}}( $objcDataGetter )""")
	return listTypeTemplate.substitute( tabLevel='\t'*level, itemObj=OBJCTypeFromDictionary(genType.itemType, "item", level+1 ), objcDataGetter=objcDataGetter )

def OBJCTypeFromDictionary( genType, objcDataGetter, level ):
	complexTypeTemplate = Template('[[$typeName alloc] initWithDictionary:$objcDataGetter error:error]')
	if isinstance( genType, GenIntegralType ):
		return OBJCDecorateTypeFromJSON( genType, objcDataGetter )
	if isinstance( genType, GenComplexType ):
		return complexTypeTemplate.substitute( typeName=genType.name, objcDataGetter=objcDataGetter )
	if isinstance( genType, GenListType ):
		if isinstance(genType.itemType, GenIntegralType):
			return OBJCDecorateTypeFromJSON( genType, objcDataGetter )
		else:
			return OBJCListTypeFromDictionary( genType, objcDataGetter, level+1 )

def OBJCComplexTypeFieldListFromDictionary( genType, objcDictArgName ):
	template = Template('\tself.$argName = $value')
	fieldList = []
	#here we init all the fields available, including ancestor's ones instead of calling non-public "[super readDictionary]" method
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		objcDataGetter = '%s[@"%s"]' % ( objcDictArgName, fieldName )
		fieldList.append( template.substitute( argName=genType.fieldAlias(fieldName), value=OBJCTypeFromDictionary( fieldType, objcDataGetter, 1 ) ) )
	return ';\n'.join( fieldList )

def OBJCTypeSerializationImplList( genType ):
	template = Template("""
- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error {
	return $typeDictionary;
}

- (NSData*)dumpWithError:(NSError* __autoreleasing*)error {
	NSDictionary* dict = [self dictionaryWithError:error];
	if (*error) return nil;
	else return [NSJSONSerialization dataWithJSONObject:[self dictionaryWithError:error] options:jsonFormatOption error:error];
}

- (void)readDictionary:(NSDictionary*)dict withError:(NSError* __autoreleasing*)error {
	id tmp;
$complexTypeFieldsFromDictionary;
}

- (instancetype)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error {
	if ( dictionary == nil ) return nil;
	if (self = [super init]) {
		[self readDictionary:dictionary withError:error];
		if ( error && *error != nil ) self = nil;
	}
	return self;
}

- (instancetype)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error {
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
	
	return template.substitute( typeDictionary=OBJCUnwindTypeToDict( genType, 'self', 2 ), complexTypeFieldsFromDictionary=OBJCComplexTypeFieldListFromDictionary( genType,'dict' ) )
	
def OBJCTypeImplementation( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
@implementation $typeName
$initImplList
$serializationImplList
@end
""")
	return template.substitute( typeName=genType.name, initImplList=OBJCTypeInitImplList(genType), serializationImplList=OBJCTypeSerializationImplList(genType) )

def OBJCTypeImplementationForCategory( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
@implementation $typeName
$initImplList
@end
""")
	return template.substitute( typeName=genType.name, initImplList=OBJCTypeInitImplList(genType) )

def OBJCCategoryTypeImplementation( genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
@implementation $typeName($category)
$serializationImplList
@end
""")
	return template.substitute( typeName=genType.name, category=category, serializationImplList=OBJCTypeSerializationImplList(genType) )	

def OBJCTypeImplementationList( module, implGenerator ):
	implList = []
	for genTypeName in module.typeList.keys():
		currentType = module.typeList[genTypeName]
		OBJCAppendIfNotEmpty( implList, implGenerator( currentType ) )
	return '\n'.join( implList )

def OBJCRPCMethodImplementation( method ):
	jsonArgsTemplate = Template('[NSJSONSerialization dataWithJSONObject:$jsonArgDict options:jsonFormatOption error:error]')
	customArgsTemplate = Template("""\
	if (![self.transport respondsToSelector:@selector($customArgSectionName:)]) {
		assert("Transport does not respond to selector $customArgSectionName:");
	} else {
		[self.transport performSelector:@selector($customArgSectionName:) withObject:$customArgDict];
	}
""")
	returnTemplate = Template('return $response;')

	transportMethodTemplate = Template('[self.transport writeAll:jsonData prefix:$prefix error:error]')
	transportHTTPMethodTemplate = Template('[(IFHTTPTransport*)self.transport writeAll:jsonData prefix:$prefix method:$httpMethod error:error]')

	template = Template("""\
$declaration {
	id tmp;
$setCustomArgs
	NSData* jsonData = $jsonData;
	if ( !$transportMethod ) {
		return$emptyVal;
	}
	NSData* outputData = [self.transport readAll];
	if ( outputData == nil ) {
		return$emptyVal;
	}
	id output = [NSJSONSerialization JSONObjectWithData:outputData options:NSJSONReadingAllowFragments error:error];
	if ( error && *error != nil ) {
		return$emptyVal;
	}
	$returnStr
}
""")

	customArgsList = []
	for customRequestTypeKey in method.customRequestTypes.keys():
		customRequestType = method.customRequestTypes[customRequestTypeKey]
		customArgsList.append( customArgsTemplate.substitute( customArgSectionName=makeAlias('set_' + customRequestTypeKey), customArgDict=OBJCUnwindTypeToDict( customRequestType, None, 3 ) ) )
	setCustomArgs = '\n'.join(customArgsList)

	jsonData='nil'
	if method.requestJsonType is not None:
		jsonData = jsonArgsTemplate.substitute( jsonArgDict=OBJCUnwindTypeToDict( method.requestJsonType, None, level=2 ) )	

	prefix = 'prefix'
	if method.prefix is not None:
		prefix = '@"%s"' % (method.prefix)

	transportMethod = transportMethodTemplate.substitute(prefix=prefix)
	if method.httpMethod is not None:
		transportMethod = transportHTTPMethodTemplate.substitute(prefix=prefix, httpMethod=OBJCHTTPEnumFromName(method.httpMethod))

	returnStr = ''
	emptyVal = ''
	if method.responseType is not None:
		returnStr = returnTemplate.substitute( response=OBJCTypeFromDictionary( method.responseType, 'output', level=2 ) )
		emptyVal = ' ' + OBJCEmptyValForType( method.responseType )

	return template.substitute( declaration=OBJCRPCMethodDeclaration( method ), setCustomArgs=setCustomArgs, jsonData=jsonData, transportMethod=transportMethod, returnStr=returnStr, emptyVal=emptyVal )

def OBJCRPCImplementation( module ):
	if len(module.methods) == 0:
		return ''

	template = Template("""\
@implementation $moduleName
$rpcMethodImplementationsList
@end
""")

	methodList = []
	for method in module.methods:
		methodList.append( OBJCRPCMethodImplementation( method ) )

	return template.substitute( moduleName=module.name, rpcMethodImplementationsList='\n'.join( methodList ) )

OBJCImplementationPreamble = """\
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused"
#pragma clang diagnostic ignored "-Wundeclared-selector"

static const NSUInteger jsonFormatOption = 
#ifdef DEBUG
	NSJSONWritingPrettyPrinted;
#else
	0;
#endif"""

OBJCImplementationConclusion = """\
#pragma clang diagnostic pop
"""

transportImportListTemplate = Template("""\
#import "$modHeader.h"
#import "IFServiceClient+Protected.h" """)

transportHTTPImportListTemplate = Template("""\
#import "$modHeader.h"
#import "IFHTTPTransport.h"
#import "IFServiceClient+Protected.h" """)

def OBJCModule( module ):
	template = Template("""\
$generatedWarning

$importList

$preamble

$typeImplementationList

$rpcImplementation

$conclusion
""")

	importList = transportImportListTemplate.substitute( modHeader=module.name )
	if isModuleDependsOnHTTPTransport( module ):
		importList = transportHTTPImportListTemplate.substitute( modHeader=module.name )
	return template.substitute(generatedWarning=OBJCGeneratedWarning, importList=importList, preamble=OBJCImplementationPreamble, typeImplementationList=OBJCTypeImplementationList( module, OBJCTypeImplementation ), rpcImplementation=OBJCRPCImplementation( module ), conclusion=OBJCImplementationConclusion)

def OBJCModuleForCategory( module ):
	template = Template("""\
$generatedWarning

#import "$modHeader.h"

$typeImplementationList
""")
	return template.substitute(generatedWarning=OBJCGeneratedWarning, modHeader=module.name, typeImplementationList=OBJCTypeImplementationList( module, OBJCTypeImplementationForCategory ))

def OBJCategory( module, category ):
	template = Template("""\
$generatedWarning

#import "$moduleName+$category.h"

$preamble

$typeImplementationList

$conclusion
""")
	return template.substitute(generatedWarning=OBJCGeneratedWarning, moduleName=module.name, category=category, preamble=OBJCImplementationPreamble, typeImplementationList=OBJCTypeImplementationList( module, lambda genType: OBJCCategoryTypeImplementation( genType, category ) ), conclusion=OBJCImplementationConclusion)

############################
# Entry point
############################

def writeObjCImplementationMonolith( genDir, module ):
	objCIface = open( os.path.join( genDir, module.name + ".h" ), "wt" )
	objCImpl = open( os.path.join( genDir, module.name + ".m" ), "wt" )

	objCIface.write( OBJCHeader( module ) )
	objCImpl.write( OBJCModule( module ) )

def writeObjCImplementationCategory( genDir, category, module ):
	objCIface = open( os.path.join( genDir, module.name + ".h" ), "wt" )
	objCImpl = open( os.path.join( genDir, module.name + ".m" ), "wt" )
	objCIfaceCategory = open( os.path.join( genDir, module.name + "+" + category + ".h" ), "wt" )
	objCImplCategory = open( os.path.join( genDir, module.name + "+" + category + ".m" ), "wt" )

	objCIface.write( OBJCHeaderForCategory( module ) )
	objCImpl.write( OBJCModuleForCategory( module ) )
	objCIfaceCategory.write( OBJCCategoryHeader( module, category ) )
	objCImplCategory.write( OBJCategory( module, category ) )

def writeObjCImplementation( genDir, category, module ):

	if not os.path.exists( genDir ):
	    os.makedirs( genDir )

	if category is not None and len(category) > 0:
		writeObjCImplementationCategory( genDir, category, module )
	else:
		writeObjCImplementationMonolith( genDir, module )


