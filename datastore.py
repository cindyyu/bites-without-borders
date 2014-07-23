from google.appengine.ext import ndb 

class User(ndb.Model) : 
  user_id = ndb.StringProperty(required=True)
  name = ndb.StringProperty(required=True)
  bio = ndb.TextProperty()
  location = ndb.StringProperty()
  pic = ndb.BlobProperty(indexed=False)
  savedRecipes = ndb.StringProperty(repeated=True)
  def recipesUrl(self):
    return '/recipes/by/%s' % self.key.id()
  def picUrl(self):
    return '/userpic?id=%s' % self.key.id()

class Recipe(ndb.Model) : 
  name = ndb.StringProperty(required=True)
  cooktime = ndb.StringProperty()
  instructions = ndb.TextProperty(repeated=True)
  servings = ndb.IntegerProperty()
  author = ndb.StringProperty()
  image = ndb.BlobProperty()
  location = ndb.GeoPtProperty()
  location_name = ndb.StringProperty()
  ingredients = ndb.StringProperty(repeated=True) 
  thumbsUp = ndb.IntegerProperty(default=0)
  thumbsDown = ndb.IntegerProperty(default=0)
  def imageUrl(self):
    return '/images?id=%s' % self.key.id()
  def deleteUrl(self):
    return '/recipes/delete/%s' % self.key.id()
  def viewUrl(self):
    return '/recipes/view/%s' % self.key.id()
  def editUrl(self): 
    return '/recipes/edit/%s' % self.key.id()
  def editUrlSuccess(self):
    return '/recipes/edit/%s?success=True' %self.key.id()