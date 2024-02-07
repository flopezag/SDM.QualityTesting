# SDM.QualityTesting

Python server to check the quality of a data model included in the Smart Data Models program

# Create a Python Virtual Environement 

Please note that this is a python 3.11 project, to install it chech this [link](https://www.python.org/downloads/).

To create a virtual environment in Python using the `venv` module, the following command can be executed in the terminal:

```shell
python3 -m venv venv
```
To activate a virtual environment named "venv" in the root path, you can use the following command:

```shell
source venv/bin/activate
```

# Poetry Initialization - Running the Project Locally 

To manage the dependencies in this project and for Python package management, Poetry is used. 

1. **Install Poetry:** 
Execute the following command in the terminal: 

    ```shell
    curl -sSL https://install.python-poetry.org | python -
    ```

2. **Activate the Virtual Environment:**
    Since this project has a virtual environment managed by Poetry, it can be activated using the following command:

    ```shell
    poetry env use 3.11
    poetry shell
    ```

3. **Install Dependencies:**
    If the project's dependencies are not installed, the following command can be used to install them based on the pyproject.toml and poetry.lock files:

    ```shell
    poetry install
    ```
    Another alternative is to use this command: 
    ```shell
    pip install -r requirements.txt
    ```

# Running the code 
To run the code use the following commands and instructions: 

```
Usage:
  sdm_qatesting.py run (--input FILE) [--output]
  sdm_qatesting.py server [--host HOST] [--port PORT]
  sdm_qatesting.py (-h | --help)
  sdm_qatesting.py --version

Arguments:
  FILE   input file
  PORT   http port used by the service

Options:
  -i, --input FILEIN  specify the RDF turtle file to parser
  -o, --output        generate the corresponding files of the parser RDF turtle file
  -h, --host HOST     launch the server in the corresponding host
                      [default: 127.0.0.1]
  -p, --port PORT     launch the server in the corresponding port
                      [default: 5600]

  -H, --help          show this help message and exit
  -v, --version       show version and exit
  ``````

# OpenAPI documentation

the full OpenAPI specification is located under [doc/openapi.yaml](doc/openapi.yaml)

This specification defines two paths: /version and /qtest:  

- The `/version` path has a single `GET` operation that returns version information. 
- The `/qtest` path has a single `POST` operation that performs quality testing of a data model. 

The `Local` and `SDMQualityTesting` schemas are also defined in the components section.

