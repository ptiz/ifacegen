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
    
    func testCall() {
        
        var prevModel = OBCBusinessModel( name: "BMod-old", andRevisions: nil, andTheDescription: "Old Business Model" )
        var model = OBCBusinessModel( name: "BMod", andRevisions: [ OBCBusinessModelRevisionsItem(version: 1, andModel: prevModel) ], andTheDescription: "Business model #1" )
        
        var error:NSError?
//TODO: uncomment when ready
//        let dict = model.dictionaryWithError(&error)
//        XCTAssertNil(error, "Serialization was unsuccessful")
        
    }
}