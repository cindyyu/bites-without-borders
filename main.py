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
from datastore import User

import webapp2
import os 
import jinja2
import webapp2_extras.appengine.auth.models

jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

user = users.get_current_user()
name = user.nickname()
userID = user.user_id()
dbUser = User.query().filter(User.user_id == userID).fetch(1)

header_values = {
  'logout_url' : users.create_logout_url('/'),
  'name' : name
}
homepage_header = jinja_environment.get_template('templates/homepage_header.html').render({'name' : name})
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

class NewRecipeHandler(webapp2.RequestHandler): 
  def get(self): 
    # show new recipe form
    template_values = { 'header': recipe_header, 'userID' : userID }
    NewRecipePage = jinja_environment.get_template('templates/recipes_new.html').render(template_values)
    self.response.write(NewRecipePage)
  def post(self):
    # handles recipe submissions
    recipe_name = self.request.get('name')
    recipe_cook_time = self.request.get('cooktime')
    recipe_instructions = self.request.get('instructions')
    recipe_servings = self.request.get('servings')
    recipe_author = self.request.get('author')
    recipe_location = self.request.get('location')
    recipe_ingredients = self.request.get('ingredients')
    template_values = { 'header': recipe_header, 'userID' : userID }
    RecipeAddedPage = jinja_environment.get_template('templates/recipes_added.html').render(template_values)
    self.response.write(RecipeAddedPage)

app = webapp2.WSGIApplication([
  ('/', HomeHandler),
  ('/recipes/new', NewRecipeHandler)
], debug=True)
