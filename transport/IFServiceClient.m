//
//  IFServiceClient.m
//  ifacegen.test
//
//  Created by Evgeny Kamyshanov on 23.02.15.
//
//

#import "IFServiceClient.h"

@interface IFServiceClient()
@property (nonatomic, readwrite) id<IFTransport> transport;
@end

@implementation IFServiceClient

- (instancetype)initWithTransport:(id<IFTransport>)trans {
    if ( self = [super init] ) {
        _transport = trans;
    }
    return self;
}

@end
