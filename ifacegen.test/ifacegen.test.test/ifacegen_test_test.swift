/**
*	Created by Evgeny Kamyshanov on Nov, 2014
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

class ifacegen_test_test: XCTestCase {

    var pass:OBCHumanPassport!
    var employee0:OBCEmployee!
    var employee1:OBCEmployee!
    var employer:OBCEmployer!
    
    var department:OBCDepartment!
    var internalDepartment:OBCDepartment!
    
    override func setUp() {
        super.setUp()
        
        pass = OBCHumanPassport()
        pass.theId = 786234
        pass.organization = "10 OM"

        let child = OBCEmployeeChildrenItem()
        child.name = "Mary"
        child.birthdate = Int64(NSDate().timeIntervalSince1970)
        
        employee0 = OBCEmployee(name: "empl0", andTheId: 781341234, andMarried: true, andPassport: self.pass, andAge: 345.67, andEmploymentRec: [ [OBCEmployeeEmploymentRecItemItem(begin: 1, andEnd: 2)], [OBCEmployeeEmploymentRecItemItem(begin: 3, andEnd: 4), OBCEmployeeEmploymentRecItemItem(begin: 5, andEnd: 6)] ], andEmploymentData: ["data":"any"], andChildren: [child])

        employee1 = OBCEmployee(name: "empl1", andTheId: 87245, andMarried:false, andPassport: self.pass, andAge: 623.76, andEmploymentRec:[], andEmploymentData:["any":"data"], andChildren:[child, child])
        
        employer = OBCEmployer(stuff: [self.employee0, self.employee1], andInfo: ["review":"passed"])
        
        internalDepartment = OBCDepartment(name: "Testers sub-dept.", andEmployees: [self.employee0], andDepartments: nil)
        department = OBCDepartment(name: "Research dept.", andEmployees: [self.employee0, self.employee1], andDepartments: [internalDepartment])
    }
    
    override func tearDown() {
        super.tearDown()
    }
    
    func testSerialization() {
        
        var error:NSError?
        let data = self.employer.dumpWithError(&error)
//        let dataStr = NSString(data: data, encoding: NSUTF8StringEncoding);
//        NSLog("%@", dataStr!);
        
        XCTAssertNil(error, "Serialization was unsuccessful")
        
        let desEmployer = OBCEmployer(JSONData: data, error: &error)
        
        XCTAssertEqual(desEmployer.stuff.count, 2, "Data was not deserialized successfully")
        
        let desEmployee0 = desEmployer.stuff[0] as OBCEmployee
        let desEmployee1 = desEmployer.stuff[1] as OBCEmployee
        
        XCTAssertEqual(desEmployee0.name, "empl0", "Employee.name is wrong")
        XCTAssertTrue(desEmployee0.passport.theId == 786234, "Employee pass is wrong")
        XCTAssertTrue(desEmployee0.children.count == 1, "Children0 array is wrong" )
        XCTAssertTrue(desEmployee1.children.count == 2, "Children1 array is wrong")
        XCTAssertTrue(desEmployee0.employmentRec.count == 2, "Employment record is wrong for Employee0")
        
        let array = desEmployee0.employmentRec[1] as [AnyObject]
        let itemItem = array[1] as OBCEmployeeEmploymentRecItemItem
        XCTAssertTrue( itemItem.begin == 5, "Employee0.employmentRec[1][1].begin is wrong")
        
        let desChild = desEmployee1.children[1] as OBCEmployeeChildrenItem
        XCTAssertEqual(desChild.name, "Mary", "Child name is wrong")
        
        let employmentDataValue = desEmployee0.employmentData["data"] as String
        XCTAssertEqual(employmentDataValue, "any", "employmentData is wrong for Employee0")
    }
    
    func testRecursiveTypes() {
        
        var error:NSError?
        let data = self.department.dumpWithError(&error)
        
        XCTAssertNil(error, "Serialization was unsuccessful")
        
        let desDepartment = OBCDepartment(JSONData: data, error: &error)
        
        XCTAssertEqual(desDepartment.departments.count, 1, "Data was not deserialized successfully")
    }
    
    func testErroneousSerialization() {
        
        let message = "{\"stuff\":[{\"wrong_value\":13}]}"
        let messageData = message.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true);

        var error:NSError?
        let employer = OBCEmployer(JSONData: messageData, error: &error)
        
        XCTAssertEqual(employer.stuff.count, 1, "Data was not deserialized successfully")
        XCTAssertTrue(employer.info == nil, "Employer info is wrong")
        
        let wrongMessage = "{\"stuff\":[{\"wrong_value\":13}"
        let wrongMessageData = wrongMessage.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true)
        
        let wrongEmployer = OBCEmployer(JSONData: wrongMessageData, error: &error)
        
        XCTAssertNil(wrongEmployer, "Struct was initialized with wrong data")
    }
}
