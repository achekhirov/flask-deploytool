import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import TypeDecorator, String
from deploytool import app
from datetime import datetime


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///releases.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Json(TypeDecorator):

    impl = String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

class Release(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    mpp = db.Column(db.String(10),unique=False,nullable=False)
    change_log = db.Column(Json(128))
    desc = db.Column(db.String(200),unique=False,nullable=False)
    date = db.Column(db.DateTime,default=datetime.utcnow)

    def __repr__(self):
        return f"Release mpp: {self.mpp} \nDescription: {self.desc} \nCreated on: {self.date}\nChanges: {self.change_log}"