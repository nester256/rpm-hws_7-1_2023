from config import *
from views import list_to_view
from psycopg2 import connect
from dotenv import load_dotenv
from os import getenv


load_dotenv()

PG_DBNAME = getenv('PG_DBNAME')
PG_HOST = getenv('PG_HOST')
PG_PORT = getenv('PG_PORT')
PG_USER = getenv('PG_USER')
PG_PASSWORD = getenv('PG_PASSWORD')


def is_num(value: any):
    return isinstance(value, (int, float))


class DbHandler:

    db_connection = connect(dbname=PG_DBNAME, host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASSWORD)
    db_cursor = db_connection.cursor()

    @classmethod
    def get_data(cls, req_conds: dict = None) -> dict:
        cls.db_cursor.execute(DbHandler.query_request(SELECTOR, req_conds) if req_conds else SELECTOR)
        ips = cls.db_cursor.fetchall()
        return {
            'number': len(ips),
            'rendered_ips': list_to_view(ips)
        }

    @classmethod
    def is_valid_token(cls, username: str, req_token: str):
        cls.db_cursor.execute(GET_TOKEN.format(username=username))
        db_token = cls.db_cursor.fetchone()
        if db_token:
            return db_token[0] == req_token
        return False

    @staticmethod
    def compose_insert(insert_data: dict):
        keys = tuple(insert_data.keys())
        values = [insert_data[key] for key in keys]
        attrs = ', '.join(keys)
        values = ', '.join([str(val) if is_num(val) else f"'{val}'" for val in values])
        return INSERT.format(table='college.ips', keys=attrs, values=values)

    @classmethod
    def update(cls, data: dict, where: dict):
        req = ', '.join([f"{key}={val}" if is_num(val) else f"{key}='{val}'" for key, val in data.items()])
        try:
            cls.db_cursor.execute(
                cls.query_request(UPDATE.format(table='college.ips', request=req), where) + RETURN_ID
            )
        except Exception as error:
            print(f'{__name__} error: {error}')
            return False
        ip_id = cls.db_cursor.fetchone()
        cls.db_connection.commit()
        return ip_id

    @classmethod
    def insert(cls, ips_data: dict):
        try:
            cls.db_cursor.execute(cls.compose_insert(ips_data))
        except Exception as error:
            print(f'{__name__} error: {error}')
            return False
        ip_id = cls.db_cursor.fetchone()[0]
        cls.db_connection.commit()
        return ip_id

    @classmethod
    def delete(cls, req_conds: dict):
        try:
            cls.db_cursor.execute(cls.query_request(DELETE.format(table='college.ips'), req_conds))
        except Exception as error:
            print(f'{__name__} error: {error}')
            return False
        cls.db_connection.commit()
        return bool(cls.db_cursor.rowcount)

    @staticmethod
    def query_request(request: str, req_conds: dict):
        conditions = []
        for attr, value in req_conds.items():
            if attr == "created":
                attr = f'{attr}::date'
            to_add = f'{attr}={value}' if isinstance(value, (int, float)) else f"{attr}='{value}'"
            conditions.append(to_add)
        return '{0} WHERE {1}'.format(request, ' AND '.join(conditions))
