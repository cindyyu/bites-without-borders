from google.appengine.ext import ndb 

class User(ndb.Model) : 
  user_id = ndb.StringProperty(required=True)
  name = ndb.StringProperty(required=True)
  location = ndb.StringProperty()
  def recipesUrl(self):
    return '/recipes/by/%s' % self.key.id()

class Recipe(ndb.Model) : 
  name = ndb.StringProperty(required=True)
  cooktime = ndb.StringProperty()
  instructions = ndb.TextProperty()
  servings = ndb.IntegerProperty()
  author = ndb.StringProperty()
  location = ndb.GeoPtProperty()
  ingredients = ndb.StringProperty(repeated=True) 
  thumbsUp = ndb.IntegerProperty()
  thumbsDown = ndb.IntegerProperty()
  def deleteUrl(self):
    return '/recipes/delete/%s' % self.key.id()
  def viewUrl(self):
    return '/recipes/view/%s' % self.key.id()
  def editUrl(self): 
    return '/recipes/edit/%s' % self.key.id()
  def editUrlSuccess(self):
    return '/recipes/edit/%s?success=True' %self.key.id()