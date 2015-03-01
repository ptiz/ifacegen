//
//  ifacegen_category_test.swift
//  ifacegen.test
//
//  Created by Evgenii Kamyshanov on 20.02.15.
//
//

import Foundation
import XCTest

class ifacegen_category_test: XCTestCase {
    
    func testCategoryDump() {
        
        var prevModel = OBCBusinessModel( name: "BMod-old", andRevisions: nil, andTheDescription: "Old Business Model" )
        var model = OBCBusinessModel( name: "BMod", andRevisions: [ OBCBusinessModelRevisionsItem(version: 1, andModel: prevModel) ], andTheDescription: "Business model #1" )
        
        var error:NSError?

        let dict = model.dictionaryWithError(&error)
        XCTAssertNotNil(dict, "Serialization was unsuccessful")
        
        let revisions = dict["revisions"] as NSArray
        let revision = revisions.objectAtIndex(0) as NSDictionary
        let modelDict = revision.objectForKey("model") as NSDictionary
        let modelName = modelDict.objectForKey("name") as String!
        XCTAssertTrue(modelName == "BMod-old", "Serialization was not successful")
    }
    
    func testCategoryReading() {
        let data = NSData(contentsOfFile: NSBundle(forClass:self.classForCoder).pathForResource("test_category_data", ofType: "json")!)
        let model = OBCBusinessModel(JSONData: data, error: nil)
        let revisions = model.revisions as NSArray
        let nestedModel = revisions.objectAtIndex(0).model as OBCBusinessModel
        
        XCTAssertTrue(nestedModel.name == "Nested BusMod", "Deserialization was not sucessful")
    }
}