#!/usr/bin/env python3

import re
import socket
import sys
import argparse
from Server import Server
from tools import Debuger
import time
VERBOSITY = 0

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
                    verbosity=args.verbosity,
                    mode=args.mode)
    server.start()

    # time.sleep(1)
    # server.stop()


    with open('./info 1.txt', mode='wt', encoding='utf-8') as result_file:
        data =  "\n".join(server.get_harvest())
        result_file.write(data)

    with open('./info 2.txt', mode='wt', encoding='utf-8') as result_file:
        data =  "\n".join(server.get_inject_replies())
        result_file.write(data)
