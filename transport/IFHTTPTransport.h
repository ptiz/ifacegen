
#import <Foundation/Foundation.h>
#import "IFTransport.h"

extern NSString* const IFHTTPTransportErrorDomain;

@interface IFHTTPTransport : NSObject<IFTransport>

- (id)initWithURL:(NSURL*)url;
- (NSHTTPURLResponse*)currentResponse;

@property (nonatomic) NSInteger retriesCount;
@property (nonatomic) NSString* userAgent;

@end
