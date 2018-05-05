import sys
import re
import flask.json
import enum
import logging

from frozendict import frozendict

logger=logging.getLogger("conctx")


def frozen(setfun):
    """Raise an error when trying to set an undeclared name, or when calling
       from a method other than Frozen.__init__ or the __init__ method of
       a class derived from Frozen"""
    def set_attr(self,name,value):
        if hasattr(self,name):                                  #If attribute already exists, simply set it
            setfun(self,name,value)
            return
        elif sys._getframe(1).f_code.co_name == '__init__':     #Allow __setattr__ calls in __init__ calls of proper object types
            for k,v in sys._getframe(1).f_locals.items():
                if k=="self" and isinstance(v, self.__class__):
                    setfun(self,name,value)
                    return
        raise AttributeError("You cannot add attributes to %s" % self)
    return set_attr


class Frozen(object):
    """Subclasses of Frozen are frozen, i.e. it is impossibile to add
     new attributes to them and their instances."""
    __setattr__=frozen(object.__setattr__)
    class __metaclass__(type):
        __setattr__=frozen(type.__setattr__)

        
"""
    Uses enum34 package which is fully compatible
    between Python2 and Python3
    Example JSON representation is:
    {
        "_type_": "st",
        "val": "INIT"
    }
"""
class State(enum.Enum):
    INIT = 0
    START = 1
    CLARIFICATION = 2
    ANSWER = 3
    SELECTION = 4
    END = 5
    PDP = 6
    RESULTS = 7
    SKIP_QUESTION = 8    
    BAD_INPUT = 9
       
    @classmethod        
    def from_dict(clazz, dct):
        return State[dct['val']]
    
"""
    Helper base class for objects which can be
    custom-encoded into JSON, and support
    full equals/hashcode overrides in order to
    make them usable in Sets.
    Also supports graceful to string and member
    access by ['name'].
"""
class BaseHelper(Frozen):

    def __getitem__(self, key):
        return getattr(self, key, None)

    def get(self, key, default):
        return getattr(self, key, default)

    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return NotImplemented

    def __ne__(self, other):
        """Define a non-equality test"""
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        else:
            return NotImplemented

    def __hash__(self):
        """Override the default hash behavior (that returns the id or the object)"""
        return hash(tuple(sorted(self.__dict__.items())))
    
    def __str__(self):
        return "%s: %s" % (self.__class__.__name__, {k: "%s...%s" % (v[:5], v[-5:]) if k=="opaque" and v is not None and len(v)>10 else v for k, v in self.__dict__.items()})

    def __repr__(self):
        return self.__str__()
            
    @classmethod        
    def from_dict(clazz, dct):
        this=clazz()
        for key in dct.keys():
            try:
                setattr(this, key, dct[key])
            except Exception as exc:
                logger.error("from_dict: class %s does not have attribute %s. Unable to set value %s. Exception: %s", clazz, key, dct[key], exc) 
        return this


"""
    Filter. Name-values pair.
    Example JSON representation:
    {
        "_type_": "rf",
        "name": "BRAND",
        "values": [ "Adidas", "Nike" ]        
    }
"""    
class Refinement(BaseHelper):

    """
        Pass values as variable arguments list.
    """
    def __init__(self, name=None, *args):         
         self.name = name
         self._p_values = frozenset(args) if args else frozenset() 

    @property
    def values(self):
        return self._p_values

    @values.setter
    def values(self, l):
        self._p_values=frozenset(l)
        

"""
    Product.
    Example JSON representation:
    {
        "_type_": "ps",
        "productId": 12345,
        "productName": "Nike Shoes"        
    }
"""        
class ProductSelection(BaseHelper):
    
    def __init__(self, productId=None, productName=""):
         self.productId = productId
         self.productName = productName
    

"""
    ConversationContext.
    Example JSON representation:
    {
        "_type_": "cc",
        "userId": 12345,
        "state": {
            "_type_": "st",
            "val": "INIT"
        }
    }
"""    
class ConversationContext(BaseHelper):
    
     def __init__(self):        
         self.conversationId = None
         self.userId = None
         self._p_apiContext = frozendict({})
         self.preview = False
         self.numQuestionsAsked = 0
         self.state = None
         self.conversationalResponse = None
         self.textInput = None
         self.searchPhrase = None
         self.answer = None
         self.question = None
         self.questionFilter = None
         self._p_ignoredFilters = frozenset()
         self._p_implicitFilters = frozenset()
         self._p_explicitFilters = frozenset()
         self._p_answerFilters = ()
         self._p_extractedFilters = frozenset()
         self.bestProductId = None
         self.numResults = None
         self._p_productSelection = ()
         self.opaque = None

     def reset(self):        
         self.numQuestionsAsked = 0
         self.conversationalResponse = None
         self.searchPhrase = None
         self.answer = None
         self.question = None
         self.questionFilter = None
         self._p_ignoredFilters = frozenset()
         self._p_implicitFilters = frozenset()
         self._p_explicitFilters = frozenset()
         self._p_answerFilters = ()
         self._p_extractedFilters = frozenset()
         self.bestProductId = None
         self.numResults = None
         self._p_productSelection = ()
         self.opaque = None

     @property
     def apiContext(self):
         return self._p_apiContext

     @apiContext.setter
     def apiContext(self, d):
         self._p_apiContext = frozendict(d)

     @property
     def ignoredFilters(self):
         return self._p_ignoredFilters

     @ignoredFilters.setter
     def ignoredFilters(self, l):
         self._p_ignoredFilters = frozenset(l)

     @property
     def implicitFilters(self):
         return self._p_implicitFilters

     @implicitFilters.setter
     def implicitFilters(self, l):
         self._p_implicitFilters = frozenset(l)

     @property
     def explicitFilters(self):
         return self._p_explicitFilters

     @explicitFilters.setter
     def explicitFilters(self, l):
         self._p_explicitFilters = frozenset(l)

     @property
     def answerFilters(self):
         return self._p_answerFilters

     @answerFilters.setter
     def answerFilters(self, l):
         self._p_answerFilters = tuple(l)

     @property
     def extractedFilters(self):
         return self._p_extractedFilters

     @extractedFilters.setter
     def extractedFilters(self, l):
         self._p_extractedFilters = frozenset(l)

     @property
     def productSelection(self):
         return self._p_productSelection

     @productSelection.setter
     def productSelection(self, l):
         self._p_productSelection = tuple(l)


TYPE_SELECTOR="_type_"


TYPE_NAMES = { State: 'st',
               Refinement: 'rf',
               ProductSelection: 'ps',
               ConversationContext: 'cc'}


NAMED_TYPES = dict(zip(TYPE_NAMES.values(), TYPE_NAMES.keys()))


class JsonWithContextEncoder(flask.json.JSONEncoder):

    @property
    def plain(self):
        return False

    @property
    def rename(self):
        return {}

    def default(self, obj):
        if isinstance(obj, set) or isinstance(obj, frozenset) or isinstance(obj, tuple):
            return list(obj)
        if isinstance(obj, frozendict):
            return dict(obj)
        for type_class in TYPE_NAMES.keys():
            if isinstance(obj, type_class):
                if isinstance(obj, enum.Enum):
                    out_dict=obj.name if self.plain else {"val": obj.name}
                else:
                    out_dict={}
                    for k, v in obj.__dict__.items():
                        if v or v==0 or v==False:
                            k=re.sub('^_p_', '', k)                            
                            out_dict[self.rename.get(k, k)]=v
                if not self.plain:
                    out_dict[TYPE_SELECTOR]=TYPE_NAMES[type_class]
                return out_dict
        return super(JsonWithContextEncoder, self).default(obj)


class PlainJsonWithContextEncoder(JsonWithContextEncoder):

    @property
    def plain(self):
        return True


class JsonWithContextDecoder(flask.json.JSONDecoder):

    def __init__(self, *args, **kwargs):
        flask.json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if TYPE_SELECTOR in dct:            
            type_name=dct.pop(TYPE_SELECTOR)
            if type_name in NAMED_TYPES:                
                return NAMED_TYPES[type_name].from_dict(dct)
        return dct
