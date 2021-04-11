#!/usr/bin/env python3

import re
import socket
import sys
import argparse
from Server import Server
from tools import Debuger

VERBOSITY = 0
NAMES = []

SSN_REGEX = "^(?!000)([0-6]\d{2}|7([0-6]\d|7[012]))([ -]?)(?!00)\d\d\3(?!0000)\d{4}$"
SSN_QUERY_REGEX = "ssn|social"
EMAIL_REGEX = "^\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}$"
CC_REGEX ="((\d{4}-?\d{4}-?\d{4}-?\d{4})|())"

def is_ssn(entry, q_param):
    return re.search(SSN_REGEX, entry) or re.search(SSN_QUERY_REGEX, q_param)


def is_cc(entry, q_param):
    return re.search(CC_REGEX, entry)


def is_email(entry, q_param):
    return re.search(EMAIL_REGEX, entry)


def is_name(entry, q_param):
    return entry in NAMES

useful_information = {
    "social security number": is_name,
    "credit card number": is_cc,
    "email": is_email,
    "name": is_name
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(conflict_handler="resolve")
    parser.add_argument("-m", "--mode",
        help="""The mode you want your proxy to operate, which will either be
        active or passive""",
        required=True)
    parser.add_argument("-h", "--listening_ip",
        help="The IP address your proxy will listen on connections on",
        required=True)
    parser.add_argument("-p", "--listening_port",
        help="The port your proxy will listen for connections on",
        required=True)
    parser.add_argument("-v","--verbosity",
        help="verbosity level",
        action='count',
        default=0,
        required=False)
    args = parser.parse_args()
    debugger = Debuger(args.verbosity)

    server = Server(hostname=args.listening_ip,
                    port=int(args.listening_port),
                    verbosity=args.verbosity)
    server.start()
