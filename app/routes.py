from flask import Blueprint,url_for,request,current_app
from app.models import Book,post_books_schema,book_schema,books_schema
from app import db
from sqlalchemy import insert


book_api = Blueprint('book_api',__name__,url_prefix='/books')

class UserError(Exception):
    def __init__(self,message,code=400):
        self.message=message
        self.code=code

@book_api.errorhandler(UserError)
def handle_usererror(e):
    current_app.logger.exception(e)
    return{"success":False,"message":e.message},e.code

# <<<<<<<<<< apis >>>>>>>>>>>>>>>>>>

@book_api.route('/',methods=['GET'])
@book_api.route('/<int:book_id>',methods=['GET'])
def get_book(book_id=None):
    pass

@book_api.route('/',methods=['POST'])
def create_book():
    books=request.json
    books=books.get('data')

    if not books:
        raise UserError('data not found')
    
    errors=post_books_schema.validate(books)
    if errors:
        return{"validationerrors":errors},400
    try:
        db.session.execute(insert(Book),books)
        db.session.commit()
    except Exception as e:
        return {"error":str(e)}
    
    return {"success":True,"message":"inserted successfully"},201


@book_api.route('/',methods=['PUT'])
@book_api.route('/<int:book_id>',methods=['PUT'])
def update_book(book_id=None):
    pass

@book_api.route('/',methods=['DELETE'])
@book_api.route('/<int:book_id>',methods=['DELETE'])
def delete_book(book_id=None):
    pass