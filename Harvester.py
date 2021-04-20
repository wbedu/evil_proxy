#!/usr/bin/env python3

import sqlite3
import json
from urllib.parse import urlparse, parse_qs
import re

SSN_REGEX = "^(?!000)([0-6]\d{2}|7([0-6]\d|7[012]))([ -]?)(?!00)\d\d\3(?!0000)\d{4}$"
SSN_QUERY_REGEX = "ssn|social"
EMAIL_REGEX = "^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$"
CC_REGEX ="((\d{4}-?\d{4}-?\d{4}-?\d{4})|())"
NAMES = []
def is_ssn(value, param):
    return re.search(SSN_REGEX, value) or re.search(SSN_QUERY_REGEX, param)


def is_cc(value, param):
    return re.search(CC_REGEX, value)


def is_email(value, param):
    return re.search(EMAIL_REGEX, param)


def is_name(value, param):
    return value in NAMES

useful_information = {
    "social security number": is_name,
    "credit card number": is_cc,
    "email": is_email,
    "name": is_name
}


class Harvester:

    def __init__(self, server_ip, server_mode, database=None, names=[]):
        self.session = None
        NAMES = names
        self.server_ip = None
        self.server_mode = server_mode;
        try:
            self.conn = sqlite3.connect(database)
            self.db = database
        except:
            print(f"failed to connect to database({database})")
            self.conn = sqlite3.connect(":memory:")
            self.db = ":memory:"

        self.conn.execute('''CREATE TABLE IF NOT EXISTS HARVEST
                    (IP           TEXT    NOT NULL,
                    TYPE          TEXT    NOT NULL,
                    VALUE         TEXT    NOT NULL,
                    URL           TEXT    NOT NULL,
                    MODE          TEXT    NOT NULL,
                    SESSION       INT     NOT NULL);''')
        self.conn.commit()

        self.__create_table()


    def __create_table(self):
        self.conn.execute('''CREATE TABLE IF NOT EXISTS SESSIONS
                    (SESSION      INTEGER PRIMARY KEY AUTOINCREMENT,
                     IP           TEXT,
                     MODE         TEXT);''')
        self.conn.execute('''INSERT INTO SESSIONS (IP,MODE)
                    VALUES (?, ?)''',(self.server_ip, self.server_mode))
        self.conn.commit()

        cur = self.conn.execute('''SELECT SESSION FROM SESSIONS
                                   ORDER BY SESSION DESC LIMIT 1;''')

        self.session_id = cur.fetchone()[0]

    def __add(self, ip, type, value, url):
        conn = sqlite3.connect(self.db)
        conn.execute('''INSERT INTO HARVEST (IP, TYPE, VALUE, URL, MODE, SESSION)
                        VALUES (?, ?, ?, ?, ?, ?)''',(ip, type, value, url,
                        self.server_mode, self.session_id))
        conn.commit()

    def harvest(self, http_response, ip):
        query = parse_qs(urlparse(http_response.url).query)
        for param, value in query.items():
            for key, evaluator in useful_information.items():
                print("param: ", param, "value: ", value[0])
                print("key: ", key)
                if evaluator(value[0], param):
                    print("true")
                    self.__add(ip, str(param), str(value), http_response.url)
                else:
                    print("false")

    def __str__(self):
        cur = self.conn.execute("SELECT * from HARVEST")
        rows = [str(row) for row in cur.fetchall()]
        return "\r\n".join(rows)

    def __del__(self):
        self.conn.close();

if __name__ == "__main__":
    harvest = Harvester("localhost", "passive",database="harvest.sqlite")
    print(harvest)
