/**
*   Created by Evgeny Kamyshanov on March, 2014
*   Copyright (c) 2013-2014 BEFREE Ltd. 
*
*   Permission is hereby granted, free of charge, to any person obtaining a copy
*   of this software and associated documentation files (the "Software"), to deal
*   in the Software without restriction, including without limitation the rights
*   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
*   copies of the Software, and to permit persons to whom the Software is
*   furnished to do so, subject to the following conditions:
*
*   The above copyright notice and this permission notice shall be included in
*   all copies or substantial portions of the Software.
*
*   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
*   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
*   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
*   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
*   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
*   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
*   THE SOFTWARE.
**/

#import "IFHTTPTransport.h"
#import "IFHTTPTransport+Protected.h"

#ifdef DEBUG
#   define IFDebugLog(...) NSLog(__VA_ARGS__)
#else
#   define IFDebugLog(...)
#endif

NSString* const IFHTTPTransportErrorDomain = @"com.ifree.ifacegen.transport.httperror";

@interface IFHTTPTransport()

@property (nonatomic, copy) NSURL* rootURL;
@property (nonatomic, copy) NSData* currentAnswer;
@property (nonatomic, copy) NSHTTPURLResponse* curentResponse;
@property (nonatomic, copy) NSDictionary* currentRequestParams;

@end

@implementation IFHTTPTransport

- (id)initWithURL:(NSURL*)url {
    if ( self = [super init] ) {
        self.rootURL = url;
        self.retriesCount = 3;

        NSString* appVersion = [[[NSBundle mainBundle] infoDictionary] objectForKey:@"CFBundleVersion"];
        NSString* appName = [[NSBundle mainBundle] bundleIdentifier];
        self.userAgent = [NSString
                     stringWithFormat:@"%@ %@", appName, appVersion];
    }
    return self;
}

- (void)setUrlParams:(NSDictionary*)params {
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

    IFDebugLog(@"Response code: %ld", (long)[self.curentResponse statusCode]);

    if ( [self.curentResponse statusCode] < 200 || [self.curentResponse statusCode] > 202 ) {

        NSDictionary* userInfo = @{ @"NSLocalizedDescriptionKey": [NSHTTPURLResponse localizedStringForStatusCode:
                                                                   [self.curentResponse statusCode]
                                                                   ]};

        *error = [[NSError alloc] initWithDomain:IFHTTPTransportErrorDomain
                                            code:[self.curentResponse statusCode]
                                        userInfo:userInfo];

        return NO;
    }

    if ( self.currentAnswer == nil || [self.currentAnswer length] == 0 ) {
        return YES;
    }

    IFDebugLog(@"Response body: %@", [[NSString alloc] initWithBytes:[self.currentAnswer bytes]
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
    IFDebugLog(@"Request: %@", request);

    [request setHTTPMethod:( data == nil ? @"GET" : @"POST" )];

    if ( data != nil ) {
        [request setHTTPBody: data];
    }

    if ( request.HTTPBody != nil ) {
        [request setValue:@"application/json" forHTTPHeaderField:@"Content-Type"];
        [request setValue:[NSString stringWithFormat:@"%lu", (unsigned long)[request.HTTPBody length]]
       forHTTPHeaderField:@"Content-Length"];

        NSString* json = [[NSString alloc] initWithBytes:[request.HTTPBody bytes]
                                                  length:[request.HTTPBody length]
                                                encoding:NSUTF8StringEncoding];

        IFDebugLog(@"HTTPTransport to be written in URL \"%@\": %@", [request.URL absoluteString], json);
    }

    [request setValue:self.userAgent forHTTPHeaderField:@"User-Agent"];

    return request;
}

- (NSString*)buildRequestParamsString:(NSDictionary*)requestParams {

    NSString* reqParm = [NSString string];
    NSString* separator = @"?";

    for ( NSString* key in [self.currentRequestParams allKeys] ) {
    
        NSString* keyValue = [NSString stringWithFormat:@"%@", [self.currentRequestParams objectForKey:key]];
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
