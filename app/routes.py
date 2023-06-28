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
    args = request.args

    sort = args.get("sort", "id")
    order = args.get("order", "asc")
    page_limit = args.get("page_limit", 10, type=int)
    page = args.get("page", 1, type=int)
    search = args.get("search")
    search_column = args.get("search_column")
    columns = (
        "id",
        "author_id",
        "pages",
        "title",
        "cover_image",
        "releaseDate",
        "isbn",
    )
    int_columns = ("id", "author_id", "pages")
    string_columns = ("title", "cover_image", "releaseDate", "isbn")

    books = Book.query

    print(order, type(order))

    if book_id:
        books = books.filter_by(id=book_id).first()

    try:
        if sort not in columns:
            raise UserError(
                'invalid sort argumnet. Only allowed "id","author_id","pages","title","cover_image","releaseDate","isbn"'
            )

        if order:
            order = order.lower()
            if order not in ("asc", "desc"):
                raise UserError("invald oder argument.only allowed 'asc','desc'")

        if search:
            print(search_column, search_column in int_columns)
            if isinstance(search, str) and search_column in int_columns:
                try:
                    search = int(search)
                except:
                    raise UserError("Cant search a string in int columns")

            if search_column in int_columns:
                books = books.filter(getattr(Book, search_column) == search)
            elif search_column in string_columns:
                books = books.filter(getattr(Book, search_column).ilike(f"%{search}%"))
            else:
                raise UserError("invalid search column")

        books = books.order_by(getattr(getattr(Book, sort), order)())

        books = books.paginate(page=page, per_page=page_limit)

        book_list = books_schema.dump(books)

        if not book_list:
            raise UserError("no content found")

        if books.has_next:
            next_url = url_for("book_api.get_book", page=books.next_num)
        else:
            next_url = None

        if books.has_prev:
            previous_url = url_for("book_api.get_book", page=books.prev_num)
        else:
            previous_url = None

        books_data = dict(
            book_details=book_list,
            total=books.total,
            current_page=books.page,
            page_limit=books.per_page,
            next_page=next_url,
            previous_page=previous_url,
        )

    except Exception as e:
        return {"error": str(e)}, 500
    return {
        "success": True,
        "Books": books_data,
        "message": "Data retrived succesfuly",
    }, 200


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
    return {"success": True, "message": "Updated successfully"}, 200


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
    return {"succes": True, "message": f"Deleted {count} row(s) successfully"}, 200
