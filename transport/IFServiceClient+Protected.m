//
//  IFServiceClient+Protected.m
//  ifacegen.test
//
//  Created by Evgeny Kamyshanov on 27.02.15.
//
//

#import "IFServiceClient+Protected.h"

@implementation IFServiceClient(Protected)

@dynamic transport;

- (NSError*)errorWithMessage:(NSString*)msg {
    return [NSError errorWithDomain:NSStringFromClass([self class]) code:0 userInfo:@{NSLocalizedDescriptionKey: msg}];
}

@end
