
#import "HTTPTransport.h"

@interface HTTPTransport (Protected)

- (NSMutableURLRequest*)prepareRequestWithURL:(NSURL*)url data:(NSData*)data;
- (NSString*)buildRequestParamsString:(NSDictionary*)requestParams;
- (BOOL)shouldBreakOnError:(NSError*)error;

@end