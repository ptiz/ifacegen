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

#import "ViewController.h"
#import "IFHTTPTransport.h"
#import "vk.h"

static NSString* const cellId = @"ViewControllerCellId";

@interface ViewController ()<UITableViewDataSource>

@property (strong, nonatomic) IBOutlet UITableView *tableView;
@property (strong, nonatomic) IBOutlet UITextField *userNameTextField;
@property (strong, nonatomic) IBOutlet UIButton *getWallButton;

@property (atomic, strong) NSArray* wallItems;

@property (nonatomic) vk* vkClient;

@end

@implementation ViewController

- (id)initWithCoder:(NSCoder *)aDecoder {

    self = [super initWithCoder:aDecoder];

    if ( self ) {

        self.wallItems = @[];

        NSURL* vkURL = [NSURL URLWithString:@"http://api.vk.com/method"];
        id<IFTransport> transport = [[IFHTTPTransport alloc] initWithURL:vkURL];
        self.vkClient = [[vk alloc] initWithTransport:transport];

    }
    return self;
}

- (void)viewDidLoad {
    [super viewDidLoad];
}

- (IBAction)getWallButtonPressed:(UIButton *)sender {

    [self.userNameTextField resignFirstResponder];

    NSString* userId = self.userNameTextField.text;
    if ( [userId length] == 0 ) {
        return;
    }

    __weak typeof(self) weakSelf = self;
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_BACKGROUND, 0), ^{

        weakSelf.getWallButton.enabled = NO;

        NSError* error;
        VkWallResponse* response = [weakSelf.vkClient vkWallWithOwnerId:userId
                                                           andCount:@"10"
                                                               andV:@"5.10"
                                                           andError:&error];

        if ( error ) {
            NSLog(@"%@", error);
        } else {
            weakSelf.wallItems = response.items;
        }

        dispatch_async(dispatch_get_main_queue(), ^{
            weakSelf.getWallButton.enabled = YES;
            [weakSelf.tableView reloadData];
        });
    });

}

#pragma mark - TableView

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return self.wallItems.count;
}

- (UITableViewCell*)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {

    UITableViewCell* cell = [tableView dequeueReusableCellWithIdentifier:cellId];
    if ( cell == nil ) {
        cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:cellId];
    }

    vkResponseItem* wallItem = self.wallItems[indexPath.row];
    cell.textLabel.text = [NSString stringWithFormat:@"From id: %lld", wallItem.fromId];
    if ( [wallItem.text length] > 0 ) {
        cell.detailTextLabel.text = wallItem.text;
    } else if ( [wallItem.theCopyHistory count] > 0 ) {
        vkResponseItemBase* copyHistoryItem = wallItem.theCopyHistory[0];
        cell.detailTextLabel.text = copyHistoryItem.text;
    }

    return cell;
}

@end
