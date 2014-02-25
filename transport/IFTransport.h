
#import <Foundation/Foundation.h>

@protocol IFTransport

- (void)setRequestParams:(NSDictionary*)params;
- (BOOL)writeAll:(NSData*)data prefix:(NSString*)prefix error:(NSError* __autoreleasing*)error;
- (NSData*)readAll;

@end
