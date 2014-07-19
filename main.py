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
from google.appengine.api.datastore_types import GeoPt
from datastore import User
from datastore import Recipe

import webapp2
import os 
import json
import jinja2
import webapp2_extras.appengine.auth.models

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

user = users.get_current_user()
name = user.nickname()
userID = user.user_id()
dbUser = User.query().filter(User.user_id == userID).fetch(1)

header_values = {
  'logout_url' : users.create_logout_url('/'),
  'name' : name, 
  #'user_recipes_url' : '/recipes/by/' + str(dbUser[0].user_id)
}
homepage_header = jinja_environment.get_template('templates/homepage_header.html').render(header_values)
recipe_header = jinja_environment.get_template('templates/recipes_header.html').render({'name' : name})

class HomeHandler(webapp2.RequestHandler):
  def get(self):
    # check if user is already in database
    if dbUser : 
      name = dbUser[0].name
      template_values = { 'name': name }
      firstTime = False
    else :
      newUser = User(user_id=userID, name=user.nickname())
      newUser.put()
      name = user.nickname()
      firstTime = True
    template_values = { 'header': homepage_header, 'logout_url': users.create_logout_url('/'), 'first_time': firstTime }
    Homepage = jinja_environment.get_template('templates/homepage.html').render(template_values)
    self.response.write(Homepage)

class NewRecipe(webapp2.RequestHandler): 
  def get(self): 
    # show new recipe form
    template_values = { 'header': recipe_header, 'userID' : userID }
    NewRecipePage = jinja_environment.get_template('templates/recipes_add.html').render(template_values)
    self.response.write(NewRecipePage)
  def post(self):
    # handles recipe submissions
    from StringIO import StringIO
    recipe_added = {
      'name' : self.request.get('name'),
      'cook_time' : self.request.get('cooktime'),
      'instructions' : self.request.get('instructions'),
      'servings' : int(self.request.get('servings')), 
      'author' : self.request.get('author'), 
      'location' : GeoPt(self.request.get('location')),
      'ingredients' : json.loads(str(self.request.get('ingredients')))
    }
    newRecipe = Recipe(
      name=recipe_added['name'],
      cooktime=recipe_added['cook_time'],
      instructions=recipe_added['instructions'],
      servings=recipe_added['servings'],
      author=recipe_added['author'],
      location=recipe_added['location'],
      ingredients=recipe_added['ingredients']
    )
    newRecipe.put()
    template_values = { 'recipe_added': recipe_added, 'header': recipe_header, 'userID' : userID }
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
      template_values = { 'recipe' : recipe } 
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
        template_values = { 'recipes' : recipes }
      else : 
        error = "This user has not uploaded any recipes."
        template_values = { 'error' : error }
    else : 
      error = "This user doesn't not exist."
      template_values = { 'error' : error }
    RecipesBy = jinja_environment.get_template('templates/recipes_by.html').render(template_values)
    self.response.write(RecipesBy)

class EditRecipePage(webapp2.RequestHandler):
  def get(self, recipe_id):
    recipe = Recipe.get_by_id(int(recipe_id))
    success = self.request.get('success')
    # check if the recipe ID exists
    if recipe :
      # check if user has permission to edit the recipe
      if recipe.author == userID : 
        template_values = { 'recipe' : recipe, 'recipe_id' : recipe_id, 'success' : success }
      else :
        error = "that's not your recipe yo"
        template_values = { 'error' : error } 
    else : 
      error = "that doesn't exist, yo"
      template_values = { 'error' : error } 
    EditRecipePage = jinja_environment.get_template('templates/recipes_edit.html').render(template_values)
    self.response.write(EditRecipePage)

class EdittedRecipe(webapp2.RequestHandler):
  def post(self): 
    # fetch new values
    recipe_editted = {
      'id' : self.request.get('recipe_id'),
      'name' : self.request.get('name'),
      'cook_time' : self.request.get('cooktime'),
      'instructions' : self.request.get('instructions'),
      'servings' : int(self.request.get('servings')), 
      'author' : self.request.get('author'), 
      'location' : GeoPt(self.request.get('location')),
      'ingredients' : json.loads(str(self.request.get('ingredients')))
    }
    # fetch recipe model corresponding to the recipe we wanna edit
    recipe_to_edit = Recipe.get_by_id(int(recipe_editted['id']))
    recipe_to_edit.name = recipe_editted['name']
    recipe_to_edit.cooktime = recipe_editted['cook_time']
    recipe_to_edit.instructions = recipe_editted['instructions']
    recipe_to_edit.servings = recipe_editted['servings']
    recipe_to_edit.location = recipe_editted['location']
    recipe_to_edit.ingredients = recipe_editted['ingredients']
    recipe_to_edit.put()
    self.redirect(recipe_to_edit.editUrlSuccess())

class ViewAllRecipes(webapp2.RequestHandler):
  def get(self): 
    # fetch all recipes
    recipes = Recipe.query().fetch()
    template_values = {'recipes' : recipes}
    ViewAllRecipes = jinja_environment.get_template('templates/recipes_all.html').render(template_values)
    self.response.write(ViewAllRecipes)

class DeleteRecipe(webapp2.RequestHandler):
  def get(self, recipe_id):
    recipe = Recipe.get_by_id(int(recipe_id))
    # check if the recipe ID exists
    if recipe :
      # check if user has permission to edit the recipe
      if recipe.author == userID : 
        recipe.key.delete()
        template_values = {}
      else :
        error = "that's not your recipe yo"
        template_values = { 'error' : error } 
    else : 
      error = "that doesn't exist, yo"
      template_values = { 'error' : error } 
    DeleteRecipePage = jinja_environment.get_template('templates/recipes_delete.html').render(template_values)
    self.response.write(DeleteRecipePage)

app = webapp2.WSGIApplication([
  ('/', HomeHandler),
  ('/recipes/new', NewRecipe),
  ('/recipes/view/(\d+)', ViewIndividualRecipe), 
  ('/recipes/by/(\d+)', ViewRecipesBy),
  ('/recipes/edit/(\d+)', EditRecipePage), 
  ('/recipes/editted', EdittedRecipe),
  ('/recipes/all', ViewAllRecipes),
  ('/recipes/delete/(\d+)', DeleteRecipe)
], debug=True)
