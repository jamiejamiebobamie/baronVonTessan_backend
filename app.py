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

# serve 20 popular drawings from the database based on likes
@app.route('/api/v1/liked-drawings/<number>',methods=['GET'])
@cross_origin(["https://baron-von-tessan.herokuapp.com"])
def serve_liked_drawings(number):
    db = mongo.db
    drawing_data_collection = db.BvT_drawingdata

    length = drawing_data_collection.count()

    best_drawings = drawing_data_collection.aggregate([
      { "$sort": { "likes": -1} },
      { "$limit": length/3},
      # { "$sample": {"size": int(number) }},
      {"$project": { "_id": { "$toString": "$_id" },
                      "vertices" : 1,
                      "description": 1,
                      "likes": 1}
       }
    ])

    number = int(number)
    if number > length:
        number = length

    best_drawings = list(best_drawings)
    print(len(best_drawings),length)
    for drawing in best_drawings:
        print(drawing["description"],drawing["likes"])

    # testing.
    # length = max(length,20)
    drawing_data = []
    j = 0
    for i in range(number):
        rand_integer = randint(0,len(best_drawings)-1 - j)
        rand_best_drawing = best_drawings[rand_integer]
        drawing_data.append(rand_best_drawing)
        current_last = len(best_drawings)-1-j
        best_drawings[current_last], best_drawings[rand_integer] = best_drawings[rand_integer], best_drawings[current_last]
        j+=1
        # print(current_last,rand_integer,rand_best_drawing["likes"])
    # best_drawings = list(best_drawings)
    # print(best_drawings)
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
