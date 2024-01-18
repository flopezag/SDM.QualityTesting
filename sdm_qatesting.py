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

from cli.command import parse_cli
from api.server import launch

if __name__ == "__main__":
    args = parse_cli()

    if args["run"] is True:
        file_in = args["--input"]
        generate_files = args["--output"]

        # my_parser = Parser()
        #
        # try:
        #     my_parser.parsing(content=file_in, out=generate_files)
        # except UnexpectedToken as e:
        #     print(e)
        # except UnexpectedInput as e:
        #     print(e)
        # except UnexpectedEOF as e:
        #     print(e)

    elif args["server"] is True:
        port = int(args["--port"])
        host = args["--host"]

        launch(app="api.server:application", host=host, port=port)
