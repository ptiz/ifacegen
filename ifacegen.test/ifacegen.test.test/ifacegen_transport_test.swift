/**
*	Created by Evgeny Kamyshanov on Jan, 2015
*	Copyright (c) 2014-2015 Evgeny Kamyshanov
*
*	Permission is hereby granted, free of charge, to any person obtaining a copy
*	of this software and associated documentation files (the "Software"), to deal
*	in the Software without restriction, including without limitation the rights
*	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
*	copies of the Software, and to permit persons to whom the Software is
*	furnished to do so, subject to the following conditions:
*
*	The above copyright notice and this permission notice shall be included in
*	all copies or substantial portions of the Software.
*
*	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
*	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
*	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
*	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
*	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
*	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
*	THE SOFTWARE.
**/

import Foundation
import XCTest

class TestTransport: IFHTTPTransport {
    
    var checkURL: ((NSURL?) -> ())?
    var checkInput: ((NSData?) -> ())?
    var checkCustomInput: ((Dictionary<String, AnyObject>?) -> ())?
    var checkHTTPMethod: ((IFHTTPMethod) -> ())?
    
    let responseFileName: String?
    
    init(_ responseFileName: String?) {
        self.responseFileName = responseFileName
        super.init(URL:NSURL(string: "http://localhost"))
    }
    
    override func writeAll(data: NSData!, endpoint: String!, method: IFHTTPMethod) throws {
        if let checkHTTPMethod = self.checkHTTPMethod {
            checkHTTPMethod( method )
        }
        
        if let checkURL = self.checkURL {
            let requestParamsString = self.buildURL(endpoint)
            checkURL(requestParamsString)
        }
        
        if let checkInput = self.checkInput, input = data {
            checkInput(input)
        }
    }
    
    override func readAll() -> NSData! {
        if let responseFileName = self.responseFileName {
            return NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource(responseFileName, ofType: "json")!)
        }
        return NSData()
    }
    
    func setCustomParams(params: Dictionary<String, AnyObject>) {
        self.checkCustomInput?(params)
    }
}

class ifacegen_transport_test: XCTestCase {
    
    func testCall() {
        
        let testTransport = TestTransport("test_transport_response")
        
        testTransport.checkURL = { (url) in
            if let checkUrl = url {
                XCTAssertEqual(checkUrl.absoluteString, "http://localhost/employees?token=qwerty&timestamp=13452345", "URL wasn't made well")
            } else {
                XCTAssert(false, "URL is nil")
            }
        }
        
        testTransport.checkInput = { (inputData) in
            if let input = inputData {
                if let json = (try? NSJSONSerialization.JSONObjectWithData(input, options:.AllowFragments)) as? [String : AnyObject] {
                    XCTAssertTrue((json["employer_id"] as? NSNumber)?.longLongValue == 9876345, "Input wasn't made well")
                    let filters: AnyObject? = json["filter"]
                    if let filter2 = filters?[1] as? Dictionary<String, AnyObject> {
                        XCTAssertTrue(filter2["payload"] as! String == "filter2", "Input wasn't made well")
                    } else {
                        XCTAssert(false, "Input is nil")
                    }
                }
            }
        }
        
        testTransport.checkCustomInput = { (param) in
            let complexParam = param?["complex_param"] as! Dictionary<String, AnyObject>?
            XCTAssertTrue(complexParam?["complex_field"] as? NSString == "complex field", "Custom complex parameter is wrong")

            let simpleParam = param?["simple_param"] as! NSNumber?
            XCTAssertTrue(simpleParam?.longLongValue == 13, "Custom simple parameter is wrong");
        }

        let testService = OBCTest(transport: testTransport)
        let filter1 = OBCGetEmployeesJsonArgsFilterItem(payload: "filter1")
        let filter2 = OBCGetEmployeesJsonArgsFilterItem(payload: "filter2")
        let complexParam = OBCGetEmployeesCustomParamsArgsComplexParam(complexField: "complex field")
        
        let response = try! testService.getEmployeesWithToken("qwerty", andTimestamp: 13452345, andComplexParam: complexParam, andSimpleParam: 13, andEmployerId: 9876345, andFilter: [filter1, filter2])
        
        XCTAssertEqual(response.count, 2, "Response objects count is wrong")
        
        let employee1 = response[0]
        XCTAssertEqual(employee1.name, "John Doe", "Employee1 name is wrong in response")
        XCTAssertEqual(employee1.passport.periods.count, 5, "Periods count is wrong for Employee1 passport")
        
        let employee2 = response[1]
        XCTAssertEqual(employee2.name, "Mary Doe", "Employee2 name is wrong in response")
    }
    
    func testHTTPCall() {
        
        let transport = TestTransport(nil)
        
        transport.checkHTTPMethod = { (method:IFHTTPMethod)->() in
            XCTAssert( method == .IFHTTPMETHOD_PUT, "HTTP method is wrong")
            print("HTTP method: \(method)")
        }
        
        let employee = try! OBCEmployee(JSONData: NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource("test_transport_employee", ofType: "json")!)!)
        XCTAssert(employee.age == 33.33, "Epmployee was not desirialized properly")
        
        let testService = OBCTest(transport: transport)
        testService.methodForPutWithEmployee(employee, andError: nil)
    }
    
    func testEdpointParams() {
        
        let transport = TestTransport("test_restful_parameters")
        
        transport.checkURL = { (url) in
            if let checkUrl = url {
                XCTAssertEqual(checkUrl.absoluteString, "http://localhost/users/johndoe123/repos?token=9712394867142", "URL wasn't made well")
            } else {
                XCTAssert(false, "URL is nil")
            }
        }
        
        let testService = OBCTest(transport: transport)
        let _ = try? testService.gitStarredReposWithUser("johndoe123", andToken:"9712394867142")

    }
}
