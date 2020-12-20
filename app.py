import os
from flask import Flask, render_template, request
import pymongo
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = str(os.environ.get('MONGO_URI'))
MONGO_URI = "mongodb://127.0.0.1:27017/database"
mongo = MongoClient(MONGO_URI)

from random import randrange
from flask_cors import CORS, cross_origin
# public API, allow all requests *
cors = CORS(app, resources={r"/api/*": {"origins": "*"}}) # change this to only accept from my frontend

@app.route('/')
def _main():
    greeting="hello this is my app"
    return render_template('index.html', title='Home',greeting=greeting)

# pull quote from db.
@app.route('/test-db')
def test_DB():
    db = mongo.database
    drawing_data_collection = db.BvT_drawingdata

    return render_template('index.html', title='Home')

# serve 6 random drawings from the database
@app.route('/api/v1/six-random-drawings',methods=['GET'])
@cross_origin()
def serve_random_drawings():
    db = mongo.database
    drawing_data_collection = db.BvT_drawingdata
    length = drawing_data_collection.count()

    drawing_data = []
    for _ in range(6):
        rand_drawing = drawing_data_collection.find()[randrange(length)]
        # need to stringify the Mongo Object ID from the drawing object before
            # appending
        drawing_data.append(rand_drawing)
    return {"drawing_data": drawing_data}

# serve 20 popular drawings from the database based on likes
@app.route('/api/v1/twenty-liked-drawings',methods=['GET'])
@cross_origin()
def serve_random_drawings():
    db = mongo.database
    drawing_data_collection = db.BvT_drawingdata
    length = drawing_data_collection.count()

    best_drawings = drawing_data_collection.aggregate([
      { "$sort": { "likes": -1} },
      { "$limit": length/3}
    ])

    drawing_data = []
    for _ in range(20):
        rand_best_drawing = best_drawings.find()[randrange(length)]
        # need to stringify the Mongo Object ID from the drawing object before
            # appending
        drawing_data.append(rand_best_drawing)
    return {"drawing_data": drawing_data}

# create new drawing document for database
@app.route('/api/v1/add-drawing-to-db',methods=['POST'])
@cross_origin()
def serve_quote_from_input():
    inserted_ok = False
    data = request.get_json()
    if data:
        # if there are less than 5000 vertices and the description is not empty
            # and the description is not "I drew a...", create a new drawing
            # document
        if len(data["vertices"]) < 5000
            and len(data["description"])
            and data["description"] != "I drew a...":

            db = mongo.database
            drawing_data_collection = db.BvT_drawingdata

            vertices = data["vertices"]
            description = data["description"]
            likes = 0

            new_document = {
                    "vertices" : vertices,
                    "description" : description,
                    "likes" : likes,
                }
            inserted_ok = drawing_data_collection.insert_one(new_document).acknowledged
    return {"success":inserted_ok}

# increment the likes of the drawings.
@app.route('/api/v1/increment-likes',methods=['POST'])
@cross_origin()
def serve_quote_from_input():
    successes = [False]
    data = mongo.get_json()
    if data:
        if len(data["IDs"]):
            db = client.database
            drawing_data_collection = db.BvT_drawingdata
            for i in range(len(data["IDs"])):
                drawing_document = drawing_data_collection.find({"_id": ObjectId(data["drawingID"])})
                current_number_of_likes = drawing_document["likes"]
                success = cardstacks.update_one( {"_id": ObjectId(data["drawingID"])},
                    {  "$set": {"likes": current_number_of_likes + 1 }  }).acknowledged
                if i == 0:
                    successes[0] = success
                else:
                    successes.append(success)
    return { "success": all(successes) }


if __name__ == '__main__':
    port = os.getenv("PORT", 7000)
    app.run(host = '0.0.0.0', port = int(port), debug=True)
    # app.run() // might need this if heroku doesn't want me to specify the port.
