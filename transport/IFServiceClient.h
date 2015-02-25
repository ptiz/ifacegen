//
//  IFServiceClient.h
//  ifacegen.test
//
//  Created by Evgeny Kamyshanov on 23.02.15.
//
//

#import <Foundation/Foundation.h>
#import "IFTransport.h"

@interface IFServiceClient : NSObject

- (instancetype)initWithTransport:(id<IFTransport>)transport NS_DESIGNATED_INITIALIZER;

@end
