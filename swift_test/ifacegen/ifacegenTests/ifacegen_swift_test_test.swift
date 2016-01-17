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

class ifacegen_swift_test_test: XCTestCase {
    var pass: HumanPassport!
    var employee0: Employee!
    var employee1: Employee!
    var employer: Employer!

    var department:Department!
    var internalDepartment:Department!

    override func setUp() {
        super.setUp()

        pass = HumanPassport()
        pass.theId = 786234
        pass.organization = "10 OM"

        let child = EmployeeChildrenItem()
        child.name = "Mary"
        child.birthdate = Int64(NSDate().timeIntervalSince1970)

        employee0 = Employee(name: "empl0", theId: 781341234, married: true, passport: self.pass, age: 345.67, employmentRec: [ [EmployeeEmploymentRecItemItem(begin: 1, end: 2)], [EmployeeEmploymentRecItemItem(begin: 3, end: 4), EmployeeEmploymentRecItemItem(begin: 5, end: 6)] ], employmentData: ["data":"any"], children: [child])

        employee1 = Employee(name: "empl1", theId: 87245, married:false, passport: self.pass, age: 623.76, employmentRec:[], employmentData:["any":"data"], children:[child, child])

        employer = Employer(stuff: [self.employee0, self.employee1], info: ["review":"passed"])

        internalDepartment = Department(name: "Testers sub-dept.", employees: [self.employee0], departments: nil)
        department = Department(name: "Research dept.", employees: [self.employee0, self.employee1], departments: [internalDepartment])
    }

    override func tearDown() {
        super.tearDown()
    }

    func testSerialization() {
        var error: NSError?
        let data = self.employer.dump(&error)

        XCTAssertNil(error, "Serialization was unsuccessful")

        let desEmployer = Employer(jsonData: data, error: &error)

        XCTAssertEqual(desEmployer!.stuff!.count, 2, "Data was not deserialized successfully")

        let desEmployee0 = desEmployer!.stuff![0]
        let desEmployee1 = desEmployer!.stuff![1]

        XCTAssertEqual(desEmployee0.name, "empl0", "Employee.name is wrong")
        XCTAssertTrue(desEmployee0.passport!.theId == 786234, "Employee pass is wrong")
        XCTAssertTrue(desEmployee0.children!.count == 1, "Children0 array is wrong" )
        XCTAssertTrue(desEmployee1.children!.count == 2, "Children1 array is wrong")
        XCTAssertTrue(desEmployee0.employmentRec!.count == 2, "Employment record is wrong for Employee0")

        let array = desEmployee0.employmentRec![1]
        let itemItem = array[1]
        XCTAssertTrue( itemItem.begin == 5, "Employee0.employmentRec[1][1].begin is wrong")

        let desChild = desEmployee1.children![1]
        XCTAssertEqual(desChild.name, "Mary", "Child name is wrong")

        let employmentDataValue = desEmployee0.employmentData!["data"] as! String
        XCTAssertEqual(employmentDataValue, "any", "employmentData is wrong for Employee0")
    }

    func testRecursiveTypes() {
        var error: NSError?
        let data = self.department.dump(&error)

        XCTAssertNil(error, "Serialization was unsuccessful")

        let desDepartment = Department(jsonData: data, error: &error)

        XCTAssertEqual(desDepartment!.departments!.count, 1, "Data was not deserialized successfully")
    }

    func testErroneousSerialization() {
        let message = "{\"stuff\":[{\"wrong_value\":13}]}"
        let messageData = message.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true);

        var error:NSError?
        let employer = Employer(jsonData: messageData, error: &error)

        XCTAssertEqual(employer!.stuff!.count, 1, "Data was not deserialized successfully")
        XCTAssertTrue(employer!.info == nil, "Employer info is wrong")

        let wrongMessage = "{\"stuff\":[{\"wrong_value\":13}"
        let wrongMessageData = wrongMessage.dataUsingEncoding(NSUTF8StringEncoding, allowLossyConversion: true)

        let wrongEmployer = Employer(jsonData: wrongMessageData, error: &error)

        XCTAssertNil(wrongEmployer, "Struct was initialized with wrong data")
    }
}
