//
//  ifacegen_test_test.swift
//  ifacegen.test.test
//
//  Created by Evgeny Kamyshanov on 22.11.14.
//  Copyright (c) 2014 ptiz. All rights reserved.
//

import Cocoa
import XCTest

class ifacegen_test_test: XCTestCase {

    var pass:OBCEmployeePassport!
    var employee0:OBCEmployee!
    var employee1:OBCEmployee!
    var employer:OBCEmployer!
    
    override func setUp() {
        super.setUp()
        
        pass = OBCEmployeePassport()
        pass.theId = 786234
        pass.organization = "10 OM"

        let child = OBCEmployeeChildrenItem()
        child.name = "Mary"
        child.birthdate = Int64(NSDate().timeIntervalSince1970)
        
        employee0 = OBCEmployee(name: "empl0", andTheId: 781341234, andDimension: 345.67, andPassport: self.pass, andChildren:[child])
        employee1 = OBCEmployee(name: "empl1", andTheId: 87245, andDimension: 623.76, andPassport: self.pass, andChildren:[child, child])
        employer = OBCEmployer(stuff: [self.employee0, self.employee1], andInfo: ["review":"passed"])
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
    
}
