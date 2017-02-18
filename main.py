from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

api = Api(app)
db = SQLAlchemy(app)


class Product(db.Model):
    """Database mapping for products."""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode, nullable=False)
    inventory = db.Column(db.Integer, nullable=False)


class ProductRepository(object):

    @property
    def session(self):
        return db.session

    @property
    def query(self):
        return self.session.query(Product)

    def get_all(self):
        return self.query


class ProductCollection(Resource):

    def __init__(self, repository_factory):
        self.repository = repository_factory()

    def get(self):
        return [{
                    'name': p.name,
                    'inventory': p.inventory
                } for p in self.repository.get_all()]


api.add_resource(ProductCollection, '/product', endpoint='product',
                 resource_class_args=[ProductRepository])


@app.route('/')
def index():
    return 'index'


def fixtures():
    s = db.session()
    for i in range(1, 10):
        s.add(Product(name="Product {}".format(i), inventory=i))
    s.commit()

if __name__ == '__main__':
    db.create_all()
    fixtures()
    app.run(host='0.0.0.0', debug=True)
