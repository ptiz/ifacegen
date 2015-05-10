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
"endpoint": "/place/details/json",
"url_params": {
    "key":"string",
    "reference": "string",    
    "sensor": "string"   
  },
"response": "GoogleDetailsResult" 
}

]}
```

The "url_params" field describes URL parameters.

Then we need some codegen:
```
$ python ifacegen.py GoogleClient.json
```

After that we have two files: GoogleClient.h and GoogleClient.m. This is how GoogleClient.h looks like:
```objc
@implementation GoogleLocation

- (instancetype)initWithLat:(double_t)lat
	andLng:(double_t)lng {
	if (self=[super init]) {
		_lat = lat;
		_lng = lng;
	}
	return self;
}

- (NSDictionary*)dictionaryWithError:(NSError* __autoreleasing*)error {
	return @{
		@"lat":@(self.lat),
		@"lng":@(self.lng)
	};
}

- (NSData*)dumpWithError:(NSError* __autoreleasing*)error {
	NSDictionary* dict = [self dictionaryWithError:error];
	if (*error) return nil;
	else return [NSJSONSerialization dataWithJSONObject:[self dictionaryWithError:error] options:jsonFormatOption error:error];
}

- (void)readDictionary:(NSDictionary*)dict withError:(NSError* __autoreleasing*)error {
	id tmp;
	self.lat = ( tmp = dict[@"lat"], [tmp isEqual:[NSNull null]] ? 0.0 : ((NSNumber*)tmp).doubleValue );
	self.lng = ( tmp = dict[@"lng"], [tmp isEqual:[NSNull null]] ? 0.0 : ((NSNumber*)tmp).doubleValue );
}

- (instancetype)initWithDictionary:(NSDictionary*)dictionary error:(NSError* __autoreleasing*)error {
	if ( dictionary == nil ) return nil;
	if (self = [super init]) {
		[self readDictionary:dictionary withError:error];
		if ( error && *error != nil ) self = nil;
	}
	return self;
}
```

That's all. Now you can create a client and start making calls! Somewhere in your code:
```objc
#import "IFHTTPTransport.h"
//...
  NSString* googleAPIHost = @"https://maps.googleapis.com/maps/api";
  self.transport = [[IFHTTPTransport alloc] initWithURL:[NSURL URLWithString:googleAPIHost]];
  self.google = [[GoogleClient alloc] initWithTransport:self.transport];
//...
  NSError* error;

  GoogleDetailsResult* result =
  [self.google placeDetailsWithKey:key
                      andReference:ref
                         andSensor:@"true"
                          andError:&error];
```

Transport protocol (and its out-of-the-box realization IFHTTPTransport) used by generated classes to make network calls has only synchronous methods. No blocks of callback delegates at all. Client code is free to wrap these calls in async manner according its needs.

##ifacegen console tool
Usage: 
```
$ python ifacegen.py [-h] [--prefix PREFIX] [-o OUTDIR] [--category CATEGORY] I [I ...]
```
- h shows help; 
- PREFIX is a string, ObjC namespace prefix that is added to a name of each class to be generated; 
- OUTDIR is a string, path to directory where the generated files to be placed. By default these files will be placed into a "gen-objc" subdirectory of working dir;
- CATEGORY is a string, suffix for category in which all serilaization methods will be placed;
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
{
"struct": "User",
"typedef": {
	"nested": {
		"field": "int32"
	}
    }
}
```
will be translated in
```objc
@interface UserNested: NSObject
- (instancetype)initWithField:(int32_t)field;
...
@property (nonatomic) int32_t field;
@end

@interface User: NSObject
- (instancetype)initWithNested:(UserNested*)nested;
...
@property (nonatomic) UserNested* nested;
@end
```

Arrays are also supported. Following code will be translated into class with "stringItems" property of type NSArray*:
```json
"typedef": {
	"string_items":["User"]
}
```
will be translated in
```objc
@property (nonatomic) NSArray* /*User*/ stringItems;
```

Field names like "id" and "void" will be decorated in code with "the" prefix, so "id" changes into "theId". The same happens with fields which names starting with "new", "alloc", "copy" and "mutableCopy". Names in code also will be converted in CamelCase if they_are_not_yet.

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
"<method>": "<procedure name for ObjC>",
"endpoint": "<remote service endpoint to be combined into resulting URL>",
"url_params": {
		"<parameter to be passed in url>": <typename>,
		...
	},
"request" : <any explicit structure name or implicit struct declaration in brackets>,
"response": <any explicit structure name or implicit struct declaration in brackets>,
<custom params section>: <any explicit structure name or implicit struct declaration in brackets>
...
}
```
"method" can be one of HTTP methods: "get", "head", "post", "put", "delete", "patch", "options" or "trace", or "procedure" for automatic mode.

"endpoint" can contain parameters also, they should be surrounded by "${}":
```json
{
"get": "userDocs",
"endpoint": "api/user/${userName}/docs",
"response": "UserDoc"
}
```
will be translated in RPC method:
```objc
- (UserDoc*)userDocsWithUserName:(NSString*)userName;
```

"url_params" field describes parameters to be passed as URL parts. 
"request" field used for passing parameters throug JSON data. 

"custom params section" may contain any IDL type declarations. Custom section requires the transport responds to corresponding selector:
```json
"custom_params": { "User" }
```
requires transport responds to
```objc
- (void)customParams:(NSDictionary*)parameters;
```
Obviously you should iherit from IFHTTPTransport or create class that conforms IFTransport protocol to support custom parameters. Please refer IFHTTPTransport (Protected) category for methods that intentended to be used in successors (inc. testing).

Any of these fields can be avoided.

##Testing
You should inherit custom transport for passing in generated RPC classes, that can provide test data as a response. Refer ifacegen.test.test project for [Swift] implementation.

##Limitations
- For ARC only;
- NSJSONSerialization used in generated code for JSON data creation, so there is intermediate dictionary created before a data writing in a transport;
- IFHTTPTransport uses NSURLConnection;
- No "date", "enum" etc. in atomic IDL types. Only int32, int64, double, string, bool, raw и rawstr. "raw" will be converted in NSDictionary from JSON dictionary and "rawstr" — in NSDictionary from JSON dictionary encoded in string (like this: "data": "{\"weird\":42,\"str\":\"yes\"}");
- Types importing system is weak and doesn't recognize and handle loops, diamonds and other tricks;
- No readable error messages for parser and generator yet. 
