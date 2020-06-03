from flask import Blueprint, current_app, jsonify, make_response, request
from json import loads
from image_server.meta import get_identity_file
from image_server.file import find_file
from PIL import Image
import io
import re

bp = Blueprint(__name__, __name__)


def make_response_from_image(img):
    output = io.BytesIO()
    img.save(output, format='JPEG')

    response = make_response(output.getvalue())
    response.headers.set('Content-Type', 'image/jpeg')
    return response


def resize_image(image, width, height):
    w = h = None
    if width == '' and height == '':
        return image
    elif width == 'auto' and height == 'auto':
        return image
    elif re.search("^(auto)?$", width):
        delta = int(height) / image.height
        w = image.width * delta
        h = height
    elif re.search("^(auto)?$", height):
        delta = int(width) / image.width
        w = width
        h = image.height * delta
    else:
        w = width
        h = height
    return image.resize((int(w), int(h)))


@bp.route('/')
def list_owners_files():
    owner = 'mock'
    path = get_identity_file(owner)
    if path is None:
        return 'file not found', 404
    return jsonify(loads(open(path, 'r').read()))


@bp.route('/<file>')
def serve_file(file):
    path = find_file(file)
    if path is None:
        return 'file not found', 404

    img = Image.open(path)

    crop = request.args.get('crop', '')
    if re.search("^\d+(,\d+){3}$", crop):
        crop = tuple([int(x) for x in crop.split(',')])
        img = img.crop(crop)

    rot = request.args.get('rotation', '0')
    if re.search("\d", rot) and rot != '0':
        img = img.rotate(int(rot))

    width = request.args.get('width', '')
    height = request.args.get('height', '')
    img = resize_image(img, width, height)

    return make_response_from_image(img)
