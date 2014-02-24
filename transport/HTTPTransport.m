
#import "HTTPTransport.h"
#import "HTTPTransport+Protected.h"

#ifdef DEBUG
#   define NSLog(...) NSLog(__VA_ARGS__)
#else
#   define NSLog(...)
#endif

@interface HTTPTransport()

@property (nonatomic) NSURL* rootURL;
@property (nonatomic) NSData* currentAnswer;
@property (nonatomic) NSHTTPURLResponse* curentResponse;
@property (nonatomic) NSDictionary* currentRequestParams;

@end

@implementation HTTPTransport

- (id)initWithURL:(NSURL*)url {
    if ( self = [super init] ) {
        self.rootURL = [url copy];
        self.retriesCount = 3;

        NSString* appVersion = [[[NSBundle mainBundle] infoDictionary] objectForKey:@"CFBundleVersion"];
        NSString* appName = [[NSBundle mainBundle] bundleIdentifier];
        self.userAgent = [NSString
                     stringWithFormat:@"%@ %@", appName, appVersion];
    }
    return self;
}

- (void)setRequestParams:(NSDictionary*)params {
    self.currentRequestParams = params;
}

#pragma mark - Transport proto

- (BOOL)writeAll:(NSData*)data prefix:(NSString*)prefix error:(NSError* __autoreleasing*)error {

    *error = nil;

    self.currentAnswer = nil;
    self.curentResponse = nil;

    if ( prefix == nil ) {
        prefix = @"";
    }

    NSURL* requestURL;
    if ( [prefix length] && [prefix characterAtIndex:0] == ':' ) {
        requestURL = [NSURL URLWithString:
                      [[self.rootURL absoluteString] stringByAppendingString:prefix]];
    } else {
       requestURL = [self.rootURL URLByAppendingPathComponent:prefix];
    }

    NSString* requestParamsString;
    if ( self.currentRequestParams != nil ) {
        requestParamsString = [self buildRequestParamsString:self.currentRequestParams];
        requestURL =
            [NSURL URLWithString:
             [[requestURL absoluteString] stringByAppendingString:requestParamsString]];
    }

    NSMutableURLRequest* request = [self prepareRequestWithURL:requestURL data:data];

    NSHTTPURLResponse* response;
    NSInteger retriesCounter = self.retriesCount;
    while ( retriesCounter-- ) {
        self.currentAnswer = [NSURLConnection sendSynchronousRequest:request
                                              returningResponse:&response
                                                          error:error];

        if ( *error == nil || [self shouldBreakOnError:*error] ) {
            break;
        }

        sleep(10);
    }

    if ( *error != nil ) {
        return NO;
    }

    self.currentRequestParams = nil;
    self.curentResponse = response;

    NSLog(@"Response code: %d", [self.curentResponse statusCode]);

    if ( [self.curentResponse statusCode] < 200 || [self.curentResponse statusCode] > 202 ) {

        NSDictionary* userInfo = @{ @"NSLocalizedDescriptionKey": [NSHTTPURLResponse localizedStringForStatusCode:
                                                                   [self.curentResponse statusCode]
                                                                   ]};

        *error = [[NSError alloc] initWithDomain:NSStringFromClass([self class])
                                            code:[self.curentResponse statusCode]
                                        userInfo:userInfo];

        return NO;
    }

    if ( self.currentAnswer == nil || [self.currentAnswer length] == 0 ) {
        return YES;
    }

    NSLog(@"Response body: %@", [[NSString alloc] initWithBytes:[self.currentAnswer bytes]
                                                         length:[self.currentAnswer length]
                                                       encoding:NSUTF8StringEncoding]
                                                       );

    return YES;
}

- (NSData*)readAll {
    return self.currentAnswer;
}

- (NSHTTPURLResponse*)currentResponse {
    return self.curentResponse;
}

#pragma mark - Overrides

- (NSMutableURLRequest*)prepareRequestWithURL:(NSURL*)url data:(NSData*)data {

    NSMutableURLRequest *request = [[NSMutableURLRequest alloc] initWithURL:url];
    NSLog(@"Request: %@", request);

    [request setHTTPMethod:( data == nil ? @"GET" : @"POST" )];

    if ( data != nil ) {
        [request setHTTPBody: data];
    }

    if ( request.HTTPBody != nil ) {
        [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
        [request setValue:[NSString stringWithFormat:@"%d", [request.HTTPBody length]]
       forHTTPHeaderField:@"Content-Length"];

        NSString* json = [[NSString alloc] initWithBytes:[request.HTTPBody bytes]
                                                  length:[request.HTTPBody length]
                                                encoding:NSUTF8StringEncoding];

        NSLog(@"HTTPTransport to be written in URL \"%@\": %@", [request.URL absoluteString], json);
    }

    [request setValue:self.userAgent forHTTPHeaderField:@"User-Agent"];

    return request;
}

- (NSString*)buildRequestParamsString:(NSDictionary*)requestParams {

    NSString* reqParm = [NSString string];
    NSString* separator = @"?";

    for ( NSString* key in [self.currentRequestParams allKeys] ) {
    
        NSString* keyValue = [self.currentRequestParams objectForKey:key];
        if ( [keyValue isEqual:[NSNull null]] || [keyValue length] == 0 ) {
            continue;
        }

        reqParm = [reqParm stringByAppendingString:separator];
        separator = @"&";

        NSString* keyParm =
            [NSString stringWithFormat:@"%@=%@", key, keyValue];
        reqParm = [reqParm stringByAppendingString:
                   [keyParm stringByAddingPercentEscapesUsingEncoding:NSUTF8StringEncoding]];
    }

    return reqParm;
}

- (BOOL)shouldBreakOnError:(NSError*)error {

    // connection lost, retry doesn't needed
    return [[error domain] isEqualToString:NSURLErrorDomain] &&
        ( [error code] == NSURLErrorNetworkConnectionLost ||
         [error code] == NSURLErrorNotConnectedToInternet );
}

@end