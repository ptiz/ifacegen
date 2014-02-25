
#import <Foundation/Foundation.h>
#import "Transport.h"

@interface HTTPTransport : NSObject<Transport>

- (id)initWithURL:(NSURL*)url;
- (NSHTTPURLResponse*)currentResponse;

@property (nonatomic) NSInteger retriesCount;
@property (nonatomic) NSString* userAgent;

@end
