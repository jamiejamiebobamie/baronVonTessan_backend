import os
from flask import Flask, render_template, request
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

MONGO_URI = str(os.environ.get('MONGO_URI'))
# MONGO_URI = "mongodb://127.0.0.1:27017/database"
mongo = MongoClient(MONGO_URI)

from random import randrange, randint
from flask_cors import CORS, cross_origin
# public API, allow all requests *
# cors = CORS(app, resources={r"/api/*": {"origins": "https://baron-von-tessan.herokuapp.com"}}) # change this to only accept from my frontend

@app.route('/')
def _main():
    greeting="hello this is my app"
    return render_template('index.html', title='Home',greeting=greeting)

# pull quote from db.
@app.route('/test-db')
def test_DB():

    db = mongo.db
    drawing_data_collection = db.BvT_drawingdata

    # print(number)
    rand_drawings = drawing_data_collection.aggregate([
      { "$sample": {"size": 1 }},
      {"$project": { "_id": { "$toString": "$_id" },
                      "vertices" : 1,
                      "description": 1,
                      "likes": 1}
       }
    ])
    rand_drawings = list(rand_drawings)

    return render_template('index.html', title='Home',greeting=rand_drawings)

# serve < number > random drawings from database
@app.route('/api/v1/random-drawings/<number>',methods=['GET'])
@cross_origin()
def serve_random_drawings(number):
    db = mongo.db
    drawing_data_collection = db.BvT_drawingdata

    # print(number)
    rand_drawings = drawing_data_collection.aggregate([
      { "$sample": {"size": int(number) }},
      {"$project": { "_id": { "$toString": "$_id" },
                      "vertices" : 1,
                      "description": 1,
                      "likes": 1}
       }
    ])
    rand_drawings = list(rand_drawings)
    # print(rand_drawings)
    return {"drawing_data": rand_drawings}

# serve <number> popular drawings from the database based on likes
@app.route('/api/v1/liked-drawings/<number>',methods=['GET'])
@cross_origin(["https://baron-von-tessan.herokuapp.com"])
def serve_liked_drawings(number):
    # get appropriate collection from database
    db = mongo.db
    drawing_data_collection = db.BvT_drawingdata
    # compute the length of the cllection (number of entries)
    length = drawing_data_collection.count()
    # sort the collection descendingly based on likes
    # skim the top third
    # this does not work. after doing some testing,
        # the: { "$sort": { "likes": -1} } option of the aggregate is not working
        # correctly. it is only partially sorting the collection...
    best_drawings = drawing_data_collection.aggregate([
      { "$sort": { "likes": -1} },
      { "$limit": length/3},
      {"$project": { "_id": { "$toString": "$_id" },
                      "vertices" : 1,
                      "description": 1,
                      "likes": 1}
       }
    ])
    # check to make sure the asked for number of drawings does not exceed the
        # length of the collection.
    number = int(number)
    if number > length:
        number = length

    # convert the mongodb aggregate into a list
    best_drawings = list(best_drawings)

    # initialize a return array for the data and a index increment.
    drawing_data = []

    # run a for loop for the given number of iterations
    for i in range(number):
        # get a random integer from 0 to
            # the length of the best_drawings array - the iteration number
        current_last = len(best_drawings)-1-i
        rand_integer = randint(0, current_last)
        rand_best_drawing = best_drawings[rand_integer]
        drawing_data.append(rand_best_drawing)
        # fisher-yates shuffle
        best_drawings[current_last], best_drawings[rand_integer] = best_drawings[rand_integer], best_drawings[current_last]

    # for debugging
    # for drawing in best_drawings:
    #     print(drawing["likes"],drawing["description"])
    return {"drawing_data": drawing_data}

# create new drawing document for database
@app.route('/api/v1/add-drawing-to-db',methods=['POST'])
@cross_origin(["https://baron-von-tessan.herokuapp.com"])
def add_drawing_to_db():
    inserted_ok = False
    data = request.get_json()
    if data:
        # if there are less than 5000 vertices and the description is not empty
            # and the description is not "I drew a...", create a new drawing
            # document
        if (len(data["drawingData"]) < 7000
            and len(data["drawingDescription"])
            and data["drawingDescription"] != "I drew a..."):

            print(len(data["drawingData"]) < 7000
                , len(data["drawingDescription"])
                , data["drawingDescription"] != "I drew a...")
                
            db = mongo.db
            drawing_data_collection = db.BvT_drawingdata

            vertices = data["drawingData"]
            description = data["drawingDescription"]
            likes = 0

            # a space needs to be added here for frontend...
            description = description.replace("|","") + " "
            new_document = {
                    "vertices" : vertices,
                    "description" : description,
                    "likes" : likes,
                }
            inserted_ok = drawing_data_collection.insert_one(new_document).acknowledged
    return {"success":inserted_ok}

# increment the likes of the drawings.
@app.route('/api/v1/increment-likes',methods=['POST'])
@cross_origin(["https://baron-von-tessan.herokuapp.com"])
def increment_likes():
    successes = [False]
    data = request.get_json()
    # data = {'IDs':["5fdf62a23bb1ca7d7473f476","5fdf63173bb1ca7d7473f477"]}
    if data:
        print(data)
        _ids = data["_ids"]
        if _ids:
            db = mongo.db
            drawing_data_collection = db.BvT_drawingdata
            for i in range(len(_ids)):
                object_id = _ids[i]
                drawing_document = drawing_data_collection.find_one({"_id": ObjectId(object_id) })
                if drawing_document:
                    likes = int(drawing_document["likes"])
                    likes += 1
                    success = drawing_data_collection.update_one( {"_id": ObjectId(object_id) },
                        {  "$set": { "likes": str(likes) }  }).acknowledged
                    if i == 0:
                        successes[0] = success
                    else:
                        successes.append(success)
    return { "success": all(successes) }


if __name__ == '__main__':
    # port = os.getenv("PORT", 7000)
    # app.run(host = '0.0.0.0', port = int(port), debug=True)
    app.run() # might need this if heroku doesn't want me to specify the port.
