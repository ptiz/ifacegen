//
//  ifacegen_test_test.swift
//  ifacegen.test.test
//
//  Created by Evgeny Kamyshanov on 22.11.14.
//  Copyright (c) 2014 ptiz. All rights reserved.
//

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
        
        employee0 = OBCEmployee(name: "empl0", andTheId: 781341234, andPassport: self.pass, andDimension: 345.67, andChildren:[child])
        employee1 = OBCEmployee(name: "empl1", andTheId: 87245, andPassport: self.pass, andDimension: 623.76, andChildren:[child, child])
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
        
        XCTAssertNil(error, "Serialization was unsuccessful")
        
        let desEmployer = OBCEmployer(JSONData: data, error: &error)
        
        XCTAssertEqual(desEmployer.stuff.count, 2, "Data was not deserialized successfully")
        
        let desEmployee0 = desEmployer.stuff[0] as OBCEmployee
        let desEmployee1 = desEmployer.stuff[1] as OBCEmployee
        
        XCTAssertEqual(desEmployee0.name, "empl0", "Employee.name is wrong")
        XCTAssertTrue(desEmployee0.passport.theId == 786234, "Employee pass is wrong")
        XCTAssertTrue(desEmployee0.children.count == 1, "Children0 array is wrong" )
        XCTAssertTrue(desEmployee1.children.count == 2, "Children1 array is wrong")
        
        let desChild = desEmployee1.children[1] as OBCEmployeeChildrenItem
        XCTAssertEqual(desChild.name, "Mary", "Child name is wrong")
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
