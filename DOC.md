#Doc

##Google APIs example
To make calls to Google Places API (https://developers.google.com/places/documentation/details) all you need is URL, URL parameters and JSON response dictionary description. Here they are:

URL:
```
https://maps.googleapis.com/maps/api/place/details/json?key=<key>&reference=<ref>&sensor=true
```

JSON response (some code omitted for simplicity):
```json
{
    "result" : {
        "formatted_address" : "48 Pirrama Road, Pyrmont NSW, Australia",
        "formatted_phone_number" : "(02) 9374 4000",
        "geometry" : {
           "location" : {
             "lat" : -33.8669710,
             "lng" : 151.1958750
           }
        },
       "name" : "Google Sydney",
       "types" : [ "establishment" ]
    }
}
```

Let's make some IDL. Surprisingly, it's JSON itself. It consists of same dictionaries but slightly annotated.  Assume we call the file GoogleClient.json:
```json
{"iface": [

{
"struct": "GoogleLocation",
"typedef": {
       "lat": "double",
       "lng": "double"
    }
},

{
"struct": "GooglePlaceDetails",
"typedef": {
      "formatted_address" : "string",
      "formatted_phone_number" : "string",
      "geometry" : {
         "location" : "GoogleLocation"
      },
      "name" : "string",
      "types" : [ "string" ]
   }
},

{
"struct": "GoogleDetailsResult",
"typedef": {
    "result" : "GooglePlaceDetails",
    "status" : "string"
  }
},

{
"procedure": "placeDetails",
"prefix": "/place/details/json",
"prerequest": {
    "key":"string",
    "reference": "string",    
    "sensor": "string"   
  },
"request" : {},
"response": "GoogleDetailsResult" 
}

]}
```

The "prerequest" field describes URL parameters, they only can be "string" types. "request" field can hold any structs and atomic types as described.

Then we need some codegen:
```
$ python ifacegen.py GoogleClient.json
```

After that we have two files: GoogleClient.h and GoogleClient.m. This is how GoogleClient.h looks like:
```objc
#import <Foundation/Foundation.h>
#import "Transport.h"

@interface GoogleLocation: NSObject
- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;
- (id)initWithLat:(double_t)lat
	andLng:(double_t)lng;
- (id)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error;
- (id)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error;
@property (nonatomic) double_t lat;
@property (nonatomic) double_t lng;
@end;

@interface GooglePlaceGeometry: NSObject
@property (nonatomic) GoogleLocation* location;
@end;

@interface GooglePlaceDetailsGeometry: NSObject
@property (nonatomic) GoogleLocation* location;
@end;

@interface GooglePlaceDetails: NSObject
- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;
- (id)initWithFormattedAddress:(NSString*)formattedAddress
	andFormattedPhoneNumber:(NSString*)formattedPhoneNumber
	andGeometry:(GooglePlaceDetailsGeometry*)geometry
	andName:(NSString*)name
	andTypes:(NSArray*)types;
- (id)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error;
- (id)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error;
@property (nonatomic) NSString* formattedAddress;
@property (nonatomic) NSString* formattedPhoneNumber;
@property (nonatomic) GooglePlaceDetailsGeometry* geometry;
@property (nonatomic) NSString* name;
@property (nonatomic) NSArray* /*NSString*/ types;
@end;

@interface GoogleDetailsResult: NSObject
- (NSData*)dumpWithError:(NSError* __autoreleasing*)error;
- (id)initWithResult:(GooglePlaceDetails*)result
	andStatus:(NSString*)status;
- (id)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error;
- (id)initWithJSONData:(NSData*)jsonData error:(NSError* __autoreleasing*)error;
@property (nonatomic) GooglePlaceDetails* result;
@property (nonatomic) NSString* status;
@end;

@interface GoogleClient: NSObject

- (id)initWithTransport:(NSObject<Transport>*)transport;

/* methods */

- (GoogleDetailsResult*)placeDetailsWithKey:(NSString*)key
		andReference:(NSString*)reference
		andSensor:(NSString*)sensor
		andLanguage:(NSString*)language
		andError:(NSError* __autoreleasing*)error;
@end
```

That's all. Now you can create a client and start making calls! Somewhere in your code:
```objc
#import "HTTPTransport.h"
//...
  NSString* googleAPIHost = @"https://maps.googleapis.com/maps/api";
  self.transport = [[HTTPTransport alloc] initWithURL:[NSURL URLWithString:googleAPIHost]];
  self.google = [[GoogleClient alloc] initWithTransport:self.transport];
//...
  NSError* error;

  GoogleDetailsResult* result =
  [self.google placeDetailsWithKey:key
                      andReference:ref
                         andSensor:@"true"
                          andError:&error];
```

Transport protocol (and its out-of-the-box realization HTTPTransport) used by generated classes to make network calls has only synchronous methods. No blocks of callback delegates at all. Client code is free to wrap these calls in async manner according its needs.

##ifacegen console tool
Usage: 
```
$ python ifacegen.py [-h] [--prefix PREFIX] [-o OUTDIR] I [I ...]
```
- h shows help; 
- PREFIX is a string, ObjC namespace prefix that is added to a name of each class to be generated; 
- OUTDIR is a string, path to directory where the generated files to be placed. By default these files will be placed into a "gen-objc" subdirectory of working dir;
- I [I ...] are IDL file names to be processed.
 
##IDL description
ifacegen uses pure JSON format for IDL without any extensions.

####IDL header
```json
{"iface": [
<imports>,
<data structure declarations>,
<remote method declarations>
]}
```
From one IDL file one ObjC class will be created. All structures described will be declared in its header. All remote methods described will be declared as this class object methods.   

####Structure declaration
```json
{
"struct": "<structure name>",
"typedef": {
	"<field name>":"<field IDL type>", 
	...
	}
}
```
####Field types supported
- int32: translated into int32_t aka int ObjC type;
- int64: translated into int64_t aka long long ObjC type;
- bool: translated into BOOL ObjC type;
- double: translated into double ObjC type;
- string: translated into NSString* ObjC type;
- raw: translated into NSDictionary* ObjC type;
- rawstr: translated into NSDictionary* from JSON-encoded string;

JSON dictionaries nested into "typedef" are translated to structures with automatic naming:
```json
"typedef": {
	"nested":{
		"field":"int32"
	}
}
```
Arrays are also supported. Following code will be translated into class with "stringItems" property of type NSArray*:
```json
"typedef": {
	"string_items":[<item type>]
}
```
Field names like "id" and"void" will be decorated in code with "the" prefix, so "id" changes into "theId". The same happens with fields which names starting with "new", "alloc", "copy" and "mutableCopy". Names in code also will be converted in CamelCase if they_are_not_yet.

You can inherit one struct from another. Generated class ExtendedItem explicitly inherits BaseItem with all fields serialization/deserialization:
```json
{
"struct": "BaseItem",
"typedef" : {
    "field": "int32"
  }
}

{
"struct": "ExtendedItem",
"extends": "BaseItem",
"typedef": {
    "another_field": "string"
  }
}
```

Explicitly declared structures can be imported from another IDL file:
```json
{"iface": [
{ "import": "OtherModule.json" },
...
]}
```
####Remote method declaration
```json
{
"procedure": "<procedure name for ObjC>",
"prefix": "<remote service method prefix to be combined into resulting URL>",
"prerequest": {
		"<parameter to be passed in url>": "string",
		...
	},
"request" : <any explicit structure name or implicit struct declaration in brackets>,
"response": <any explicit structure name or implicit struct declaration in brackets>
}
```
"prerequest" field describes parameters to be passed as URL parts. Their data type must be only "string". "request" field used for passing parameters throug JSON data. Any of them can be declared as empty JSON dictionary if not needed.

##Limitations
- For ARC only;
- NSJSONSerialization used in generated code for JSON data creation, so there is intermediate dictionary created before a data writing in a transport;
- You can not define global prefix for all the structs in generated code yet;
- No "date", "enum" etc. in atomic IDL types. Only int32, int64, double, string, bool, raw и rawstr. "raw" will be converted in NSDictionary from JSON dictionary and "rawstr" — in NSDictionary from JSON dictionary encoded in string (like this: "data": "{\"weird\":42,\"str\":\"yes\"}");
- Types importing system is weak and doesn't recognize and handle loops, diamonds and other tricks;
- No forwarding struct declaration;
- No readable error messages for parser and generator yet. 
