//
//  IFServiceClient.m
//  ifacegen.test
//
//  Created by Evgeny Kamyshanov on 23.02.15.
//
//

#import "IFServiceClient.h"

@interface IFServiceClient()
@property (nonatomic) id<IFTransport> transport;
@end

@implementation IFServiceClient

- (instancetype)initWithTransport:(id<IFTransport>)trans {
    if ( self = [super init] ) {
        _transport = trans;
    }
    return self;
}
- (NSError*)errorWithMessage:(NSString*)msg {
    return [NSError errorWithDomain:NSStringFromClass([self class]) code:0 userInfo:@{NSLocalizedDescriptionKey: msg}];
}

@end
