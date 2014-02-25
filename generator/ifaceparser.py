#python
import json
import sys
import types
import os
from collections import OrderedDict
from ifaceobj import *

def typeFromJSON( decoration, argName, value, typeList, importedTypeList ):
	newType = None
	
	if type( value ) == types.DictType or type( value ) == OrderedDict:
		newType = GenComplexType( decoration, argName )	
		for k in value.keys():
			field = value[k]
			newType.addFieldType( k, typeFromJSON( newType.name, k, field, typeList, importedTypeList ) )
		if len( newType.fieldNames() ) == 0:
			return None
		typeList[newType.name] = newType
		return newType

	if type( value ) == types.ListType:
		newType = GenListType( decoration, argName )
		listItem = value[0]
		newType.itemType = typeFromJSON( newType.name, 'item', listItem, typeList, importedTypeList )
		typeList[newType.name] = newType
		return newType

	#apply decoration to name if needed: GenType(value).name already decorated
	decoratedTypeName = GenType(value).name

	if decoratedTypeName in importedTypeList:
		return importedTypeList[ decoratedTypeName ]

	if decoratedTypeName in typeList:
		return typeList[ decoratedTypeName ]

	return GenIntegralType( value )

def buildTypeFromStructJSON( jsonItem, typeList, importedTypeList ):
	typeName = jsonItem["struct"]
	retType = typeFromJSON( "", typeName, jsonItem["typedef"], typeList, importedTypeList )
	if retType is not None and "extends" in jsonItem:
		parentTypeName = jsonItem["extends"]
		if (parentTypeName is not None):
			if (parentTypeName in typeList):
				retType.baseType = typeList[ parentTypeName ]
			if (parentTypeName in importedTypeList):
				retType.baseType = importedTypeList[ parentTypeName ]
		else:
			raise Exception("Unknown base type %s for type %s" % retType.name, parentTypeName )
	return retType

def buildMethodFromJSON( jsonItem, typeList, importedTypeList ):

	methodName = jsonItem["procedure"]
	prefix = jsonItem["prefix"]
	request = jsonItem["request"]
	response = jsonItem["response"]

	prerequest = None
	if "prerequest" in jsonItem.keys():
		prerequest = jsonItem["prerequest"]

	method = GenMethod( methodName, prefix )
	typeDecoration = capitalizeFirstLetter( methodName )	

	for k in request.keys():
		argument = request[k]
		method.requestTypes[k] = typeFromJSON( typeDecoration, k, argument, typeList, importedTypeList )

	if prerequest is not None:
		for k in prerequest.keys():
			argument = prerequest[k]
			tp = typeFromJSON( typeDecoration, k, argument, typeList, importedTypeList )
			if isinstance( tp, GenIntegralType ):
				method.prerequestTypes[k] = tp
			else:
				raise Exception("Only integral types allowed in pre-request arguments: %s, %s:%s" % k, methodName, tp.name )

	# flatten return type if it is only one filed in dictionary
	if len( response ) == 1:
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
		if jsonObj["iface"] is not None:

			baseDir = os.path.dirname( jsonFile )

			inputNameParts = os.path.basename( jsonFile ).split('.')		
			module = GenModule( inputNameParts[0] )

			for jsonItem in jsonObj["iface"]:
				if "struct" in jsonItem:
					structType = buildTypeFromStructJSON( jsonItem, module.typeList, module.importedTypeList )
					if structType is not None:
						module.structs.append( structType.name )
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
