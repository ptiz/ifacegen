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

import types
import os
from collections import OrderedDict

tabooedNames = [ "void", "id", "description" ]
tabooedStarts = [ "new", "alloc", "copy", "mutableCopy" ]
prerequestSymbols = { '[':'_', ']':'_', '.':'_' }

def capitalizeFirstLetter( strToCap ):
	return strToCap[:1].capitalize() + strToCap[1:]

def lowercaseFirstLetter( strToLo ):
	return strToLo[:1].lower() + strToLo[1:]

def makeAlias( strNameIn ):
	strName = strNameIn
	
	for i,j in prerequestSymbols.iteritems():
		strName = strName.replace(i, j)

	toks = strName.split('_')
	alias = ''

	if len(toks) > 1:
		alias += toks[0]
		for t in toks[1:]:
			alias += capitalizeFirstLetter(t)
	else:
		toks = strName.split('-')
		if len(toks) > 1:
			alias += toks[0]
			for t in toks[1:]:
				alias += capitalizeFirstLetter(t)
		else:
			alias = strName

	if alias in tabooedNames:
		return 'the' + capitalizeFirstLetter(alias)

	for tabooedStart in tabooedStarts:
		if alias.lower().startswith( tabooedStart ):
			return 'the' + capitalizeFirstLetter(alias)

	return alias

def strFromDictionary( d ):
	s = ""
	comm = ""
	for k in d.keys():
		s += ( comm +  "[" + k + ": " + str( d[k] ) + "]")
		comm = ", "
	return s

##############

genIntegralTypeList = [ "int32", "int64", "double", "string", "bool", "raw", "rawstr" ]

class GenType:
	namePrefix = ""
	def __init__( self, name ):
		if len( GenType.namePrefix ) and not name.startswith( GenType.namePrefix ):
			self.name = GenType.namePrefix + capitalizeFirstLetter( name )
		else:
			self.name = name
		self.nullable = False
		self.ptr = "*"

class GenIntegralType( GenType ):
	def __init__( self, sType ):
		GenType.__init__( self, "IntegralType" )
		if not sType in genIntegralTypeList:
			raise Exception( "Unknown integral type: " + sType )
		self.sType = sType
		if self.sType == "bool" or self.sType == "int32" or self.sType == "int64" or self.sType == "double":
			self.ptr = ""

	def __str__( self ):
		return "GenIntegralType (" + self.sType + ")"

	def __eq__( self, other ):
		if other is None or not isinstance( other, GenIntegralType ):
			return False
		return self.sType == other.sType

class GenComplexType( GenType ):
	def __init__( self, decoration, name ):
		if decoration is None or len( decoration ) == 0:
			GenType.__init__( self, makeAlias( name ) )
		else:
			GenType.__init__( self, decoration + capitalizeFirstLetter( makeAlias( name ) ) )
		self.fields_ = OrderedDict()
		self.fieldAliases_ = {}
		self.baseType = None

	def __eq__( self, other ):
		if other is None or not isinstance( other, GenComplexType ):
			return False
		if len( other.fields_ ) != len( self.fields_ ):
			return False
		for fieldKey in other.fields_.keys():
			if not fieldKey in self.fields_:
				return False
			if self.fields_[fieldKey] != other.fields_[fieldKey]:
				return False
		return True

	def addFieldType( self, fieldName, fieldType ):
		self.fields_[fieldName] = fieldType
		self.fieldAliases_[fieldName] = makeAlias( fieldName )

	def fieldNames( self ):
		return self.fields_.keys()

	def allFieldNames( self ):
		fieldsList = []
		if self.baseType is not None:
			fieldsList.extend( self.baseType.allFieldNames() )
		fieldsList.extend( self.fieldNames() )
		return fieldsList		

	def fieldType( self, fieldName ):
		if self.baseType is not None:		
			ft = self.baseType.fieldType( fieldName )
			if ft is not None:
				return ft
		if not fieldName in self.fields_:
			return None
		return self.fields_[fieldName]

	def fieldAlias( self, fieldName ):
		if self.baseType is not None:		
			fa = self.baseType.fieldAlias( fieldName )
			if fa is not None:
				return fa
		if not fieldName in self.fields_:
			return None				
		return self.fieldAliases_[fieldName]

	def traverse( self, f ):
		typeNames = [self.name]
		for key in self.fields_.keys():
			field = self.fields_[key]
			if isinstance( field ) and f( field, self.fieldAliases_[key] ):
				field.traverse(f)
			else:
				f( field, self.fieldAliases_[key] )

	def __str__( self ):
		return ''
		# typeNames = 
		# s = "GenComplexType " + self.name + ": " + strFromDictionary( self.fields_ ) + ", aliases: " + strFromDictionary( self.fieldAliases_ )

class GenListType( GenType ):
	def __init__( self, decoration, name ):
		GenType.__init__( self, decoration + capitalizeFirstLetter( makeAlias( name ) ) )
		self.itemType = None

	def __str__( self ):
		return "GenListType " + self.name + ", item: " + str( self.itemType )

class GenMethod:
	def __init__( self, name, prefix ):
		self.name = name
		self.prefix = prefix
		self.requestJsonType = None
		self.customRequestTypes = OrderedDict()
		self.responseType = None
		self.responseArgName = None

	def __str__(self):
		return "GenMethod " + self.name + ": JSON params: " + str( self.requestJsonType ) + ", Custom params: " + strFromDictionary(self.customRequestTypes) + ", Response type: " + str( self.responseType )

class GenModule:
	namePrefix = ""
	def __init__( self, name ):
		self.typeList = OrderedDict()
		self.methods = []
		self.structs = []
		if len(GenModule.namePrefix) and not name.startswith( GenModule.namePrefix ):
			self.name = GenModule.namePrefix + capitalizeFirstLetter(name)
		else:
			self.name = name
		self.importedModuleNames = []
		self.importedTypeList = OrderedDict()

		