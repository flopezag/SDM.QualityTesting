#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##
# Copyright 2024 FIWARE Foundation, e.V.
#
# This file is part of SDM Quality Testing
#
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
##

from fastapi import FastAPI, UploadFile, Request, Response, status, HTTPException
from fastapi.logger import logger as fastapi_logger
from uvicorn import run
from os.path import splitext
from datetime import datetime
from cli.command import __version__
from secure import (
    Server,
    ContentSecurityPolicy,
    StrictTransportSecurity,
    ReferrerPolicy,
    PermissionsPolicy,
    CacheControl,
    Secure,
)
from logging import getLogger
from pathlib import Path
from api.custom_logging import CustomizeLogger
#from requests import exceptions
from json import load
#from io import StringIO

initial_uptime = datetime.now()
logger = getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="SDM SQL Schema Generation", debug=False)

    logging_config_path = Path.cwd().joinpath("common/config.json")
    customize_logger = CustomizeLogger.make_logger(logging_config_path)
    fastapi_logger.addHandler(customize_logger)

    return app


application = create_app()


@application.middleware("http")
async def set_secure_headers(request, call_next):
    response = await call_next(request)
    server = Server().set("Secure")

    csp = (
        ContentSecurityPolicy()
        .default_src("'none'")
        .base_uri("'self'")
        .connect_src("'self'" "api.spam.com")
        .frame_src("'none'")
        .img_src("'self'", "static.spam.com")
    )

    hsts = StrictTransportSecurity().include_subdomains().preload().max_age(2592000)

    referrer = ReferrerPolicy().no_referrer()

    permissions_value = PermissionsPolicy().geolocation("self", "'spam.com'").vibrate()

    cache_value = CacheControl().must_revalidate()

    secure_headers = Secure(
        server=server,
        csp=csp,
        hsts=hsts,
        referrer=referrer,
        permissions=permissions_value,
        cache=cache_value,
    )

    secure_headers.framework.fastapi(response)

    return response


@application.get("/version", status_code=status.HTTP_200_OK)
def getversion(request: Request):
    request.app.logger.info("Request version information")

    data = {
        "doc": "...",
        "git_hash": "nogitversion",
        "version": __version__,
        "release_date": "no released",
        "uptime": get_uptime(),
    }

    return data


@application.post("/parse", status_code=status.HTTP_201_CREATED)
async def parse(request: Request, file: UploadFile, response: Response):
    request.app.logger.info(f'Request parse file "{file.filename}"')

    # check if the post request has the file part
    if splitext(file.filename)[1] != ".ttl":  # type: ignore[type-var]
        resp = {"message": "Allowed file type is only ttl"}
        response.status_code = status.HTTP_400_BAD_REQUEST
        request.app.logger.error(f'POST /parse 400 Bad Request, file: "{file.filename}"')
    else:
        try:
            content = await file.read()
        except Exception as e:
            request.app.logger.error(f'POST /parse 500 Problem reading file: "{file.filename}"')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        else:
            request.app.logger.info("File successfully read")

        # Prepare the content
        content = content.decode("utf-8")  # type: ignore[assignment]

        # Start parsing the file
        resp = {"message": "iaea iacta est"}
        response.status_code = status.HTTP_200_OK
        request.app.logger.error(f'POST /parse 200 OK, file: "{file.filename}"')

    return resp


def get_uptime():
    now = datetime.now()
    delta = now - initial_uptime

    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)

    fmt = "{d} days, {h} hours, {m} minutes, and {s} seconds"

    return fmt.format(d=days, h=hours, m=minutes, s=seconds)


def get_url():
    config_path = Path.cwd().joinpath("common/config.json")

    with open(config_path) as config_file:
        config = load(config_file)

    url = f"{config['broker']}/ngsi-ld/v1/entityOperations/create"

    return url


def launch(app: str = "server:application", host: str = "127.0.0.1", port: int = 5500):
    run(
        app=app,
        host=host,
        port=port,
        log_level="info",
        reload=True,
        server_header=False,
    )


if __name__ == "__main__":
    launch()
