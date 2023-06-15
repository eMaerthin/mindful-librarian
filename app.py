import base64

import certifi
from flask import Flask, jsonify, render_template, request, redirect, send_from_directory
from flask_restful import Api, Resource
from json import JSONEncoder
from flasgger import Swagger, swag_from
import os
from bson import json_util, ObjectId
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import openai
from PIL import Image
import requests
from io import BytesIO


openai.api_key = os.getenv("OPENAI_API_KEY")
# define a custom encoder point to the json_util provided by pymongo (or its dependency bson)
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj): return json_util.default(obj)

# TODO: make JWT working


class HelloWorld(Resource):
    def get(self):
        """
        This is an example endpoint that returns a hello message.
        ---
        responses:
            200:
                description: A hello message
        """
        return jsonify({'message': 'Hello World'})


app = Flask(__name__, static_folder='assets')
app.json_encoder = CustomJSONEncoder
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', None)
mongo_conn_str = os.environ.get('MONGO_CONN_STR')
client = MongoClient(mongo_conn_str, server_api=ServerApi('1'), tlsCAFile=certifi.where())

# database name
database_name = 'mindfullibrarian'

# db conn
db = client[database_name]

# collection names
TAGS_COLLECTION = 'tags'
ASSETS_COLLECTION = 'assets'

tags_collection = db[TAGS_COLLECTION]
assets_collection = db[ASSETS_COLLECTION]

api = Api(app)
api.add_resource(HelloWorld, '/')

swagger = Swagger(app)


@app.route('/assets/img/<path:filename>', methods=["GET"])
def serve_static(filename):
    print('i am here1' + filename)
    return send_from_directory(app.static_folder, os.path.join('img', filename))


@app.route('/tags', methods=['GET'])
def get_tags():
    """
    This is an endpoint to get tags from db.
    ---
    responses:
        200:
            description: added tags
    """
    tags = list(tags_collection.find())

    return {'tags': [elem['tag'] for elem in tags]}


@app.route('/new_asset', methods=['POST'])
def new_asset():
    """
    This is an endpoint to add asset to db.
    ---
    responses:
        200:
            description: tbd
    """
    return True


@app.route('/add_asset_type1', methods=['GET', 'POST'])
def add_asset():
    if request.method == 'POST':
        tags = request.form.get('tags')
        descriptions = request.form.get('descriptions')
        images = generate_images(tags, descriptions)
        # Save asset to MongoDB
        asset = {
            'tags': tags,
            'descriptions': descriptions,
            'images': images
        }
        assets_collection.insert_one(asset)

        return redirect('/welcome')

    return render_template('add_asset_type1.html')


test_image_dict = {
    'drawing of a hedgehog using pastel colours that resembles mood anxiety, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-BlI0Gqvq36cPPekrqdH1LXDR.png?st=2023-06-15T09%3A15%3A45Z&se=2023-06-15T11%3A15%3A45Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A22%3A49Z&ske=2023-06-15T21%3A22%3A49Z&sks=b&skv=2021-08-06&sig=WYYVxWp6XQwQEnCEwJwqUqKgnTZYm6P6JzzQOhoUV1I%3D',
    'drawing of a hedgehog using pastel colours that resembles mood happiness, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-rLs6Vn9zYjgqoDXd2vo0e5fU.png?st=2023-06-15T09%3A15%3A45Z&se=2023-06-15T11%3A15%3A45Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A33%3A33Z&ske=2023-06-15T21%3A33%3A33Z&sks=b&skv=2021-08-06&sig=nv5Ctp6vtzm62Jn6apg/cBs47YndeL9kS4eN1nWn7uE%3D',
    'drawing of a hedgehog using pastel colours that resembles mood loneliness, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-ZnE7Y0CO4Rh0jprLVAfLBlqH.png?st=2023-06-15T09%3A15%3A45Z&se=2023-06-15T11%3A15%3A45Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A30%3A48Z&ske=2023-06-15T21%3A30%3A48Z&sks=b&skv=2021-08-06&sig=ugb2QxhthT2y8hYFdxmDOPwrnW0cjZDwiYoglbXVUyI%3D',
    'drawing of a hedgehog using pastel colours that resembles mood boredom, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-uoC3gZ4GjtxqYnBops96xe64.png?st=2023-06-15T09%3A15%3A45Z&se=2023-06-15T11%3A15%3A45Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A21%3A31Z&ske=2023-06-15T21%3A21%3A31Z&sks=b&skv=2021-08-06&sig=flMe6DCrc1vZl/SuVkrrFBoe5EUa8aqZJvcr36eXqe0%3D',
    'drawing of a hedgehog using pastel colours that resembles mood emptiness, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-sgPA4AJ7uzr1gDBLcso4p6sZ.png?st=2023-06-15T09%3A15%3A45Z&se=2023-06-15T11%3A15%3A45Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A21%3A04Z&ske=2023-06-15T21%3A21%3A04Z&sks=b&skv=2021-08-06&sig=rT0oGNXxArVgltpNde8VHRRWVOQM4GtlfruEEoJTqgk%3D',
    'drawing of a hedgehog using pastel colours that resembles mood fear, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-bbTdqeMUMDhs9ymFIVjYdbnj.png?st=2023-06-15T09%3A15%3A46Z&se=2023-06-15T11%3A15%3A46Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A22%3A49Z&ske=2023-06-15T21%3A22%3A49Z&sks=b&skv=2021-08-06&sig=pXKkrRuZuAdqeZG3rz9tw2mzJ5guNyWkvqrfANlStu8%3D',
    'drawing of a hedgehog using pastel colours that resembles mood anger, digital art': 'https://oaidalleapiprodscus.blob.core.windows.net/private/org-TGLG42S8xYW1UWHtlGqY8fW3/user-maoT5wjkgIbhvhlYG1m0vwEj/img-EW2v1608cLZeyKJVY6plcwBx.png?st=2023-06-15T08%3A59%3A21Z&se=2023-06-15T10%3A59%3A21Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-06-14T21%3A25%3A34Z&ske=2023-06-15T21%3A25%3A34Z&sks=b&skv=2021-08-06&sig=7mkSVOqC7%2BSvrQr0fXXagijcrmfK9kFkYW7FtVLu8uo%3D'
}

def image_to_data_uri(image):
    # Convert the image to a data URI
    image_buffer = BytesIO()
    image.save(image_buffer, format='PNG')
    image_binary = image_buffer.getvalue()
    data_uri = 'data:image/png;base64,' + base64.b64encode(image_binary).decode('utf-8')
    return data_uri

@app.route('/welcome', methods=["GET"])
def welcome():
    last_assets = assets_collection.find().limit(10)
    #for asset in last_assets:
    #    asset["data_uri"] = image_to_data_uri(asset["image"])
    return render_template("welcome.html")#, last_assets=last_assets)


@app.route('/image', methods=["POST"])
def image():
    text = request.json.get("input")
    document_id = request.json.get("id")
    print(f'image: {text}')
    if text in test_image_dict:
        return jsonify({
        "id": document_id,
        "url": test_image_dict[text]}
    )
    dalle_res = openai.Image.create(
        prompt=text,
        n=1,
        size="256x256"
    )
    output = dalle_res['data'][0]['url']
    x = jsonify({
        "id": document_id,
        "url": output}
    )
    return x


def generate_images(tags, descriptions):
    # Call external API to generate images based on tags and descriptions
    # ...
    # Return a list of generated image URLs
    return ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']


@app.route('/build_mosaic', methods=["POST"])
def build_mosaic(cols=None, rows=None):
    image_urls = request.json.get("input")
    # Calculate the size of each tile
    tile_width = 256
    tile_height = 256
    if cols is None and rows is None:
        cols = len(image_urls)
        rows = 1
    # Create a blank canvas for the mosaic
    mosaic_width = cols * tile_width
    mosaic_height = rows * tile_height
    mosaic = Image.new('RGB', (mosaic_width, mosaic_height))

    # Iterate over the image URLs and paste each image as a tile in the mosaic
    for i, url in enumerate(image_urls):
        # Fetch the image from the URL
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))

        # Resize the image to fit the tile size
        image = image.resize((tile_width, tile_height))

        # Calculate the position of the tile in the mosaic
        row = i // cols
        col = i % cols
        x = col * tile_width
        y = row * tile_height

        # Paste the image onto the mosaic
        mosaic.paste(image, (x, y))
    image_buffer = BytesIO()
    mosaic.save(image_buffer, format='PNG')
    image_binary = image_buffer.getvalue()

    # Save the image to MongoDB
    result = assets_collection.insert_one({'image': image_binary, 'type': 'img', 'name': 'test'})
    inserted_id = result.inserted_id
    return {'inserted_id': inserted_id}


if __name__ == '__main__':
    app.run(debug=True)
