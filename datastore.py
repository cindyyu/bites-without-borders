from google.appengine.ext import ndb 

class User(ndb.Model) : 
  user_id = ndb.StringProperty(required=True)
  name = ndb.StringProperty(required=True)
  location = ndb.StringProperty()

class Recipe(ndb.Model) : 
  name = ndb.StringProperty(required=True)
  cooktime = ndb.StringProperty()
  instructions = ndb.TextProperty()
  servings = ndb.IntegerProperty()
  author = ndb.StringProperty()
  location = ndb.GeoPtProperty()
  ingredients = ndb.StringProperty(repeated=True) 