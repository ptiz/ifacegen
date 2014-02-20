#python
import json
import sys
import types
import os
from collections import OrderedDict
from ifaceobj import *

def typeFromJSON( decoration, argName, value, typeList ):
	newType = None
	if type( value ) == types.DictType or type( value ) == OrderedDict:
		newType = GenComplexType( decoration, argName )	
		for k in value.keys():
			field = value[k]
			newType.addFieldType( k, typeFromJSON( newType.name, k, field, typeList ) )
		if len( newType.fieldNames() ) == 0:
			return None
		typeList[newType.name] = newType

	elif type( value ) == types.ListType:
		newType = GenListType( decoration, argName )		
		listItem = value[0]
		newType.itemType = typeFromJSON( newType.name, 'item', listItem, typeList )
		typeList[newType.name] = newType

	#apply decoration to name if needed: GenType(value).name
	elif GenType(value).name in typeList:
		newType = typeList[ GenType(value).name ]
	else:
		newType = GenIntegralType( value )
	return newType					

def buildTypeFromStructJSON( jsonItem, typeList ):
	typeName = jsonItem["struct"]
	retType = typeFromJSON( "", typeName, jsonItem["typedef"], typeList )
	if retType is not None and "extends" in jsonItem:
		parentTypeName = jsonItem["extends"]
		if (parentTypeName is not None) and (parentTypeName in typeList):
			retType.baseType = typeList[ parentTypeName ]
		else:
			raise Exception("Unknown base type %s for type %s", retType.name, parentTypeName )
	return retType

def buildMethodFromJSON( jsonItem, typeList ):

	methodName = jsonItem["procedure"]
	prefix = jsonItem["prefix"]
	request = jsonItem["request"]
	response = jsonItem["response"]

	prerequest = None
	if "prerequest" in jsonItem.keys():
		prerequest = jsonItem["prerequest"]

	method = GenMethod( methodName, prefix )

	for k in request.keys():
		argument = request[k]
		method.requestTypes[k] = typeFromJSON( methodName, k, argument, typeList )

	if prerequest is not None:
		for k in prerequest.keys():
			argument = prerequest[k]
			tp = typeFromJSON( methodName, k, argument, typeList )
			if isinstance( tp, GenIntegralType ):
				method.prerequestTypes[k] = tp
			else:
				raise Exception("Only integral types allowed in pre-request arguments: %s, %s:%s" % k, methodName, tp.name )

	# flatten return type if it is only one filed in dictionary
	if len( response ) == 1:
		if type( response ) == types.ListType:
			method.responseType = typeFromJSON( methodName, "List", response, typeList )
			method.responseArgName = None
		else:
			method.responseType = typeFromJSON( methodName, response.keys()[0], response.values()[0], typeList )
			method.responseArgName = response.keys()[0]
	else:
		method.responseType = typeFromJSON( methodName, "Info", response, typeList )
		method.responseArgName = None
	
	return method
