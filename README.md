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
