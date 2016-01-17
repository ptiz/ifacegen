/**
*	Created by Evgeny Kamyshanov on Mar, 2015
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

class ifacegen_category_test: XCTestCase {
    
    func testCategoryDump() {
        
        let prevModel = OBCBusinessModel( name: "BMod-old", andRevisions: [], andTheDescription: "Old Business Model" )
        let model = OBCBusinessModel( name: "BMod", andRevisions: [ OBCBusinessModelRevisionsItem(version: 1, andModel: prevModel) ], andTheDescription: "Business model #1" )
        
        let dict = try! model.dictionary()
        
        let revisions = dict["revisions"] as! NSArray
        let revision = revisions.objectAtIndex(0) as! NSDictionary
        let modelDict = revision.objectForKey("model") as! NSDictionary
        let modelName = modelDict.objectForKey("name") as! String!
        
        XCTAssertTrue(modelName == "BMod-old", "Serialization was not successful")
    }
    
    func testCategoryReading() {
        let data = NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource("test_category_data", ofType: "json")!)
        let model = try! OBCBusinessModel(JSONData: data!)
        let revisions = model.revisions
        let nestedModel = revisions[0].model
        
        XCTAssertTrue(nestedModel.name == "Nested BusMod", "Deserialization was not sucessful")
    }
}