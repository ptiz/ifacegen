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

class ifacegen_swift_category_test: XCTestCase {

    func testCategoryDump() {
        let prevModel = BusinessModel( name: "BMod-old", revisions: nil, theDescription: "Old Business Model" )
        let model = BusinessModel( name: "BMod", revisions: [ BusinessModelRevisionsItem(version: 1, model: prevModel) ], theDescription: "Business model #1" )

        var error: NSError?

        let dict = model.dictionary(&error)
        XCTAssertNotNil(dict, "Serialization was unsuccessful")

        let revisions = dict["revisions"] as! [AnyObject]
        let revision = revisions[0] as! [String : AnyObject]
        let modelDict = revision["model"] as! [String : AnyObject]
        let modelName = modelDict["name"] as! String!
        XCTAssertTrue(modelName == "BMod-old", "Serialization was not successful")
    }

    func testCategoryReading() {
        var error: NSError?
        let data = NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource("test_category_data", ofType: "json")!)
        let model = BusinessModel(jsonData: data, error: &error)
        let revisions = model!.revisions
        let nestedModel = revisions![0].model

        XCTAssertTrue(nestedModel!.name == "Nested BusMod", "Deserialization was not sucessful")
    }
}