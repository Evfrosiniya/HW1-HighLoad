import argparse
import os
import sys

from server import HttpServer
from extensions import Handler

HOST = '127.0.0.1'
PORT = 80
LISTNERS = 100
MSGSIZE = 1024

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r', '--root', default=os.environ.get('DOCUMENT_ROOT'), help='Root directory for reading files')
    parser.add_argument(
        '-c', '--ncpu', default=3, type=int, help='Number of cpu')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if not os.path.exists(args.root):
        print("Please, check root directory.")
        sys.exit()

    server = HttpServer()
    server.start(args.root, Handler, HOST, PORT, args.ncpu, LISTNERS, MSGSIZE)
