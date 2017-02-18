import functools

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from marshmallow import fields, Schema, post_load, validates, ValidationError
from math import ceil
from werkzeug.utils import cached_property


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

api = Api(app)
db = SQLAlchemy(app)


@app.errorhandler(ValidationError)
def validation_error_handler(error):
    """Transforms validation error messages in a json response."""
    response = jsonify(error.messages)
    response.status_code = 400
    return response


class Product(db.Model):
    """Database mapping for products."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode, nullable=False)
    inventory = db.Column(db.Integer, nullable=False)


class Repository(object):
    """Generic repository pattern"""
    model = None

    @property
    def session(self):
        return db.session

    @property
    def query(self):
        assert self.model, "A model is required to use the query property."
        return self.session.query(self.model)

    def get_all(self):
        return self.query

    def save(self, entity):
        self.session.add(entity)
        self.session.commit()
        return entity


class ProductRepository(Repository):
    """Repository implementation for products.
    Any specific logic for products should be contained here.
    """
    model = Product


class ProductCollectionSchema(Schema):
    """Schema used to serialize products on collection view"""
    id = fields.Integer()
    name = fields.String()
    inventory = fields.Integer()


class ProductCreateSchema(Schema):
    """Schema used to parse and validate product data on create"""
    name = fields.String(required=True)
    inventory = fields.Integer(required=True)

    @validates('inventory')
    def validate_inventory(self, value):
        if value < 0:
            raise ValidationError('Invalid negative inventory.')

    @post_load
    def make_product(self, data):
        return Product(**data)


def marshall_with(schema, **kwargs):
    """Decorator to serialize output using specified schema
    :param kwargs will be passed down to the dump method from marshmallow Schema
    """
    serializer = functools.partial(schema.dump, **kwargs)

    def decorator(f):
        @functools.wraps(f)
        def inner(*fargs, **fkwargs):
            rv = f(*fargs, **fkwargs)
            return jsonify(serializer(rv).data)
        return inner
    return decorator


def parse_with(schema, arg_name='entity', **kwargs):
    """Decorator used to parse json input using the specified schema
    :param kwargs will be passed down to the dump method from marshmallow Schema
    :param arg_name will be inserted as a keyword argument containing the
        deserialized data.
    """
    def decorator(f):
        @functools.wraps(f)
        def inner(*fargs, **fkwargs):
            json = request.get_json()
            entity, errors = schema.load(json, **kwargs)
            fkwargs.update({arg_name: entity})
            return f(*fargs, **fkwargs)
        return inner
    return decorator


class ProductCollection(Resource):
    """Minimalistic collection resource to illustrate basic behaviour"""

    def __init__(self, repository_factory):
        self.repository = repository_factory()

    @marshall_with(ProductCollectionSchema(), many=True)
    def get(self):
        return self.repository.get_all()

    @marshall_with(ProductCollectionSchema())
    @parse_with(ProductCreateSchema(strict=True))
    def post(self, entity):
        return self.repository.save(entity)


api.add_resource(ProductCollection, '/product', endpoint='product',
                 resource_class_args=[ProductRepository])


@app.route('/')
def index():
    return 'index'


def fixtures():
    """Bootstrap product table with a few products"""
    s = db.session()
    for i in range(1, 10):
        s.add(Product(name="Product {}".format(i), inventory=i))
    s.commit()

if __name__ == '__main__':
    db.create_all()
    fixtures()
    app.run(host='0.0.0.0', debug=True)
