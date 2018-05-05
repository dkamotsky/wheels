from conctx import *
import unittest
import json
import codecs
import pickle

SAMPLE_JSON1="""
{                                                                     
    "ConversationContext": {                                          
        "_type_": "cc",                                                
        "answer": "I prefer calvin klein",                            
        "apiContext": {                                               
            "APPLICATION": "MOBILE",                                  
            "DEVICE_TYPE": "PHONE",                                   
            "REGION_CODE": "US"                                       
        }
    },                                                            
    "newInput": true                                                 
}
"""

SAMPLE_JSON2="""
{                                                                     
    "l": [
        {                                          
            "_type_": "cc",                                                
            "extractedFilters": [
                {                                                         
                    "_type_": "rf",                                       
                    "name": "BELT_STYLE",                                 
                    "values": [                                           
                        "wide",                                           
                        "medium"                                          
                    ]                                                     
                }                                                         
            ]
        },
        {                                          
            "_type_": "cc",                                                
            "userId": 12345                                               
        }        
    ]                                                 
}
"""

SAMPLE_JSON3="""
{                                                                     
    "ConversationContext": {                                          
        "_type_": "cc",
        "state": {   
            "_type_": "st",
            "val": "PDP"
        }                           
    },                                                            
    "abcd": "efgh"                                                 
}
"""


class ConversationContextTest(unittest.TestCase):

    def setUp(self):
         self.cc=ConversationContext()
         self.cc.conversationId = "guid-12345"
         self.cc.userId = 12345
         self.cc.apiContext = {"DEVICE_TYPE": "PHONE", "APPLICATION": "MOBILE", "REGION_CODE": "US"}
         self.cc.preview = True
         self.cc.numQuestionsAsked = 1
         self.cc.state = State.INIT
         self.cc.conversationalResponse = "Hello, my name is Leslie :)"
         self.cc.textInput = "I am looking for jeans"
         self.cc.searchPhrase = "jeans"
         self.cc.answer = "I prefer calvin klein"
         self.cc.question = "Do you prefer Calvin Klein or Michael Kors?"
         self.cc.questionFilter = Refinement("BRAND", "Calvin Klein", "Michael Kors")
         self.cc.ignoredFilters = [Refinement("STYLE", "capri", "lowrise"), Refinement("MATERIAL", "acrylic")]
         self.cc.implicitFilters = [Refinement("GENDER_AGE", "Female"), Refinement("SEARCH_DIMENSION", "S", "34", "20x12")]
         self.cc.explicitFilters = [Refinement("COLOR_NORMAL", "Blue")]
         self.cc.answerFilters = [Refinement("BRAND", "Calvin Klein")]
         self.cc.extractedFilters = [Refinement("BELT_STYLE", "wide", "medium")]
         self.cc.bestProductId = 98765
         self.cc.numResults = 88
         self.cc.productSelection = [ProductSelection(12, "prod12"), ProductSelection(34, "prod34")]
         self.opaque = codecs.encode(pickle.dumps({"abc": "def"}), "base64").decode()
         self.ec=ConversationContext()
         self.ec.conversationId = "mostly empty"
         self.ec.productSelection = [ProductSelection(12, "prod12"), ProductSelection(34, "prod34")]         

    def test_frozen(self):
        try:
            self.cc.newAttr="blah"
        except Exception as e:
            assert type(e)==AttributeError
        else:
            assert False
        try:
            self.cc.state.newAttr="blah"
        except Exception as e:
            assert False
        try:
            self.cc.questionFilter.newAttr="blah"
        except Exception as e:
            assert type(e)==AttributeError
        else:
            assert False            
        try:
            iter(self.cc.productSelection).next().newAttr="blah"
        except Exception as e:
            assert type(e)==AttributeError
        else:
            assert False            
         
    def test_json_recode(self):
        ConversationContextTest.json_recode(self.cc)
        ConversationContextTest.json_recode(self.ec)
        
    @staticmethod
    def json_recode(obj):
        s=json.dumps(obj, cls=JsonWithContextEncoder, sort_keys=True, indent=4)
        j=json.loads(s, cls=JsonWithContextDecoder)        
        assert obj==j
        s=json.dumps({"newInput": False, "ConversationContext": obj}, cls=JsonWithContextEncoder, sort_keys=True, indent=4)
        j=json.loads(s, cls=JsonWithContextDecoder)
        assert obj==j["ConversationContext"]
        assert j["newInput"]==False
        if obj.opaque:
            d=pickle.loads(codecs.decode(j["ConversationContext"]["opaque"].encode(), "base64"))
            assert d["abc"]=="def"

    def test_sample_json(self):
        j=json.loads(SAMPLE_JSON1, cls=JsonWithContextDecoder)
        assert j["ConversationContext"]["answer"]=="I prefer calvin klein"
        assert j["ConversationContext"]["apiContext"]["DEVICE_TYPE"]=="PHONE"
        assert j["newInput"]==True
        j=json.loads(SAMPLE_JSON2, cls=JsonWithContextDecoder)
        ef,=j["l"][0]["extractedFilters"]
        assert ef.values==frozenset(["wide", "medium"])
        assert j["l"][1]["userId"]==12345                
        j=json.loads(SAMPLE_JSON3, cls=JsonWithContextDecoder)
        assert j["ConversationContext"]["state"]==State.PDP

    def test_plain_json(self):
        s=json.dumps(self.cc, cls=PlainJsonWithContextEncoder, sort_keys=True, indent=4)
        j=json.loads(s)
        assert j["state"]=="INIT"
        assert j["questionFilter"]["name"]=="BRAND"
        class RenamingEncoder(PlainJsonWithContextEncoder):
            @property
            def rename(self):
                return {"questionFilter": "questionRefinement"}
        s=json.dumps(self.cc, cls=RenamingEncoder, sort_keys=True, indent=4)
        j=json.loads(s)
        assert j["state"]=="INIT"
        assert j["questionRefinement"]["name"]=="BRAND"
            


if __name__ == '__main__':
    unittest.main()
