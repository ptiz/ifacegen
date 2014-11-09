# ifacegen

## What it is
ifacegen is a code generator, it simplifies using of existing REST+JSON APIs from Objective-C code. ifacegen makes native wrappers for remote service calls and JSON dictionaries. Simple IDL used for description of existing protocol. This is a fork from initial repo, that you can find at https://bitbucket.org/ifreefree/ifacegen

## What is not
ifacegen is not general purpose serialization tool. It's only compiles IDL given and generates special Objective-C classes accordingly. ifacegen doesn't support JSON Schema because of it's verbosity.

##Requirements
iOS+ARC, Python 2.7

##Limitations
- For ARC only;
- NSJSONSerialization used in generated code for JSON data creation, so there is intermediate dictionary created before a data writing in a transport;
- No "date", "enum" etc. in atomic IDL types. Only int32, int64, double, string, bool, raw и rawstr. "raw" will be converted in NSDictionary from JSON dictionary and "rawstr" — in NSDictionary from JSON dictionary encoded in string (like this: "data": "{\"weird\":42,\"str\":\"yes\"}");
- No forwarding struct declaration;
- No readable error messages for parser and generator yet.

##Installation
    pod 'ifacegen', :git => 'https://github.com/ptiz/ifacegen.git'

##Usage
```
$ python ifacegen.py [-h] [--prefix PREFIX] [-o OUTDIR] I [I ...]
```
- h shows help; 
- PREFIX is a string, ObjC namespace prefix that is added to a name of each class to be generated; 
- OUTDIR is a string, path to directory where the generated files to be placed. By default these files will be placed into a "gen-objc" subdirectory of working dir;
- I [I ...] are IDL file names to be processed. 

Example can be found in the repo. Also see a tutorial in [DOC file](DOC.md)
