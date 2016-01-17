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
import os
from string import Template

def SwiftCheckOptional( getType, optional):
	result = getType
	if optional:
		result += "?"
	return result

def SwiftAssumeType( genType, optional=False ):
	if isinstance( genType, GenIntegralType ):
		t = genType.sType
		integralTypeMap = { "string": "String", "bool": "Bool", "int32": "Int32", "int64": "Int64", "double": "Double", "raw": "[String : AnyObject]", "rawstr": "[String : AnyObject]" }
		if t in integralTypeMap:
			return SwiftCheckOptional( integralTypeMap[t], optional)
	if isinstance( genType, GenComplexType ):
		return SwiftCheckOptional( genType.name, optional)
	if isinstance( genType, GenListType ):
		return SwiftCheckOptional ('[%s]' % SwiftAssumeType(genType.itemType) , optional)
	return "_ERROR_"

def SwiftGetNumberValue(genType):
	if genType.sType == "bool":
		return 'boolValue'
	if genType.sType == "int32":
		return 'intValue'
	if genType.sType == "int64":
		return 'longLongValue'
	if genType.sType == "double":
		return 'doubleValue'
	return "ERROR"

def SwiftDecorateTypeForDict( objcTypeStr, genType, wrapToNull=True ):
	wrapTemplate = ''
	optional = ''
	if wrapToNull is True:
		wrapTemplate = objcTypeStr + ' == nil ? NSNull() : '
		optional = '!'
	template = Template(wrapTemplate + '$objcTypeStr as! AnyObject')
	if genType.sType == 'bool':
		template = Template(wrapTemplate + 'NSNumber(bool: $objcTypeStr%s)' % optional)
	if genType.sType == 'int32':
		template = Template(wrapTemplate + 'NSNumber(int: $objcTypeStr%s)' % optional)
	if genType.sType == 'int64':
		template = Template(wrapTemplate + ' NSNumber(longLong: $objcTypeStr%s)' % optional)
	if genType.sType == 'double':
		template = Template(wrapTemplate + ' NSNumber(double: $objcTypeStr%s)' % optional)
	if genType.sType == 'rawstr':
		template = Template('NSString(data: try! NSJSONSerialization.dataWithJSONObject($objcTypeStr as AnyObject, options: [.PrettyPrinted]), encoding: NSUTF8StringEncoding)')
	return template.substitute( objcTypeStr=objcTypeStr )

def SwiftDecorateTypeFromJSON( genType, varValue ):
	templateNSNumberStr = Template('($tmpVarValue as? NSNumber)?.$selector')
	templateNSStringStr = Template('$tmpVarValue as? String')
	templateNSDictionaryStr = Template('$tmpVarValue as? [String : AnyObject]')
	templateRawNSDictionaryStr = Template(' $tmpVarValue as? try! NSJSONSerialization.JSONObjectWithData:((tmp as? String)?.dataUsingEncoding(NSUTF8StringEncoding), options: .AllowFragments)')
	if isinstance( genType, GenListType ):
		if genType.itemType.ptr == '':
			return '(%s as? [NSNumber])?.map{$0.%s}' % (varValue, SwiftGetNumberValue( genType.itemType ))
		else:
			return Template('$tmpVarValue as? $itemType').substitute( tmpVarValue=varValue, itemType=SwiftAssumeType( genType ) )
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
	return "ERROR"

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
	template = Template('$argAlias: $argType?')
	argList = []
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		fieldAlias = genType.fieldAlias(fieldName)
		argList.append( template.substitute( argAlias=fieldAlias, argType=SwiftAssumeType(fieldType) ) )
	return ', \n\t\t\t'.join(argList)

def SwiftTypeInitDeclaration( genType ):
	return Template('\tinit($argList)').substitute( argList=SwiftArgList(genType))

def SwiftTypePropertyList( genType ):
	template = Template('\tvar $propAlias: $propType ')
	listTemplate = Template('\tvar $propAlias: $propType ')
	propList = []
	for fieldName in genType.fieldNames():
		fieldType = genType.fieldType(fieldName)
		if isinstance( fieldType, GenListType ):
			propList.append( listTemplate.substitute(propType=SwiftAssumeType(fieldType, optional=True), propAlias=genType.fieldAlias( fieldName )) )
		else:
			propList.append( template.substitute(propType=SwiftAssumeType(fieldType, optional=True), propAlias=genType.fieldAlias( fieldName )) )
	return '\n'.join(propList)

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
	template = Template('func ${methodName}($argList) -> $responseType')
	argList = []

	if method.prefix is None:
		argList.append('prefix: String!')
	for customRequestType in method.customRequestTypes.values():
		argList.append(SwiftArgList(customRequestType))
	if method.requestJsonType is not None:
		argList.append(SwiftArgList(method.requestJsonType))

	argList.append('inout error: NSError?')

	argListStr = ', '.join(argList)

	responseType = 'Void'
	if method.responseType is not None:
		responseType = "%s?" % ( SwiftAssumeType(method.responseType) )

	return template.substitute( responseType=responseType, methodName=method.name, argList=argListStr )

def SwiftRPCMethodList( module ):
	methodList = []
	for method in module.methods:
		methodList.append(SwiftRPCMethodDeclaration(method))
	return '\n'.join(methodList)

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
	template = Template('\t\tself.$fieldAlias = $fieldAlias')
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
		argList.append( '%s: %s' % ( fieldAlias, fieldAlias ) )
	return '\n\t\t\t\t\t\t, '.join( argList )

def SwiftTypeInitImplList( genType ):
	baseTemplate = Template("""
$declaration {
\t\t//super.init()
$fieldInitList
\t}""")

	superTemplate = Template("""
$declaration {
\t\tsuper.init($actualArgList)
$fieldInitList
\t}""")
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
			# TODO: inside map don't cast to any type
			if objcArgName != '$0':
				return Template('($argName == nil ? NSNull() : $argName!.dictionary(&error) as AnyObject)').substitute(argName=objcArgName)
			else:
				return Template('$argName.dictionary(&error) as AnyObject').substitute(argName=objcArgName)

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
			return """(%s == nil ? NSNull() : %s!.map {%s})""" % (objcArgName, objcArgName, SwiftDecorateTypeForDict('$0', genType.itemType, wrapToNull=False))
		else:
			# TODO: inside map don't cast to any type
			if objcArgName != '$0':
				arrayTemplate = Template("""$objcArgName == nil ? NSNull() : $objcArgName!.map{
$tabLevel\t$argValue
$tabLevel} as AnyObject""")
			else:
				arrayTemplate = Template("""$objcArgName.map{
$tabLevel\t$argValue
$tabLevel} as AnyObject""")
			return arrayTemplate.substitute( tabLevel='\t'*level, argValue=SwiftUnwindTypeToDict(
				genType.itemType, '$0', level + 2, recursive=False), objcArgName=objcArgName )

def SwiftListTypeFromDictionary( genType, objcDataGetter, level ):

	if objcDataGetter == '$0':
		template = """($objcDataGetter as! [AnyObject]).map{
${tabLevel}\t\t$itemObj
${tabLevel}\t}"""
	else:
		template = """($objcDataGetter as? [AnyObject])?.map{
${tabLevel}\t\t$itemObj
${tabLevel}\t}"""

	if isinstance( genType.itemType, GenListType ):
		listTypeTemplate = Template(template)
	else:
		listTypeTemplate = Template(template + """.filter{$oneArg != nil}.map{ $oneArg! }""")
	return listTypeTemplate.substitute( tabLevel='\t'*level, oneArg='$0', itemObj=SwiftTypeFromDictionary(genType.itemType, "$0",
																							 level + 1), objcDataGetter=objcDataGetter, type=SwiftAssumeType( genType ), itemType=SwiftAssumeType( genType.itemType ) )

def SwiftTypeFromDictionary( genType, objcDataGetter, level ):
	complexTypeTemplate = Template('$typeName(dictionary: $objcDataGetter as? [String : AnyObject], error: &error)')
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
	template = Template('self.$argName = $value')
	fieldList = []
	#here we init all the fields available, including ancestor's ones instead of calling non-public "[super readDictionary]" method
	for fieldName in genType.allFieldNames():
		fieldType = genType.fieldType(fieldName)
		objcDataGetter = '%s?["%s"]' % ( objcDictArgName, fieldName )
		fieldList.append( template.substitute( argName=genType.fieldAlias(fieldName), value=SwiftTypeFromDictionary(
			fieldType, objcDataGetter, 1)) )
	return '\n\t\t'.join( fieldList )

def SwiftTypeSerializationImplList( genType, isCategory=False ):
	overridePrefix = ''
	superInitCall = ''
	convenience = ''
	defaultInitTemplate = Template("""${conveniencePref}${overridePref}init(){
		$superInit
	}""")
	if genType.baseType is not None:
		overridePrefix = 'override '
		superInitCall = 'super.init()'
	if isCategory:
		convenience = 'convenience '
		superInitCall = 'self.init()'
		# There is not default init for category
		defaultInitTemplate = Template("""""")

	defaultInitValue = defaultInitTemplate.substitute(conveniencePref=convenience, overridePref=overridePrefix, superInit=superInitCall)

	template = Template("""
	${overridePref}func dictionary(inout error: NSError?) -> [String : AnyObject] {
		return $typeDictionary
	}

	${overridePref}func dump(inout error: NSError?) -> NSData? {
		let dict = self.dictionary(&error)
		if let _ = error {
			return nil
		} 
		do {
    		let result = try NSJSONSerialization.dataWithJSONObject(dict, options: [.PrettyPrinted])
    		return result
		} catch let er as NSError {
    		error = er
    		return nil
		}	
	}

	${overridePref}func read(dict: [String : AnyObject]?, inout error: NSError?) {
		$complexTypeFieldsFromDictionary
	}

	${conveniencePref}${overridePref}init?(dictionary: [String : AnyObject]!, inout error: NSError?) {
		$superInit
		if dictionary == nil {
			return nil
		}
		self.read(dictionary, error: &error)
		if let _ = error {
			return nil
		}
	}

	${conveniencePref}${overridePref}init?(jsonData: NSData?, inout error: NSError?) {
		$superInit
		do {
			if let jsonData = jsonData, let dict = try NSJSONSerialization.JSONObjectWithData(jsonData, options: [.AllowFragments]) as? [String : AnyObject] {
				self.read(dict, error: &error)
			} else {
				return nil
			}
		} catch let er as NSError {
			error = er
			return nil
		}
	}
	$defaultInit
""")
	
	return template.substitute( conveniencePref=convenience, overridePref=overridePrefix, typeDictionary=SwiftUnwindTypeToDict(genType, 'self', 3), complexTypeFieldsFromDictionary=SwiftComplexTypeFieldListFromDictionary(
		genType, 'dict'), superInit=superInitCall, defaultInit=defaultInitValue)
	
def SwiftTypeImplementation( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	baseTypeName = ''
	if genType.baseType is not None:
		baseTypeName = ": " + genType.baseType.name

	template = Template("""\
class $typeName $baseTypeName {
$properties
$initImplList
$serializationImplList
}
""")
	return template.substitute( typeName=genType.name, baseTypeName=baseTypeName, properties=SwiftTypePropertyList( genType ), initImplList=SwiftTypeInitImplList(genType), serializationImplList=SwiftTypeSerializationImplList(
		genType))

def SwiftTypeImplementationForCategory( genType ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
class $typeName {
$properties

	init() {
	}
$initImplList
}
""")
	return template.substitute( typeName=genType.name, properties=SwiftTypePropertyList( genType ), initImplList=SwiftTypeInitImplList(genType))

def SwiftCategoryTypeImplementation( genType, category ):
	if isinstance( genType, GenIntegralType ) or isinstance( genType, GenListType ):
		return ''
	template = Template("""\
extension $typeName {
$serializationImplList
}
""")
	return template.substitute( typeName=genType.name, category=category, serializationImplList=SwiftTypeSerializationImplList(
		genType, isCategory=True))

def SwiftTypeImplementationList( module, implGenerator ):
	implList = []
	for genTypeName in module.typeList.keys():
		currentType = module.typeList[genTypeName]
		SwiftAppendIfNotEmpty( implList, implGenerator( currentType ) )
	return '\n'.join( implList )

def SwiftRPCMethodImplementation( method ):
	jsonArgsTemplate = Template('try! NSJSONSerialization.dataWithJSONObject($jsonArgDict, options: [.PrettyPrinted])')
	customArgsTemplate = Template("""\
		if let conProtocol = self.transport as? $protocolName {
			conProtocol.$customArgSectionName($customArgDict)
		} else {
			assertionFailure("Transport does not respond to selector $customArgSectionName:")
		}
""")
	returnTemplate = Template('return $response')

	template = Template("""\
	$declaration {
	$setCustomArgs
		do {
			let jsonData: NSData! = $jsonData
			try self.transport?.writeAll(jsonData, prefix: $prefix)
			if let outData = self.transport?.readAll() {
				let output = try NSJSONSerialization.JSONObjectWithData(outData, options: [.AllowFragments])
				$returnStr
			}
			return$emptyVal
		} catch let er as NSError {
    		error = er
    		return$emptyVal
		}
	}
""")

	customArgsList = []
	for customRequestTypeKey in method.customRequestTypes.keys():
		customRequestType = method.customRequestTypes[customRequestTypeKey]
		customArgsList.append( customArgsTemplate.substitute( protocolName=makeAlias('_' + method.name) + 'Protocol', customArgSectionName=makeAlias('set_' + customRequestTypeKey), customArgDict=SwiftUnwindTypeToDict(
			customRequestType, None, 4)) )
	setCustomArgs = '\n'.join(customArgsList)

	jsonData='nil'
	if method.requestJsonType is not None:
		jsonData = jsonArgsTemplate.substitute( jsonArgDict=SwiftUnwindTypeToDict(method.requestJsonType, None,
																				  level=4))

	prefix = 'prefix'
	if method.prefix is not None:
		prefix = '"%s"' % method.prefix

	returnStr = ''
	emptyVal = ''
	if method.responseType is not None:
		returnStr = returnTemplate.substitute( response=SwiftTypeFromDictionary(method.responseType, 'output', level=2))
		emptyVal = ' ' + SwiftEmptyValForType(method.responseType)

	return template.substitute( declaration=SwiftRPCMethodDeclaration(method), setCustomArgs=setCustomArgs, jsonData=jsonData, prefix=prefix, returnStr=returnStr, emptyVal=emptyVal )

def SwiftRPCProtocolDeclaration( module ):
	if len(module.methods) == 0:
		return ''

	template = Template("""
protocol $protocolName {
$methodListDeclaration
}
""")
	protocolsList = []
	for method in module.methods:
		if len(method.customRequestTypes.keys()) == 0:
			continue
		methodList = []
		for customRequestTypeKey in method.customRequestTypes.keys():
			methodList.append('\tfunc ' + makeAlias('set_' + customRequestTypeKey) + '(' + makeAlias(customRequestTypeKey) +  ': Dictionary<String, AnyObject>!)')
		protocolsList.append(template.substitute(protocolName=makeAlias('_' + method.name) + "Protocol", methodListDeclaration='\n'.join(methodList)))

	return '\n'.join(protocolsList)

def SwiftRPCImplementation( module ):
	if len(module.methods) == 0:
		return ''

	template = Template("""\
class $moduleName: IFServiceClient {
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

$rpcProtocolDeclaration

$rpcImplementation

""")

	return template.substitute(generatedWarning=SwiftGeneratedWarning, modHeader=module.name, typeImplementationList=SwiftTypeImplementationList(
		module, SwiftTypeImplementation), rpcProtocolDeclaration=SwiftRPCProtocolDeclaration( module ),
		rpcImplementation=SwiftRPCImplementation( module))

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


