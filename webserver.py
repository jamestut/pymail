#!/usr/bin/env python3
import argparse
from wsgiref.simple_server import make_server
import pymailwsgiapp

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", default=8000, type=int)
    ap.add_argument("--appkey", required=True)
    ap.add_argument("--sendto", required=True)
    args = ap.parse_args()

    pymailwsgiapp.set_destination(args.sendto)
    pymailwsgiapp.set_app_key(args.appkey)

    print(f"Serving on {args.host}:{args.port}")
    httpd = make_server(args.host, args.port, pymailwsgiapp.application)
    httpd.serve_forever()
