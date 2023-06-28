from dataclasses import dataclass
from app import db
from marshmallow import Schema,fields

@dataclass
class Book(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    author_id=db.Column(db.Integer)
    title=db.Column(db.Text,nullable=False)
    cover_image=db.Column(db.Text)
    pages=db.Column(db.Integer,nullable=False)
    releaseDate=db.Column(db.Text,nullable=False)
    isbn=db.Column(db.Text)

class PostBookSchema(Schema):
    author_id=fields.Integer(required=False,allow_none=True)
    title=fields.String(required=True)
    cover_image=fields.String(required=False,allow_none=True)
    pages=fields.Integer(required=True)
    releaseDate=fields.String(required=True)
    isbn=fields.String(required=False,allow_none=True)

post_books_schema=PostBookSchema(many=True)


class BookSchema(PostBookSchema):
    id=fields.Integer(required=True)

book_schema = BookSchema()
books_schema=BookSchema(many=True)