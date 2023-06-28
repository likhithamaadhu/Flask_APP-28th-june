# Below are in built import
import json
import urllib.request

# Below are installed import
from sqlalchemy import insert
from sqlalchemy.schema import DDL

# Below are custom imports
from app.models import Book, books_schema
from app import db, create_app

app = create_app()
with app.app_context():

    def download_data():
        print("Fetching data from URL")
        try:
            url = "https://my-json-server.typicode.com/dmitrijt9/book-api-mock/books"
            response = urllib.request.urlopen(url)
            data = response.read().decode("UTF-8")
            data = json.loads(data)
        except Exception as error:
            print(str(error))

        return data

    def load_data():
        parsed_data = download_data()
        count=len(parsed_data)
        errors =books_schema.validate(parsed_data)
        if errors:
            print(errors)

        db.session.execute(insert(Book), parsed_data)
        alter_sequence = DDL(f"SELECT setval('book_id_seq', {count}, true);")
        db.session.execute(alter_sequence)
        db.session.commit()

    load_data()