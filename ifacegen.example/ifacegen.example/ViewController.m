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
#import "git.h"

static NSString* const cellId = @"ViewControllerCellId";

@interface ViewController ()<UITableViewDataSource>

@property (strong, nonatomic) IBOutlet UITableView *tableView;
@property (strong, nonatomic) IBOutlet UITextField *userNameTextField;
@property (strong, nonatomic) IBOutlet UIButton *getReposButton;
@property (strong, nonatomic) IBOutlet UILabel *userLabel;
@property (strong, nonatomic) IBOutlet UILabel *userEmailLabel;

@property (atomic, strong) NSArray* userRepos;

@property (nonatomic) git* gitClient;

@end

@implementation ViewController

- (id)initWithCoder:(NSCoder *)aDecoder {

    self = [super initWithCoder:aDecoder];

    if ( self ) {

        self.userRepos = @[];

        NSURL* gitURL = [NSURL URLWithString:@"https://api.github.com"];
        id<IFTransport> transport = [[IFHTTPTransport alloc] initWithURL:gitURL];
        self.gitClient = [[git alloc] initWithTransport:transport];

    }
    return self;
}

- (void)viewDidLoad {
    [super viewDidLoad];
}

- (IBAction)getWallButtonPressed:(UIButton *)sender {

    [self.userNameTextField resignFirstResponder];

    NSString* userName = self.userNameTextField.text;
    if ( [userName length] == 0 ) {
        return;
    }

    __weak typeof(self) weakSelf = self;
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_BACKGROUND, 0), ^{

        weakSelf.getReposButton.enabled = NO;
        weakSelf.userRepos = @[];
        
        NSError* error;
        GitPublicUser* userInfo = [weakSelf.gitClient userWithUserName:userName andError:&error];
        if (!error) {
            weakSelf.userRepos = [weakSelf.gitClient reposWithUserName:userName andError:&error];
        }

        if ( error ) {
            dispatch_async(dispatch_get_main_queue(), ^{
                [[[UIAlertView alloc] initWithTitle:@"Error"
                                           message:error.localizedDescription
                                          delegate:nil
                                 cancelButtonTitle:@"OK"
                                 otherButtonTitles:nil] show];
            });

        }
        
        dispatch_async(dispatch_get_main_queue(), ^{
            weakSelf.getReposButton.enabled = YES;
            weakSelf.userLabel.text = userInfo.name;
            weakSelf.userEmailLabel.text = userInfo.email;
            [weakSelf.tableView reloadData];
        });
    });

}

#pragma mark - UITableViewDataSource

- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    return self.userRepos.count;
}

- (UITableViewCell*)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {

    UITableViewCell* cell = [tableView dequeueReusableCellWithIdentifier:cellId];
    if ( cell == nil ) {
        cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:cellId];
    }

    GitRepo* repo = self.userRepos[indexPath.row];
    
    cell.textLabel.text = repo.name;
    cell.detailTextLabel.text = [NSString stringWithFormat:@"Forks: %d, issues: %d, watchers: %d", repo.forks, repo.openIssues, repo.watchers];

    return cell;
}

@end
