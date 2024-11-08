# SDM.QualityTesting

The SDM.QualityTesting service is a Python server dedicated to assessing the **quality** of a **data model** within the Smart Data Models program.

It offers an OpenAPI specification with two distinct paths: `/version` and `/qtest`.

**Path: `/version`**

- The `/version` path is used to provide clients with version information, including details such as the document, git hash, version, release date, and uptime.

**Path: `/qtest`**

- Description: A POST operation used to perform quality testing of a data model.
- Request Body: Expects a JSON payload with details of the data model, such as the GitHub URL to the data model's model.yaml, the associated email for testing, and the number of tests to be conducted

This service aims to streamline the quality assessment process for data models, providing a structured and efficient means of ensuring the robustness and reliability of the models within the Smart Data Models

# Poetry Initialization - Running the Project Locally 

Please note that this is a **Python 3.11** project, to install it, check this [link](https://www.python.org/downloads/).

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
    
4. **Deactivate and exit the virtual environment**: 
Once done, make sure to exit from the virtual environment by running this command:
    ```shell
    deactivate
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
  -i, --input FILEIN  description to specify the file to the script
  -o, --output        generate the corresponding output file
  -h, --host HOST     launch the server in the corresponding host
                      [default: 127.0.0.1]
  -p, --port PORT     launch the server in the corresponding port
                      [default: 5600]

  -H, --help          show this help message and exit
  -v, --version       show version and exit
  ``````

# OpenAPI documentation

the full OpenAPI specification is located under [doc/openapi.yaml](doc/openapi.yaml)

This specification defines two paths: `/version` and `/qtest`:  

## The `/version` path

- The purpose of the /version path is to provide clients with version information, including details such as the document, git hash, version, release date, and uptime. 
- The API defines an endpoint for retrieving version information. 
- When a `GET` request is sent to the `/version` path, the API returns a JSON object containing details such as the document, git hash, version, release date, and uptime. 
- The API logs relevant information, such as the request for version information, using the provided logger.

## The `/qtest` path

- The `/qtest` path serves as an endpoint for performing quality testing of a data model. 
- When a `POST` operation is sent to this path, the API expects a JSON payload containing details of the data model, such as the GitHub URL to the data model's model.yaml, the email associated with the testing, and the number of tests to be performed. 
- Upon receiving the request, the API processes the information, conducts the quality tests, and returns the results.
- The associated SDMQualityTesting schema, which defines the structure of the expected JSON payload, is utilized in this process. 
- the API logs relevant information, such as the request for quality testing and any potential errors, using the provided logger. 

# License
These scripts are licensed under Apache License 2.0.
