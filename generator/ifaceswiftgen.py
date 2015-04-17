# Created by Anton Davydov on Apr, 2015
# Copyright (c) 2014-2015 Anton Davydov

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

def SwiftAssumeType( genType ):
	if isinstance( genType, GenIntegralType ):
		t = genType.sType
		integralTypeMap = { "string": "String", "bool": "Bool", "int32": "Int32", "int64": "Int64", "double": "Double", "raw": "Dictionary<String, Any>", "rawstr": "Dictionary<String, Any>" }
		if t in integralTypeMap:
			return integralTypeMap[t]
	if isinstance( genType, GenComplexType ):
		return genType.name
	if isinstance( genType, GenListType ):
		return 'Array<%s>' % SwiftAssumeType(genType.itemType)
	return "_ERROR_"

def SwiftDecorateTypeForDict( objcTypeStr, genType ):
	template = Template('($objcTypeStr == nil ? NSNull() : $objcTypeStr)')
	if genType.sType == 'bool' or genType.sType == 'int32' or genType.sType == 'int64' or genType.sType == 'double':
		template = Template('$objcTypeStr')
	if genType.sType == 'rawstr':
		template = Template('NSString(data: NSJSONSerialization.dataWithJSONObject($objcTypeStr, options: jsonFormatOption, error: error), encoding: NSUTF8StringEncoding)')
	return template.substitute( objcTypeStr=objcTypeStr )

def SwiftDecorateTypeFromJSON( genType, varValue ):
	templateNSNumberStr = Template('($tmpVarValue as? NSNumber)?.$selector')
	templateNSStringStr = Template('$tmpVarValue as? String')
	templateNSDictionaryStr = Template('$tmpVarValue as? NSDictionary')
	templateNSArrayStr = Template('$tmpVarValue as? NSArray )')
	templateRawNSDictionaryStr = Template(' $tmpVarValue as? NSJSONSerialization.JSONObjectWithData:((tmp as? String)?.dataUsingEncoding(NSUTF8StringEncoding), options: NSJSONReadingAllowFragments, error: &error)')
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

def SwiftEmptyValForType( genType ):
	if isinstance( genType, GenIntegralType ) and genType.sType == "bool":
		return 'NO'
	if len(genType.ptr) == 0:
		return '0'
	return 'nil'

def SwiftAppendIfNotEmpty( list, strItem ):
	if strItem is not None and len(strItem) > 0:
		list.append( strItem )

############################
# Header declaration
############################

def SwiftArgList( genType ):
	template = Template('$argAlias: $argType')
	argList = []
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		argList.append( template.substitute( argAlias=fieldAlias, argType=SwiftAssumeType(fieldType) ) )
	return ', \n\t\t'.join(argList)

def SwiftTypeInitDeclaration( genType ):
	return Template('\tinit($argList)').substitute( argList=SwiftArgList(genType))

def SwiftTypePropertyList( genType ):
	template = Template('\tvar $propAlias: $propType! ')
	listTemplate = Template('\tvar $propAlias: $propType! ')
	propList = []
	for fieldName in genType.fieldNames():
		fieldType = genType.fieldType(fieldName)
		if isinstance( fieldType, GenListType ):
			propList.append( listTemplate.substitute(propType=SwiftAssumeType(fieldType), propAlias=genType.fieldAlias( fieldName )) )
		else:
			propList.append( template.substitute(propType=SwiftAssumeType(fieldType), propAlias=genType.fieldAlias( fieldName )) )
	return '\n'.join(propList)

def SwiftTypeForwardingDeclaration( genType ):
	return '@class %s;\n' % genType.name;

def SwiftImportList( module ):
	template = Template('#import "$modImport.h"\n')
	importList = ''
	for name in module.importedModuleNames:
		importList += template.substitute(modImport=name)
	return importList

def SwiftFindDependenciesUnresolved( typeSet, typeToCheck ):
	unresolved = []
	if isinstance( typeToCheck, GenComplexType ):
		for fieldName in typeToCheck.allFieldNames():
			fieldType = typeToCheck.fieldType(fieldName)
			if isinstance( fieldType, GenComplexType ) and ( fieldType.name not in typeSet ):
				unresolved.append( fieldType )
	return unresolved


#TODO: make a column if there are more than 2 args in the declaration
def SwiftRPCMethodDeclaration( method ):
	template = Template('func ${methodName}With$argList -> $responseType')
	argList = []

	if method.prefix is None:
		argList.append('Prefix:(NSString*)prefix')
	for customRequestType in method.customRequestTypes.values():
		argList.append(SwiftArgList(customRequestType))
	if method.requestJsonType is not None:
		argList.append(SwiftArgList(method.requestJsonType))

	argList.append('error: NSError!')

	argListStr = ', \n\t'.join(argList)

	responseType = 'void'
	if method.responseType is not None:
		responseType = "%s" % ( SwiftAssumeType(method.responseType) )

	return template.substitute( responseType=responseType, methodName=method.name, argList=argListStr )

def SwiftRPCMethodList( module ):
	methodList = []
	for method in module.methods:
		methodList.append(SwiftRPCMethodDeclaration(method))
	return ';\n'.join(methodList)

SwiftGeneratedWarning = """\
/**
 * @generated
 *
 * AUTOGENERATED. DO NOT EDIT! 
 *
 */"""


############################
# Implementation module
############################

def SwiftTypeFieldInitList( genType ):
	template = Template('\t\tself.$fieldAlias = $fieldAlias;')
	fieldList = []
	for fieldName in genType.fieldNames():
		field = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		fieldList.append( template.substitute( fieldAlias=fieldAlias ) )
	return '\n'.join( fieldList )

def SwiftTypeMethodActualArgList( genType ):
	argList = []
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType( fieldName )
		fieldAlias = genType.fieldAlias( fieldName )
		argList.append( '%s:%s' % ( capitalizeFirstLetter( fieldAlias ), fieldAlias ) )
	return '\n\t\t\t\t\t\tand'.join( argList )

def SwiftTypeInitImplList( genType ):
	baseTemplate = Template("""
$declaration {
\t\t//super.init()
$fieldInitList
\t}""")

	superTemplate = Template("""
$declaration {
	super.init($actualArgList)
$fieldInitList
}""")
	if genType.baseType is not None:
		return superTemplate.substitute( declaration=SwiftTypeInitDeclaration(genType), actualArgList=SwiftTypeMethodActualArgList(
			genType.baseType), fieldInitList=SwiftTypeFieldInitList(genType))
	return baseTemplate.substitute( declaration=SwiftTypeInitDeclaration(genType), fieldInitList=SwiftTypeFieldInitList(
		genType))

def SwiftUnwindTypeToDict( genType, objcArgName, level, recursive=True ):
	if isinstance( genType, GenIntegralType ):
		return SwiftDecorateTypeForDict(objcArgName, genType)

	elif isinstance( genType, GenComplexType ):
		if not recursive:
			return '%s.dictionary(error)' % objcArgName

		fieldTemplate = Template('$tabLevel"$argName" : $argValue')
		fieldList = []

		for argName in genType.allFieldNames():
			fieldType = genType.fieldType(argName)
			objcStatement = genType.fieldAlias(argName)
			if objcArgName is not None:
				objcStatement = '%s.%s' % ( objcArgName, genType.fieldAlias(argName) )
			fieldList.append( fieldTemplate.substitute( tabLevel='\t'*level, argName=argName, argValue=SwiftUnwindTypeToDict(
				fieldType, objcStatement, level + 1, recursive=False)) )

		return Template('[\n$fieldList\n$tabLevel]').substitute( fieldList=',\n'.join(fieldList), tabLevel='\t'*(level-1) )

	elif isinstance( genType, GenListType ):
		if isinstance( genType.itemType, GenIntegralType ):
			return Template('($objcArgName == nil ? [NSNull null] : $objcArgName)').substitute(objcArgName=objcArgName)
		else:
			arrayTemplate = Template("""\
^NSArray*(NSArray* inArr) {
${tabLevel}NSMutableArray* resArr = [NSMutableArray arrayWithCapacity:[inArr count]];
${tabLevel}for($objcType inObj in inArr) { [resArr addObject:$argValue]; }
${tabLevel}return resArr; } ($objcArgName)""")
			return arrayTemplate.substitute( tabLevel='\t'*level, objcType=SwiftAssumeType(genType.itemType), argValue=SwiftUnwindTypeToDict(
				genType.itemType, 'inObj', level + 2, recursive=False), objcArgName=objcArgName )

def SwiftListTypeFromDictionary( genType, objcDataGetter, level ):
	listTypeTemplate = Template("""\
^NSArray*(id inObj) {
${tabLevel}\tNSMutableArray* items;
${tabLevel}\tif ( inObj == nil ||  [inObj isEqual:[NSNull null]] || ![inObj isKindOfClass:NSArray.class]) return nil;
${tabLevel}\tNSArray* inArr = (NSArray*)inObj;
${tabLevel}\titems = [NSMutableArray arrayWithCapacity:inArr.count];
${tabLevel}\tfor ( id item in inArr ) { id tmp; [items addObject:$itemObj]; }
${tabLevel}\treturn items;
${tabLevel}}( $objcDataGetter )""")
	return listTypeTemplate.substitute( tabLevel='\t'*level, itemObj=SwiftTypeFromDictionary(genType.itemType, "item",
																							 level + 1), objcDataGetter=objcDataGetter )

def SwiftTypeFromDictionary( genType, objcDataGetter, level ):
	complexTypeTemplate = Template('$typeName($objcDataGetter, error: error)')
	if isinstance( genType, GenIntegralType ):
		return SwiftDecorateTypeFromJSON(genType, objcDataGetter)
	if isinstance( genType, GenComplexType ):
		return complexTypeTemplate.substitute( typeName=genType.name, objcDataGetter=objcDataGetter )
	if isinstance( genType, GenListType ):
		if isinstance(genType.itemType, GenIntegralType):
			return SwiftDecorateTypeFromJSON(genType, objcDataGetter)
		else:
			return SwiftListTypeFromDictionary(genType, objcDataGetter, level + 1)

def SwiftComplexTypeFieldListFromDictionary( genType, objcDictArgName ):
	template = Template('\tself.$argName = $value')
	fieldList = []
	#here we init all the fields available, including ancestor's ones instead of calling non-public "[super readDictionary]" method
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		objcDataGetter = '%s["%s"]' % ( objcDictArgName, fieldName )
		fieldList.append( template.substitute( argName=genType.fieldAlias(fieldName), value=SwiftTypeFromDictionary(
			fieldType, objcDataGetter, 1)) )
	return ';\n'.join( fieldList )

def SwiftTypeSerializationImplList( genType ):
	template = Template("""
    func dictionary(error: NSError!) -> Dictionary<String, Any>! {
	    return $typeDictionary;
    }

    func dump(error: NSError!) -> NSData! {
	    var dict: Dictionary<String, Any>! = self.dictionary(error)
	    if let e = error {
	        return nil
	    } else {
	        return NSJSONSerialization.dataWithJSONObject(self.dictionary(error), options: jsonFormatOption, error: error)
	    }
    }

    func read(dict: Dictionary<String, Any>!, error: NSError!) {
	    var tmp: AnyObject!;
        $complexTypeFieldsFromDictionary;
    }

    init!(dictionary: Dictionary<String, Any>!, error: NSError!) {
	    if dictionary == nil {
	        return nil
	    }
	    //super.init()
		self.read(dictionary, error: error);
		if let e = error {
		    return nil
		}
    }

    init!(jsonData: NSData!, error: NSError!) {
	    if let jData = jsonData {
            //super.init()
		    let dict: Dictionary<String, Any>! = NSJSONSerialization.JSONObjectWithData(jData, options: NSJSONReadingAllowFragments, error: error)
		    if let er = error {
		        return nil
		    }
		    self.read(dict, error: error)
		    if let er =  error {
		        return nil
		    }
	    } else {
	        return nil
	    }
    }
""")
	
	return template.substitute( typeDictionary=SwiftUnwindTypeToDict(genType, 'self', 2), complexTypeFieldsFromDictionary=SwiftComplexTypeFieldListFromDictionary(
		genType, 'dict'))
	
def SwiftTypeImplementation( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
class $typeName {
$properties
$initImplList
$serializationImplList
}
""")
	return template.substitute( typeName=genType.name, properties=SwiftTypePropertyList( genType ), initImplList=SwiftTypeInitImplList(genType), serializationImplList=SwiftTypeSerializationImplList(
		genType))

def SwiftTypeImplementationForCategory( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
class $typeName {
$initImplList
}
""")
	return template.substitute( typeName=genType.name, initImplList=SwiftTypeInitImplList(genType))

def SwiftCategoryTypeImplementation( genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
extension $typeName {
$serializationImplList
}
""")
	return template.substitute( typeName=genType.name, category=category, serializationImplList=SwiftTypeSerializationImplList(
		genType))

def SwiftTypeImplementationList( module, implGenerator ):
	implList = []
	for genTypeName in module.typeList.keys():
		currentType = module.typeList[genTypeName]
		SwiftAppendIfNotEmpty( implList, implGenerator( currentType ) )
	return '\n'.join( implList )

def SwiftRPCMethodImplementation( method ):
	jsonArgsTemplate = Template('NSJSONSerialization.dataWithJSONObject($jsonArgDict, options: jsonFormatOption, error: error)')
	customArgsTemplate = Template("""\
	if !self.transport.respondsToSelector("$customArgSectionName:") {
		assert("Transport does not respond to selector $customArgSectionName:")
	} else {
		self.transport.performSelector("$customArgSectionName:",  object: $customArgDict)
	}
""")
	returnTemplate = Template('return $response')

	template = Template("""\
$declaration {
	id tmp;
$setCustomArgs
	let jsonData: NSData! = $jsonData;
	if !self.transport.writeAll(jsonData, prefix: $prefix error: error) {
		return$emptyVal
	}
	let outputData: NSData! = self.transport.readAll()
	if let outData = outputData {
        let output = NSJSONSerialization.JSONObjectWithData(outData, options: NSJSONReadingAllowFragments, error: error)
        if let er = error {
            return$emptyVal;
        }
        $returnStr
	} else {
	    return$emptyVal
	}
}
""")

	customArgsList = []
	for customRequestTypeKey in method.customRequestTypes.keys():
		customRequestType = method.customRequestTypes[customRequestTypeKey]
		customArgsList.append( customArgsTemplate.substitute( customArgSectionName=makeAlias('set_' + customRequestTypeKey), customArgDict=SwiftUnwindTypeToDict(
			customRequestType, None, 3)) )
	setCustomArgs = '\n'.join(customArgsList)

	jsonData='nil'
	if method.requestJsonType is not None:
		jsonData = jsonArgsTemplate.substitute( jsonArgDict=SwiftUnwindTypeToDict(method.requestJsonType, None,
																				  level=2))

	prefix = 'prefix'
	if method.prefix is not None:
		prefix = '"%s"' % (method.prefix)

	returnStr = ''
	emptyVal = ''
	if method.responseType is not None:
		returnStr = returnTemplate.substitute( response=SwiftTypeFromDictionary(method.responseType, 'output', level=2))
		emptyVal = ' ' + SwiftEmptyValForType(method.responseType)

	return template.substitute( declaration=SwiftRPCMethodDeclaration(method), setCustomArgs=setCustomArgs, jsonData=jsonData, prefix=prefix, returnStr=returnStr, emptyVal=emptyVal )

def SwiftRPCImplementation( module ):
	if len(module.methods) == 0:
		return ''

	template = Template("""\
class $moduleName {
$rpcMethodImplementationsList
}
""")

	methodList = []
	for method in module.methods:
		methodList.append(SwiftRPCMethodImplementation(method))

	return template.substitute( moduleName=module.name, rpcMethodImplementationsList='\n'.join( methodList ) )


def SwiftModule( module ):
	template = Template("""\
$generatedWarning

import Foundation

$typeImplementationList

$rpcImplementation

""")

	return template.substitute(generatedWarning=SwiftGeneratedWarning, modHeader=module.name, typeImplementationList=SwiftTypeImplementationList(
		module, SwiftTypeImplementation), rpcImplementation=SwiftRPCImplementation(
		module))

def SwiftModuleForCategory( module ):
	template = Template("""\
$generatedWarning

import Foundation

$typeImplementationList
""")
	return template.substitute(generatedWarning=SwiftGeneratedWarning, typeImplementationList=SwiftTypeImplementationList(
		module, SwiftTypeImplementationForCategory))

def SwiftCategory( module, category ):
	template = Template("""\
$generatedWarning

import Foundation

$typeImplementationList

""")
	return template.substitute(generatedWarning=SwiftGeneratedWarning, typeImplementationList=SwiftTypeImplementationList(
		module, lambda genType: SwiftCategoryTypeImplementation(genType, category)))

############################
# Entry point
############################

def writeSwiftImplementationMonolith( genDir, module ):
	swiftImpl = open( os.path.join( genDir, module.name + ".swift" ), "wt" )

	swiftImpl.write(SwiftModule( module ))

def writeSwiftImplementationCategory( genDir, category, module ):
	objCImpl = open( os.path.join( genDir, module.name + ".swift" ), "wt" )
	objCImplCategory = open( os.path.join( genDir, module.name + "+" + category + ".swift" ), "wt" )

	objCImpl.write(SwiftModuleForCategory(module))
	objCImplCategory.write(SwiftCategory(module, category))

def writeSwiftImplementation( genDir, category, module ):

	if not os.path.exists( genDir ):
		os.makedirs( genDir )

	if category is not None and len(category) > 0:
		writeSwiftImplementationCategory( genDir, category, module )
	else:
		writeSwiftImplementationMonolith(genDir, module)


