from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'

db = SQLAlchemy(app)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Unicode, nullable=False)
    inventory = db.Column(db.Integer, nullable=False)


@app.route('/')
def index():
    return 'index'


if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', debug=True)
