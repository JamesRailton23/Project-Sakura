import os
import datetime
import pathlib
import openfoodfacts
import google.auth.transport.requests
import requests
from flask import Flask, render_template, request, redirect, flash, session, abort
from flask_pymongo import PyMongo
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
from google.oauth2 import id_token
from openai import OpenAI

# region Misc
app = Flask(__name__)
app.secret_key = # Removed due to security
app.config["MONGO_URI"] = # Removed due to security
mongo = PyMongo(app)
client = # Removed due to security

# endregion

# region Google sign in code
google_client_id = # Removed due to security
clients_secrets_file = # Removed due to security
flow = # Removed due to security


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)
        else:
            return function()

    wrapper.__name__ = function.__name__
    return wrapper


@app.route('/login', methods=['GET', 'POST'])
def login():
    authorisation_url, state = # Removed due to security
    session["state"] = state
    return redirect(authorisation_url)


@app.route('/callback')
def callback():
    # Removed due to security
    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = # Removed due to security
    request_session = # Removed due to security
    cached_session = # Removed due to security
    token_request = # Removed due to security

    id_info = # Removed due to security

    session["google_id"] = # Removed due to security
    session["name"] = # Removed due to security
    return redirect("/portal")


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')


# endregion

# region Item class
class Item:
    def __init__(self, barcode, storage_location, expiry_date=""):
        self.barcode = str(barcode)
        self.storage_location = str(storage_location)
        self.entry_date = str(datetime.date.today())
        self.expiry_date = str(expiry_date)
        self.image_url = None
        self.name = None
        self.item = None

        # clean up the incoming data
        self.barcode = self.barcode.strip()
        self.storage_location = self.storage_location.strip()
        self.entry_date = self.entry_date.strip()
        self.expiry_date = self.expiry_date.strip()
        self.barcode = self.barcode.removeprefix("@")
        self.barcode = self.barcode.removesuffix("@")
        self.barcode = self.barcode.strip()

    def add_item_to_database(self):
        api = openfoodfacts.API()
        try:
            self.item = api.product.get(code=self.barcode, fields=["product_name", "selected_images"])
            try:
                self.name = self.item["product"]["product_name"]
            except Exception:
                flash('Product name cannot be found for the given product, using default name instead', 'warning')
                self.name = "Unknown Item, please upload the item to openfoodfacts"
            try:
                self.image_url = self.item["product"]["selected_images"]["front"]["display"]["en"]
            except Exception:
                flash('Image URL cannot be found for the given product, using default image instead', 'warning')
                self.image_url = # Removed due to security
            mongo.db.items.insert_one(
                {'barcode': self.barcode, 'name': self.name, 'storage_location': self.storage_location,
                 'entry_date': self.entry_date, 'expiry_date': self.expiry_date,
                 'image_url': self.image_url})

        except Exception:
            flash("An error has occurred!!", 'danger')
        else:
            flash("Your item has been successfully added!!", 'success')


# endregion

# region Webpages
@app.route('/')
def index():
    return render_template("index.html")


@app.route("/portal")
@login_is_required
def portal():
    return render_template("portal.html", name=session["name"])


@app.route("/portal/add_item")
@login_is_required
def add_item():
    return render_template("add_item.html")


@app.route("/portal/view_all_locations/cupboard_left")
@login_is_required
def cupboard_left():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Left Cupboard'}))
    return render_template("cupboard_left.html", table_items=items_list)


@app.route("/portal/view_all_locations/cupboard_right")
@login_is_required
def cupboard_right():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Right Cupboard'}))
    return render_template("cupboard_right.html", table_items=items_list)


@app.route("/portal/view_all_locations/freezer_large")
@login_is_required
def freezer_large():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Large Freezer'}))
    return render_template("freezer_large.html", table_items=items_list)


@app.route("/portal/view_all_locations/freezer_small")
@login_is_required
def freezer_small():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Small Freezer'}))
    return render_template("freezer_small.html", table_items=items_list)


@app.route("/portal/view_all_locations/fridge")
@login_is_required
def fridge():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Fridge'}))
    return render_template("fridge.html", table_items=items_list)


@app.route("/portal/view_all_locations/pantry")
@login_is_required
def pantry():
    items = mongo.db.items
    items_list = list(items.find({'storage_location': 'Pantry'}))
    return render_template("pantry.html", table_items=items_list)


@app.route("/portal/view_all_locations")
@login_is_required
def view_all_item():
    return render_template("view_all_locations.html")


@app.route("/portal/view_item")
@login_is_required
def view_item():
    item = None
    return render_template("view_item.html", items=item)


# endregion

# region Portal buttons redirect
@app.route('/redirect_add_item', methods=['POST'])
def redirect_add_new_items():
    return redirect("/portal/add_item")


@app.route('/redirect_view_all_locations', methods=['POST'])
def redirect_view_all_locations():
    return redirect("/portal/view_all_locations")


@app.route('/redirect_view_item', methods=['POST'])
def redirect_view_an_item():
    return redirect("/portal/view_item")


# endregion

# region Back to portal buttons
@app.route('/add_item_to_portal', methods=['POST'])
def add_new_items_to_portal():
    return redirect("/portal")


@app.route('/view_item_to_portal', methods=['POST'])
def view_item_to_portal():
    return redirect("/portal")


@app.route('/view_all_locations_to_portal', methods=['POST'])
def view_all_item_to_portal():
    return redirect("/portal")


# endregion

# region View-all redirect to storage locations
@app.route('/view_cupboard_left', methods=['POST'])
def view_cupboard_left():
    return redirect("/portal/view_all_locations/cupboard_left")


@app.route('/view_cupboard_right', methods=['POST'])
def view_cupboard_right():
    return redirect("/portal/view_all_locations/cupboard_right")


@app.route('/view_fridge', methods=['POST'])
def view_fridge():
    return redirect("/portal/view_all_locations/fridge")


@app.route('/view_small_freezer', methods=['POST'])
def view_small_freezer():
    return redirect("/portal/view_all_locations/freezer_small")


@app.route('/view_large_freezer', methods=['POST'])
def view_large_freezer():
    return redirect("/portal/view_all_locations/freezer_large")


@app.route('/view_pantry', methods=['POST'])
def view_pantry():
    return redirect("/portal/view_all_locations/pantry")


# endregion

# region Storage locations redirect to view all
@app.route('/cupboard_left_to_view_all_locations', methods=['POST'])
def cupboard_left_to_view_all_locations():
    return redirect("/portal/view_all_locations")


@app.route('/cupboard_right_to_view_all_locations', methods=['POST'])
def cupboard_right_to_view_all():
    return redirect("/portal/view_all_locations")


@app.route('/freezer_large_to_view_all_locations', methods=['POST'])
def freezer_large_to_view_all_locations():
    return redirect("/portal/view_all_locations")


@app.route('/freezer_small_to_view_all_locations', methods=['POST'])
def freezer_small_to_view_all_locations():
    return redirect("/portal/view_all_locations")


@app.route('/fridge_to_view_all_locations', methods=['POST'])
def fridge_to_view_all_locations():
    return redirect("/portal/view_all_locations")


@app.route('/pantry_to_view_all_locations', methods=['POST'])
def pantry_to_view_all_locations():
    return redirect("/portal/view_all_locations")


# endregion

# region Code for uploading item to db
@app.route('/add_new_item', methods=['POST', 'GET'])
def add_new_item_form():
    barcode = request.form['tbx_barcode']
    storage_location = request.form['ddl_location']
    expiry_date = request.form['cal_expiry_date']

    if barcode.startswith('@') and barcode.endswith('@'):
        new_item = Item(barcode, storage_location, expiry_date)
        new_item.add_item_to_database()
        return render_template('add_item.html')
    else:
        flash("Invalid barcode format!!", 'danger')
        return render_template('add_item.html')


# endregion

# region Code for displaying item
@app.route('/retrieve_item', methods=['POST', 'GET'])
@login_is_required
def retrieve_item():
    barcode = request.form['tbx_barcode']
    barcode = barcode.strip()
    barcode = barcode.removeprefix("@")
    barcode = barcode.removesuffix("@")
    barcode = barcode.strip()
    items = mongo.db.items
    item = items.find_one({'barcode': barcode})
    food_item = item['name']
    item_recipes = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system",
                   "content": "You are a helpful recipe giving bot, your task is to generate a list of 10 and only 10 "
                              "possible recipes that can be made using a given ingredient. I will provide you with "
                              "the ingredient, and you should suggest"
                              "a variety of recipe types that can be made using that ingredient. Please do not "
                              "include the ingredients or instructions on how to make the recipes, but focus on "
                              "providing a diverse range of recipe ideas that utilize the given ingredient. Please "
                              "note that your response should be flexible enough to allow for various relevant and "
                              "creative recipe suggestions. You should aim to provide a wide range of recipe types, "
                              "such as appetizers, main courses, desserts, and beverages, to cater to different "
                              "preferences and tastes, below is the ingredient:"}, {"role": "user", "content": food_item}]
    )
    recipes = item_recipes.choices[0].message.content
    if item and item_recipes:
        return render_template('view_item.html', items=item, recipes=recipes)


# endregion


if __name__ == '__main__':
    app.run()
