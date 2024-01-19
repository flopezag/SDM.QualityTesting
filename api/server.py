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

from fastapi import FastAPI, Request, Response, status
from fastapi.logger import logger as fastapi_logger
from uvicorn import run
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
from json import load, JSONDecodeError
from common.config import CONFIG_DATA
from smartdatamodels.master_tests import SDMQualityTesting

initial_uptime = datetime.now()
logger = getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="SDM SQL Schema Generation", debug=False)

    customize_logger = CustomizeLogger.make_logger(config_data=CONFIG_DATA)
    fastapi_logger.addHandler(customize_logger)
    app.logger = customize_logger

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
    request.app.logger.info("GET /version - Request version information")

    data = {
        "doc": "...",
        "git_hash": "nogitversion",
        "version": __version__,
        "release_date": "no released",
        "uptime": get_uptime(),
    }

    return data


@application.post("/qtest", status_code=status.HTTP_200_OK)
async def qtest(request: Request, response: Response):
    request.app.logger.info(f'POST /qtest - Quality Testing of a Data Model')

    resp = dict()

    try:
        req_info = await request.json()
    except JSONDecodeError:
        request.app.logger.error("Missing JSON payload")

        resp = {
            "message": "It is needed to provide a JSON object in the payload with the details of the GitHub URL to the"
                       " Data Model model.yaml from which you want to generate the SQL Schema"
        }

        response.status_code = status.HTTP_400_BAD_REQUEST
        return resp

    url = req_info["url"]
    email = req_info["email"]
    tests = req_info["tests"]

    request.app.logger.debug(f'Request generate quality tests from URL:"{url}", tests:"{tests}", and email:"{email}"')

    sdm_quality_testing = SDMQualityTesting(data_model_repo_url=url, mail=email, last_test_number=tests)
    sdm_quality_testing.do_tests()

    #
    # # check if the post request has a valid GitHub URL to the model.yaml file of a Data Model in the SDM repository
    # if check_github_url(url=url):
    #     request.app.logger.debug(f'Valid GitHub URL: "{url}"')
    #     sql_schema = generate_sql_schema(model_yaml=url)
    #     request.app.logger.info(f'SQL Schema: \n"{sql_schema}"')
    #
    #     resp = {
    #         "message": sql_schema
    #     }
    #
    #     request.app.logger.info(f'POST /generate 200 OK')
    #
    #     return resp
    #
    # else:
    #     request.app.logger.error(f'Invalid GitHub URL: "{url}"')
    #     response.status_code = status.HTTP_400_BAD_REQUEST
    #     resp["message"] = f"Invalid GitHub URL: {url}"
    #    return resp
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


def check_github_url(url: str) -> bool:
    github_url_pattern = r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)"

    return True


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
