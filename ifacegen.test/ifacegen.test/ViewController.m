
#import "ViewController.h"
#import "HTTPTransport.h"
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
        NSObject<Transport>* transport = [[HTTPTransport alloc] initWithURL:vkURL];
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

    VkWallResponseItemsItem* wallItem = self.wallItems[indexPath.row];
    cell.textLabel.text = [NSString stringWithFormat:@"From id: %lld", wallItem.fromId];
    if ( [wallItem.text length] > 0 ) {
        cell.detailTextLabel.text = wallItem.text;
    } else if ( [wallItem.theCopyHistory count] > 0 ) {
        VkWallResponseItemsItemTheCopyHistoryItem* copyHistoryItem = wallItem.theCopyHistory[0];
        cell.detailTextLabel.text = copyHistoryItem.text;
    }

    return cell;
}

@end
