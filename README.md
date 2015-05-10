# ifacegen

##What is it for
You need this tool, if you like me have to connect few RESTful services in every app and completely fed up with endless manual json dictionaries handling. Forget about error prone string literals comparing, you will have native classes and methods for remote services like if they were your local objects.

## What is it
ifacegen is a code generator, it simplifies using of existing REST+JSON APIs from Objective-C code. ifacegen makes native wrappers for remote service calls and JSON dictionaries. Simple IDL used for description of existing protocol. This is a fork from initial repo, that you can find at https://bitbucket.org/ifreefree/ifacegen

## What is it not
ifacegen is neither a general purpose serialization nor advanced networking tool. It only compiles IDL given and generates special Objective-C classes accordingly.

##Requirements
iOS+ARC, Python 2.7

##Limitations
- For ARC only;
- NSJSONSerialization used in generated code for JSON data creation, so there is intermediate dictionary created before a data writing in a transport;
- No "date", "enum" etc. in atomic IDL types. Only int32, int64, double, string, bool, raw и rawstr. "raw" will be converted in NSDictionary from JSON dictionary and "rawstr" — in NSDictionary from JSON dictionary encoded in string (like this: "data": "{\"weird\":42,\"str\":\"yes\"}");
- All fields in IDL struct are treated as optional. No errors are raised if the value does not exist for the field. 
- No readable error messages for parser and generator yet.

##Installation
```
pod 'ifacegen'
```

##Usage
```
$ python ifacegen.py [-h] [--prefix PREFIX] [-o OUTDIR] I [I ...]
```
- h shows help; 
- PREFIX is a string, ObjC namespace prefix that is added to a name of each class to be generated; 
- OUTDIR is a string, path to directory where the generated files to be placed. By default these files will be placed into a "gen-objc" subdirectory of working dir;
- I [I ...] are IDL file names to be processed. 

If you use Cocoapods to install the tool, you may want to add "Run Script" phase to your Build Phases, like this:
```
python Pods/ifacegen/generator/ifacegen.py <IDL file names> -o <output directory>
```

##Documentation and Example
Example can be found in the repo. Also see IDL description and a tutorial in [DOC file](DOC.md)

##ToDo
- Mandatory fields;
- Swift code generator;
- Parser and generator error handling improvement;
- CoreData support.
