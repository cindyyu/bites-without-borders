#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import users
from google.appengine.ext import ndb 
from google.appengine.api.datastore_types import GeoPt
from datastore import User
from datastore import Recipe


import webapp2
import os 
import json
import jinja2
#import webapp2_extras.appengine.auth.models

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def UserId() :
  return users.get_current_user().user_id()

def UserInfo() :
  user = users.get_current_user()
  name = user.nickname()
  userID = UserId()
  dbUser = User.query().filter(User.user_id == userID).fetch(1)
  return dbUser

def GetHeader(type) :

  dbUser = UserInfo()
  name = users.get_current_user().nickname()

  header_values = {
    'logout_url' : users.create_logout_url('/'),
    'name' : users.get_current_user().nickname()
  }

  if dbUser :
    header_values['user_recipes_url'] = '/recipes/by/' + str(dbUser[0].user_id)

  homepage_header = jinja_environment.get_template('templates/homepage_header.html').render(header_values)
  recipe_header = jinja_environment.get_template('templates/recipes_header.html').render({'name' : name, 'user_recipes_url': '/recipes/by/' + str(dbUser[0].user_id)})

  if type == 'homepage' : 
    return homepage_header
  if type == 'recipe' : 
    return recipe_header

class HomeHandler(webapp2.RequestHandler):
  def get(self):
    # check if user is already in database
    rawRecipes = Recipe.query().fetch()
    recipes = []
    for rawRecipe in rawRecipes : 
      if rawRecipe.image :
        recipes.append({
          'name': rawRecipe.name, 
          'latlng': str(rawRecipe.location), 
          'location': rawRecipe.location_name, 
          'cooktime': rawRecipe.cooktime, 
          'image': '<div style="background-image: url(' + rawRecipe.imageUrl() + ')"></div>',
          'servings': rawRecipe.servings, 
          'ingredients': json.dumps(rawRecipe.ingredients),
          'recipeUrl' : rawRecipe.viewUrl()
        })
      else :
        recipes.append({
          'name': rawRecipe.name, 
          'latlng': str(rawRecipe.location), 
          'location': rawRecipe.location_name, 
          'cooktime': rawRecipe.cooktime, 
          'servings': rawRecipe.servings, 
          'ingredients': json.dumps(rawRecipe.ingredients),
          'recipeUrl' : rawRecipe.viewUrl()
        })    
    user = users.get_current_user()
    name = user.nickname()
    userID = user.user_id()
    dbUser = User.query().filter(User.user_id == userID).fetch(1)

    if UserInfo() : 
      name = dbUser[0].name
      template_values = { 'name': name }
      firstTime = False
    else :
      newUser = User(user_id=userID, name=name, savedRecipes=[''])
      newUser.put()
      name = user.nickname()
      firstTime = True

    template_values = { 'title': 'Homepage', 'recipes': json.dumps(recipes), 'header': GetHeader('homepage'), 'logout_url': users.create_logout_url('/'), 'first_time': firstTime }
    Homepage = jinja_environment.get_template('templates/homepage.html').render(template_values)
    self.response.write(Homepage)

class NewRecipe(webapp2.RequestHandler): 
  def get(self): 
    # show new recipe form
    template_values = { 'title': 'Add New Recipe', 'header': GetHeader('recipe'), 'userID' : UserId() }
    NewRecipePage = jinja_environment.get_template('templates/recipes_add.html').render(template_values)
    self.response.write(NewRecipePage)
  def post(self):
    # handles recipe submissions
    import re
    recipe_added = {
      'name' : self.request.get('name'),
      'image' : self.request.get('img'),
      'cook_time' : self.request.get('cooktime'),
      'instructions' : json.loads(str(self.request.get('instructions'))),
      'servings' : int(self.request.get('servings')), 
      'author' : self.request.get('author'), 
      'location_name' : self.request.get('location_name'),
      'location' : GeoPt(re.sub("[()]", "", self.request.get('location'))),
      'ingredients' : json.loads(str(self.request.get('ingredients')))
    }
    newRecipe = Recipe(
      name=recipe_added['name'],
      cooktime=recipe_added['cook_time'],
      instructions=recipe_added['instructions'],
      servings=recipe_added['servings'],
      author=recipe_added['author'],
      location=recipe_added['location'],
      location_name=recipe_added['location_name'],
      ingredients=recipe_added['ingredients']
    )
    if recipe_added['image'] :
      newRecipe.image = recipe_added['image']
    newRecipe.put()
    recipe_added['id'] = newRecipe.key.id()
    template_values = { 'title': 'New Recipe Added', 'success': True, 'recipe_added': recipe_added, 'header': GetHeader('recipe'), 'userID' : UserId() }
    RecipeAddedPage = jinja_environment.get_template('templates/recipes_added.html').render(template_values)
    self.response.write(RecipeAddedPage)

class ViewIndividualRecipe(webapp2.RequestHandler):
  def get(self, recipe_id):
    # check if ID is found in recipe database
    recipe = Recipe.get_by_id(int(recipe_id))
    if not recipe : 
      error = "That recipe was not found."
      template_values = { 'error' : error }
    else : 
      # check if this recipe belongs to user
      if recipe.author == UserId() :
        isOwner = True
      else :
        isOwner = False
      recipe_author_name = User.query().filter(User.user_id == recipe.author).fetch(1)[0].name
      template_values = { 'title': recipe.name, 'recipe' : recipe, 'isOwner' : isOwner, 'header': GetHeader('recipe'), 'recipe_author_name': recipe_author_name } 
    IndividualRecipe = jinja_environment.get_template('templates/recipes_individual.html').render(template_values)
    self.response.write(IndividualRecipe)

class ViewRecipesBy(webapp2.RequestHandler): 
  def get(self, author_id):
    # check if there is user that corresponds with the ID
    author = User.query().filter(User.user_id == author_id).fetch()
    if author : 
      # check if the user has any recipes
      recipes = Recipe.query().filter(Recipe.author == author_id).fetch()
      if recipes : 
        template_values = { 'header': GetHeader('recipe'), 'recipes' : recipes, 'author' : author[0].name ,'author_bio' : author[0].bio , 'title' : 'Recipes by ' + author[0].name}
        if author[0].pic :
          template_values['author_pic'] = author[0].picUrl()
        if author[0].location :
          template_values['author_location'] = author[0].location
      else : 
        error = "This user has not uploaded any recipes."
        template_values = { 'header': GetHeader('recipe'), 'title': 'Error', 'error' : error }
    else : 
      error = "This user doesn't not exist."
      template_values = { 'header': GetHeader('recipe'), 'title': 'Error', 'error' : error }
    RecipesBy = jinja_environment.get_template('templates/recipes_by.html').render(template_values)
    self.response.write(RecipesBy)

class EditRecipePage(webapp2.RequestHandler):
  def get(self, recipe_id):
    recipe = Recipe.get_by_id(int(recipe_id))
    success = self.request.get('success')
    # check if the recipe ID exists
    if recipe :
      # check if user has permission to edit the recipe
      if recipe.author == UserId() : 
        template_values = { 'title': 'Edit Recipe', 'recipe' : recipe, 'recipe_id' : recipe_id, 'success' : success }
      else :
        error = "that's not your recipe yo"
        template_values = { 'title': 'Error', 'error' : error } 
    else : 
      error = "that doesn't exist, yo"
      template_values = { 'title': 'Error', 'error' : error } 
    template_values['header'] = GetHeader('recipe')
    EditRecipePage = jinja_environment.get_template('templates/recipes_edit.html').render(template_values)
    self.response.write(EditRecipePage)

class EdittedRecipe(webapp2.RequestHandler):
  def post(self): 
    import re
    # fetch new values
    recipe_editted = {
      'id' : self.request.get('recipe_id'),
      'name' : self.request.get('name'),
      'cook_time' : self.request.get('cooktime'),
      'instructions' : self.request.get('instructions'),
      'image' : self.request.get('img'),
      'servings' : int(self.request.get('servings')), 
      'author' : self.request.get('author'), 
      'location' : GeoPt(re.sub("[()]", "", self.request.get('location'))),
      'location_name' : self.request.get('location_name'),
      'ingredients' : json.loads(str(self.request.get('ingredients'))),
      'instructions' : json.loads(str(self.request.get('instructions')))
    }
    # fetch recipe model corresponding to the recipe we wanna edit
    recipe_to_edit = Recipe.get_by_id(int(recipe_editted['id']))
    recipe_to_edit.name = recipe_editted['name']
    recipe_to_edit.cooktime = recipe_editted['cook_time']
    if recipe_editted['image'] != '' :
      recipe_to_edit.image = recipe_editted['image']
    recipe_to_edit.instructions = recipe_editted['instructions']
    recipe_to_edit.servings = recipe_editted['servings']
    recipe_to_edit.location = recipe_editted['location']
    recipe_to_edit.location_name = recipe_editted['location_name']
    if recipe_editted['ingredients'] :
      recipe_to_edit.ingredients = recipe_editted['ingredients']
    recipe_to_edit.put()
    self.redirect(recipe_to_edit.editUrlSuccess())

class ViewAllRecipes(webapp2.RequestHandler):
  def get(self): 
    # fetch all recipes
    recipes = Recipe.query().fetch()
    template_values = {'title': 'All Recipes', 'header': GetHeader('recipe'), 'recipes' : recipes, 'title': 'All Recipes'}
    ViewAllRecipes = jinja_environment.get_template('templates/recipes_all.html').render(template_values)
    self.response.write(ViewAllRecipes)

class DeleteRecipe(webapp2.RequestHandler):
  def get(self, recipe_id):
    recipe = Recipe.get_by_id(int(recipe_id))
    # check if the recipe ID exists
    if recipe :
      # check if user has permission to edit the recipe
      if recipe.author == UserId() : 
        recipe.key.delete()
        template_values = {}
      else :
        error = "You do not have permission to do this."
        template_values = {'title': 'Error', 'error' : error } 
    else : 
      error = "The recipe you are trying to delete does not exist."
      template_values = {'header': GetHeader('recipe'), 'title': 'Error', 'error' : error } 
    DeleteRecipePage = jinja_environment.get_template('templates/recipes_delete.html').render(template_values)
    self.response.write(DeleteRecipePage)

class ThumbUpRecipe(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    recipe = Recipe.get_by_id(int( data['recipeID'] ))
    # check if user has already saved this recipe
    dbUser = User.query().filter(User.user_id == UserId()).fetch(1)
    user = dbUser[0]
    matches = 0
    for savedRecipe in user.savedRecipes :
      if savedRecipe == data['recipeID'] :
        matches += 1
        break;
    if matches == 0 :
      if recipe.thumbsUp == None :
        recipe.thumbsUp = 1
      else :
        recipe.thumbsUp += 1
      recipe.put()
      user.savedRecipes.append( data['recipeID'] );
      user.put()
    self.response.write(json.dumps(({'recipe_thumbsUp': recipe.thumbsUp, 'net_thumbs': recipe.thumbsUp - recipe.thumbsDown})))

class ThumbDownRecipe(webapp2.RequestHandler):
  def post(self):
    data = json.loads(self.request.body)
    recipe = Recipe.get_by_id(int(data['recipeID']))
    if recipe.thumbsDown == None :
      recipe.thumbsDown = 1
    else :
      recipe.thumbsDown += 1
    recipe.put()
    self.response.write(json.dumps(({'recipe_thumbsDown': recipe.thumbsDown, 'net_thumbs': recipe.thumbsUp - recipe.thumbsDown})))

class SavedRecipes(webapp2.RequestHandler):
  def get(self) : 
    dbUser = UserInfo()
    if dbUser :
      user = dbUser[0]
      recipes = []
      for recipe in user.savedRecipes :
        if recipe != '' :
          savedRecipe = Recipe.get_by_id(int(recipe))
          if savedRecipe :
            recipes.append(savedRecipe)
      template_values = { 'title': 'Your Saved Recipes', 'header': GetHeader('recipe'), 'recipes' : recipes, 'title': 'Your Saved Recipes' } 
      SavedRecipes = jinja_environment.get_template('templates/recipes_all.html').render(template_values)
      self.response.write(SavedRecipes)
    else :
      self.response.write("EH")

class UserSettings(webapp2.RequestHandler) :
  def get(self) : 
    dbUser = UserInfo()
    if dbUser : 
      user = dbUser[0]
      template_values = { 'title': 'Edit User Settings', 'user': user }
    else :
      error = "an error occurred"
      template_values = { 'title': 'Error', 'error': error }
    template_values['header'] = GetHeader('recipe')
    SettingsPage = jinja_environment.get_template('templates/user_settings.html').render(template_values)
    self.response.write(SettingsPage)
  def post(self) : 
    dbUser = UserInfo() 
    if dbUser : 
      user = dbUser[0]
      updated_location = self.request.get("location")
      updated_image = self.request.get("image")
      updated_bio = self.request.get("bio")
      user.bio = updated_bio
      user.location = updated_location
      if updated_image != '' : 
        user.pic = updated_image
      user.put()
      template_values = { 'title': 'Settings Saved', 'success': True, 'user': user, 'header': GetHeader('recipe') }
    SettingsPage = jinja_environment.get_template('templates/user_settings.html').render(template_values)
    self.response.write(SettingsPage)

class Image(webapp2.RequestHandler):
  def get(self) : 
    image_id = self.request.get('id')
    image = Recipe.get_by_id(int(image_id)).image
    self.response.headers['Content-Type'] = 'image/png'
    self.response.write(image)

class UserPic(webapp2.RequestHandler):
  def get(self) : 
    image_id = self.request.get('id')
    image = User.get_by_id(int(image_id)).pic
    self.response.headers['Content-Type'] = 'image/png'
    self.response.write(image)

class RemoveSavedRecipe(webapp2.RequestHandler):
  def post(self): 
    recipe_id = self.request.get("recipe_id")
    user = UserInfo()
    savedRecipes = user[0].savedRecipes
    # find index of recipe within savedRecipes property
    index = -1
    for recipe in savedRecipes :
      index += 1
      if recipe != '' and int(recipe) == int(recipe_id) :
        break;
    if index > -1 :
      del savedRecipes[index]
    user[0].savedRecipes = savedRecipes
    user[0].put()
    RemoveSavedPage = jinja_environment.get_template('templates/recipes_remove_saved.html').render({'header' : GetHeader('recipe')})
    self.response.write(RemoveSavedPage)


app = webapp2.WSGIApplication([
  ('/', HomeHandler),
  ('/recipes/new', NewRecipe),
  ('/recipes/view/(\d+)', ViewIndividualRecipe), 
  ('/recipes/by/(\d+)', ViewRecipesBy),
  ('/recipes/edit/(\d+)', EditRecipePage), 
  ('/recipes/editted', EdittedRecipe),
  ('/recipes/all', ViewAllRecipes),
  ('/recipes/delete/(\d+)', DeleteRecipe),
  ('/recipes/thumbsUp', ThumbUpRecipe),
  ('/recipes/thumbsDown', ThumbDownRecipe),
  ('/recipes/saved', SavedRecipes),
  ('/images', Image),
  ('/settings', UserSettings),
  ('/userpic', UserPic),
  ('/recipes/saved/remove', RemoveSavedRecipe)
], debug=True)
