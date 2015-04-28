/**
*	Created by Anton Davydov on Apr, 2015
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

class TestSwiftTransport: IFHTTPTransport {

    var checkURL: ((String?) -> ())?
    var checkInput: ((NSData?) -> ())?
    var checkCustomInput: ((Dictionary<String, AnyObject>?) -> ())?
    var checkHTTPMethod: ((IFHTTPMethod) -> ())?

    let responseFileName: String?

    init(ResponseFileName responseFileName: String?) {
        self.responseFileName = responseFileName
        super.init(URL:NSURL(string: ""))
    }

    override func writeAll(data: NSData!, prefix: String!, method: IFHTTPMethod, error: NSErrorPointer) -> Bool {
        if let checkHTTPMethod = self.checkHTTPMethod {
            checkHTTPMethod( method )
        }

        return true
    }

    override func writeAll(data: NSData!, prefix: String!, error: NSErrorPointer) -> Bool {

        if let requestParams = self.currentRequestParams {
            let requestParamsString = self.buildRequestParamsString(requestParams)
            self.checkURL?(requestParamsString)
        }

        if let input = data {
            self.checkInput?(input)
        }

        return true
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

class ifacegen_swift_transport_test: XCTestCase {

    func testCall() {

        let testTransport = TestSwiftTransport(ResponseFileName: "test_transport_response")

        testTransport.checkURL = { (urlString) in
            if let url = urlString {
                XCTAssertEqual(url, "?token=qwerty&timestamp=13452345", "URL wasn't made well")
            } else {
                XCTAssert(false, "URL is nil")
            }
        }

        testTransport.checkInput = { (inputData) in
            if let input = inputData {
                if let json = NSJSONSerialization.JSONObjectWithData(input, options:.AllowFragments, error: nil) as? [String : AnyObject] {
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

        let testService = test(transport: testTransport)
        let filter1 = getEmployeesJsonArgsFilterItem(payload: "filter1")
        let filter2 = getEmployeesJsonArgsFilterItem(payload: "filter2")
        let complexParam = getEmployeesCustomParamsArgsComplexParam(complexField: "complex field")

        var error: NSError?
        let response = testService.getEmployees("qwerty", timestamp: 13452345, complexParam: complexParam, simpleParam: 13, employerId: 9876345, filter: [filter1, filter2], error: &error)

        XCTAssertEqual(response!.count, 2, "Response objects count is wrong")

        let employee1 = response![0]
        XCTAssertEqual(employee1.name!, "John Doe", "Employee1 name is wrong in response")
        XCTAssertEqual(employee1.passport!.periods!.count, 5, "Periods count is wrong for Employee1 passport")

        let employee2 = response![1]
        XCTAssertEqual(employee2.name!, "Mary Doe", "Employee2 name is wrong in response")
        XCTAssertTrue(employee2.passport!.periods == nil, "Periods count is wrong for Employee2 passport")
    }

    func testHTTPCall() {

        let transport = TestSwiftTransport(ResponseFileName: nil)

        transport.checkHTTPMethod = { (method:IFHTTPMethod)->() in
            XCTAssert( method == .IFHTTPMETHOD_PUT, "HTTP method is wrong")
            println("HTTP method: \(method)")
        }
        var error: NSError?
        let employee = Employee(jsonData: NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource("test_transport_employee", ofType: "json")!), error: &error)
        XCTAssert(employee!.age == 33.33, "Epmployee was not desirialized properly")

        let testService = test(transport: transport)
        testService.methodForPut(employee, error: &error)
    }
}
