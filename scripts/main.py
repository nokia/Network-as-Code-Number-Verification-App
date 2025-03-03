#!/usr/bin/env python3
# Copyright (c) 2025 Nokia All rights reserved.
# Licensed under the BSD 3-Clause License
# SPDX-License-Identifier: BSD-3-Clause


import asyncio
import logging

import uvicorn
from fastapi import status
from html_server import app

logging.basicConfig(level=logging.DEBUG, format='%(levelname)-9s %(name)-12s: %(message)s - %(asctime)-8s')
logger = logging.getLogger("main")


@app.get("/healthz", status_code=status.HTTP_200_OK)
async def healthz():
    return


async def start_uvicorn():
    config = uvicorn.Config(app, host="0.0.0.0", port=8088, log_level="debug", workers=1, limit_concurrency=100, server_header=False)
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await asyncio.gather(
        start_uvicorn(),
    )

if __name__ == "__main__":
    asyncio.run(main())
