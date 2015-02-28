//
//  IFServiceClient+Protected.h
//  ifacegen.test
//
//  Created by Evgeny Kamyshanov on 27.02.15.
//
//

#import <Foundation/Foundation.h>
#import "IFServiceClient.h"

@interface IFServiceClient(Protected)

- (NSError*)errorWithMessage:(NSString*)msg;

@property (nonatomic, readonly) id<IFTransport> transport;

@end
