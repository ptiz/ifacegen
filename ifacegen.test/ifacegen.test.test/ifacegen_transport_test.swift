//
//  ifacegen_transport_test.swift
//  ifacegen.test
//
//  Created by Evgenii Kamyshanov on 27.01.15.
//
//

import Foundation
import XCTest

class TestTransport: IFHTTPTransport {
    
    var checkURL: ((String?) -> ())?
    var checkInput: ((NSData?) -> ())?
    
    override init!(URL url: NSURL!) {
        super.init(URL: url)
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
        let response = "{\"response\":[{\"name\":\"John Doe\",\"id\":13,\"dimension\":13.1,\"passport\":{\"id\":12345,\"organization\":\"Org Inc.\" },\"children\":[{\"name\":\"John Doe J.\",\"birthdate\":8713452345}]}]}"
        return response.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true);
    }
}

class ifacegen_transport_test: XCTestCase {
    
    func testCall() {
        
        let testTransport = TestTransport(URL: NSURL(fileURLWithPath: "") )
        
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
                        XCTAssertTrue(filter2["payload"] as String == "filter2", "Input wasn't made well")
                    } else {
                        XCTAssert(false, "Input is nil")
                    }
                }
            }
        }

        let testService = OBCTest(transport: testTransport)
        let filter1 = OBCGetEmployeesFilterItem(payload: "filter1")
        let filter2 = OBCGetEmployeesFilterItem(payload: "filter2")
        let response = testService.getEmployeesWithToken("qwerty", andTimestamp: 13452345, andEmployerId: 9876345, andFilter: [filter1, filter2], andError: nil)
        
        XCTAssertEqual(response.count, 1, "Response objects count is wrong")
        
        let employee = response[0] as OBCEmployee
        XCTAssertEqual(employee.name, "John Doe", "Employee name is wrong in response")
    }
}
