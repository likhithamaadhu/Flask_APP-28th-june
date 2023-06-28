# installed imports
from flask import Blueprint, url_for, request, current_app
from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as upsert

# custom imports
from app.models import Book, post_books_schema, book_schema, books_schema
from app import db


# blueprint
book_api = Blueprint("book_api", __name__, url_prefix="/books")


# user defined  exceptions
class UserError(Exception):
    def __init__(self, message, code=400):
        self.message = message
        self.code = code


@book_api.errorhandler(UserError)
def handle_usererror(e):
    current_app.logger.exception(e)
    return {"success": False, "message": e.message}, e.code


# <<<<<<<<<< apis >>>>>>>>>>>>>>>>>>


@book_api.route("/", methods=["GET"])
@book_api.route("/<int:book_id>", methods=["GET"])
def get_book(book_id=None):
    pass


@book_api.route("/", methods=["POST"])
def create_book():
    """
    This API inserts the books into database.
    It can insert single row and multiple rows as well.

    payload : list of dictionaries

    "author_id": integer,
    "title": string,
    "cover_image": string,
    "pages": integer,
    "releaseDate": (year)string,
    "isbn": string
    """
    books = request.json
    books = books.get("data")

    errors = post_books_schema.validate(books)  # validating input data
    if errors:
        return {"validationerrors": errors}, 400

    if not books:
        raise UserError("data not found")
    try:
        db.session.execute(insert(Book), books)
        db.session.commit()
    except Exception as e:
        return {"error": str(e)}

    return {"success": True, "message": "inserted successfully"}, 201


@book_api.route("/", methods=["PUT"])
@book_api.route("/<int:book_id>", methods=["PUT"])
def update_book(book_id=None):
    """
    This API updates the book details in databse.
    it performs single update or bulk update.

    if the given id is not there in db it inserts that row.
    payload : list of dictionaries including "id"

    "id":integer
    "author_id": integer,
    "title": string,
    "cover_image": string,
    "pages": integer,
    "releaseDate": (year)string,
    "isbn": string
    """
    if book_id:
        book = request.json
        book["id"] = book_id
        books = [book]
    else:
        books = request.json.get("data")

    _books = []
    for row in books:
        # getting existing data from db for which
        # certain columns are not given in payload
        row_id = row.get("id")
        book = Book.query.filter_by(id=row_id).first()
        book = book_schema.dump(book)
        book.update(row)
        _books.append(book)

    errors = books_schema.validate(_books)
    if errors:
        return {"validationerrors": errors}, 400

    try:
        query = upsert(Book).values(_books)
        query = query.on_conflict_do_update(
            index_elements=[Book.id],
            set_=dict(
                author_id=query.excluded.author_id,
                title=query.excluded.title,
                cover_image=query.excluded.cover_image,
                pages=query.excluded.pages,
                releaseDate=query.excluded.releaseDate,
                isbn=query.excluded.isbn,
            ),
        )
        db.session.execute(query)
        db.session.commit()
    except Exception as e:
        return {"error": str(e)}
    return {"success": True, "message": "Updated successfully"}


@book_api.route("/", methods=["DELETE"])
@book_api.route("/<int:book_id>", methods=["DELETE"])
def delete_book(book_id=None):
    """
    This API deletes the books from database.
    it accepts both single and multiple ids

    payload:list

    id:integer

    for bulk delete, in the list of IDs, api delete the ids present in database and
    ignore which are not present in db.
    """
    id_list = [book_id] if book_id else request.json.get("data")
    print(id_list)

    if not id_list:
        raise UserError("Data not found")

    books = Book.query.filter(Book.id.in_(id_list))
    count = books.count()

    if not count:
        raise UserError("IDs not found")

    try:
        books.delete()
        db.session.commit()
    except Exception as e:
        return {"error": str(e)}
    return {"succes": True, "message": f"Deleted {count} row(s) successfully"}
