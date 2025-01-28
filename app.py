from get_tile import generate_image, download_book_cover
from flask import Flask, render_template, send_file, request, abort
from publisher_country_ranges import generate_country_image, generate_publisher_image
from datasets.build_datasets import load_isbn_list_from_disk, get_npy_files_without_extension
from functools import lru_cache
from math import floor
import isbnlib, tqdm

app = Flask(__name__)

@lru_cache(maxsize=1) #only run this function once, and cache the result, instead of reloading into memory each time.
def load_datasets():
    isbn_dict={}
    dataset_list=get_npy_files_without_extension("./datasets")
    for dataset in tqdm.tqdm(dataset_list, desc="loading datasets into memory"):
        isbn_dict[dataset]=load_isbn_list_from_disk(f"./datasets/{dataset}.npy")
    return isbn_dict

@app.route("/")
def index():
    return render_template("index.html", datasets=get_npy_files_without_extension("./datasets"))

@app.route("/map", methods=['GET'])
def map_view():
    # Extract dataset-color pairs from query parameters
    pairs = []
    for key, value in request.args.items():
        if key.startswith("dataset-"):
            pair_id = key.split("-")[1]
            color_key = f"color-{pair_id}"
            color = request.args.get(color_key)
            if color:
                pairs.append((value, color))
    if len(pairs)>10:
        abort(404, description="Too many pairs submitted.")
    return render_template("map.html", pairs=pairs)

@app.route("/static/tiles/<dataset_name>/<color>/<int:z>/<int:y>/<int:x>.webp")
def serve_tile(dataset_name,color,z,y,x):
    if 0<z<=16:
        datasets=load_datasets()
        if dataset_name not in datasets:
            abort(404, description="invalid dataset")
        file=generate_image(z, y, x, color, dataset_name, datasets, use_cache=True)
        return send_file(file, mimetype='image/webp')
    else:
        abort(404, description="invalid z value")

@app.route("/static/tiles/book_covers/<int:z>/<int:y>/<int:x>.jpg")
def serve_book_covers(z,y,x):
    if z != 0:
        abort(404, description="Covers only displayed at highest zoom level (z should be 0)")
    file=download_book_cover(z, y, x, use_cache=True)
    return send_file(file, mimetype='image/jpg')

@app.route("/static/tiles/countries/<int:z>/<int:y>/<int:x>.webp")
def serve_countries_tile(z, y, x):
    if not (0 < z <= 16): # do not load country overlay when on layer 0 with book covers (which would add tint) 
        abort(404, description="invalid z value")
    file = generate_country_image(z, y, x, use_cache=True)
    return send_file(file, mimetype='image/webp')

@app.route("/static/tiles/publishers/<int:z>/<int:y>/<int:x>.webp")
def serve_publishers_tile(z, y, x):
    if not (0 < z <= 16): # do not load country overlay when on layer 0 with book covers (which would add tint) 
        abort(404, description="invalid z value")
    file = generate_publisher_image(z, y, x, use_cache=True)
    return send_file(file, mimetype='image/webp')

@app.route('/get_popup')
def get_popup():
    y = floor(-256 * float(request.args.get('lat')))
    x = floor(256 * float(request.args.get('lng')))
    isbn12 = 978_000_000_000 + x + (2**16) * y
    isbn13 = str(isbn12) + isbnlib.check_digit13(str(isbn12))

    try:
        masked_isbn13 = isbnlib.mask(isbn13)
        isbn13 = masked_isbn13 if masked_isbn13 else isbn13
        meta = isbnlib.meta(isbn13)
    except:
        return "Invalid ISBN or Metadata"

    AAlink=f"https://annas-archive.se/search?q={isbn13}"
    OLlink=f"https://openlibrary.org/isbn/{isbn13}"
    isbn_info=isbnlib.info(isbn13)

    return render_template("popup.html", isbn13=isbn13, meta=meta,
                            AAlink=AAlink, OLlink=OLlink, isbn_info=isbn_info)

if __name__ == "__main__":
    load_datasets() # initial loading of datasets into memory
    app.run(host="0.0.0.0", debug=True) # Available to local network, and live update changes 