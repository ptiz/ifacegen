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

import json
import sys
import types
import os
from collections import OrderedDict
from ifaceobj import *

def typeFromJSON( decoration, argName, value, typeList, importedTypeList ):

	try:
		return GenIntegralType(value)
	except Exception as ex:
		pass

	if type( value ) == types.UnicodeType:
		decoratedTypeName = GenType( value ).name
		if decoratedTypeName in importedTypeList:
			return importedTypeList[ decoratedTypeName ]
		if decoratedTypeName in typeList:
			return typeList[ decoratedTypeName ]
		raise Exception( 'Unknown type name found: ' + value )
	
	if type( value ) == types.DictType or type( value ) == OrderedDict:
		newType = GenComplexType( decoration, argName )

		if newType.name in importedTypeList or newType.name in typeList:
			raise Exception( 'Duplicated name in struct declaration: ' + newType.name )

		typeList[newType.name] = newType

		for k in value.keys():
			field = value[k]
			newType.addFieldType( k, typeFromJSON( newType.name, k, field, typeList, importedTypeList ) )
		if len( newType.fieldNames() ) == 0:
			return None

		typeList[newType.name] = typeList.pop(newType.name)

		return newType

	if type( value ) == types.ListType:
		newType = GenListType( decoration, argName )
		listItem = value[0]
		newType.itemType = typeFromJSON( newType.name, 'item', listItem, typeList, importedTypeList )
		typeList[newType.name] = newType
		return newType

	return None

def buildTypeFromStructJSON( jsonItem, typeList, importedTypeList ):
	typeName = jsonItem["struct"]
	retType = typeFromJSON( "", typeName, jsonItem["typedef"], typeList, importedTypeList )
	if retType is not None and "extends" in jsonItem:
		parentTypeName = jsonItem["extends"]
		if (parentTypeName is not None):
			decoratedParentTypeName = GenType( parentTypeName ).name
			if (decoratedParentTypeName in typeList):
				retType.baseType = typeList[ decoratedParentTypeName ]
			elif (decoratedParentTypeName in importedTypeList):
				retType.baseType = importedTypeList[ decoratedParentTypeName ]
			else:
				raise Exception("Unknown base type %s for type %s" % retType.name, parentTypeName )
	return retType

def buildMethodFromJSON( jsonItem, typeList, importedTypeList ):

	prefix = None
	methodName = None
	request = None
	customRequests = OrderedDict()
	response = None

	for methodKey in jsonItem.keys():
		if methodKey == "procedure":
			methodName = jsonItem["procedure"]
		elif methodKey == "prefix":
			prefix = jsonItem["prefix"]
		elif methodKey == "response":
			response = jsonItem["response"]
		elif methodKey == "request":
			request = jsonItem["request"]
		else:
			customRequests[methodKey] = jsonItem[methodKey]

	if methodName is None:
		raise Exception("No method name provided for method in IDL: %s" % jsonItem)

	method = GenMethod( methodName, prefix )
	typeDecoration = capitalizeFirstLetter( methodName )

	if request is not None:
		requestTypeName = "%s_json_args" % methodName
		method.requestJsonType = typeFromJSON( None, requestTypeName, request, typeList, importedTypeList )
		del typeList[method.requestJsonType.name]

	for customRequestKey in customRequests.keys():
		customRequest = customRequests[customRequestKey]
		customRequestTypeName = "%s_%s_args" % (methodName, customRequestKey)
		method.customRequestTypes[customRequestKey] = typeFromJSON( None, customRequestTypeName, customRequest, typeList, importedTypeList )
		del typeList[method.customRequestTypes[customRequestKey].name]	

	if response is None:
		return method
	elif len( response ) == 1:
		# flatten return type if it is only one filed in dictionary
		if type( response ) == types.ListType:
			method.responseType = typeFromJSON( typeDecoration, "List", response, typeList, importedTypeList )
			method.responseArgName = None
		else:
			method.responseType = typeFromJSON( typeDecoration, response.keys()[0], response.values()[0], typeList, importedTypeList )
			method.responseArgName = response.keys()[0]
	else:
		method.responseType = typeFromJSON( typeDecoration, "Info", response, typeList, importedTypeList )
		method.responseArgName = None
	
	return method

def parseModule( jsonFile ):
	with open( jsonFile, "rt" ) as jFile:
		jsonObj = json.load( jFile, object_pairs_hook=OrderedDict )

		if jsonObj["iface"] is None:
			raise Exception('Module ' + jsonFile + ' is not a valid ifacegen IDL file. "iface" section was not found.')

		baseDir = os.path.dirname( jsonFile )

		inputNameParts = os.path.basename( jsonFile ).split('.')
		module = GenModule( inputNameParts[0] )

		for jsonItem in jsonObj["iface"]:
			if "struct" in jsonItem:
				buildTypeFromStructJSON( jsonItem, module.typeList, module.importedTypeList )
			elif "procedure" in jsonItem:
				module.methods.append( buildMethodFromJSON( jsonItem, module.typeList, module.importedTypeList ) )
			elif "import" in jsonItem:
				importModule( os.path.join( baseDir, jsonItem["import"]), fromModule=module )

	return module

def importModule( jsonFile, fromModule ):
	importedModule = parseModule( jsonFile )
	if ( importedModule is None ) or ( importedModule.name in fromModule.importedModuleNames ) or ( importedModule.name == fromModule.name ):
		return
	for typeName in importedModule.importedTypeList.keys():
		if typeName in fromModule.typeList:
			raise Exception( "Type %s imported from module %s exists in current module %s" % typeName, importedModule.name, fromModule.name )
		else:
			fromModule.importedTypeList[typeName] = importedModule.importedTypeList[typeName]
	for typeName in importedModule.typeList.keys():
		if typeName in fromModule.typeList:
			raise Exception( "Type %s imported from module %s exists in current module %s" % typeName, importedModule.name, fromModule.name )
		else:
			fromModule.importedTypeList[typeName] = importedModule.typeList[typeName]
	fromModule.importedModuleNames.append( importedModule.name )
