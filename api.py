#!/usr/bin/env python3

import responder

api = responder.API()

@api.route("/{cat}/{name}")
async def greet_world(req, resp, *, cat, name):
    resp.text = f"{cat}/{name}!"

@api.route("/favicon.ico")
async def greet_world(req, resp, *, favicon):
    resp.text = f"favicon.ico"

if __name__ == '__main__':
    api.run()
