# My Python Project

This is my task regarding the XM interviews. It uses FastAPI and other dependencies listed in `requirements.txt`.

## Project Structure

- `main.py`: The main application file.
- `tests.py`: The file containing tests for the application.
- `requirements.txt`: The file containing the list of dependencies.

## Requirements

- Docker
- Python 3.11

## Setup

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2. **Build the Docker image**:

    ```bash
    docker build -t my-python-app .
    ```

3. **Run the Docker container**:

    ```bash
    docker run -p 80:80 my-python-app
    ```

4. **Run tests** (optional):

    ```bash
    docker run my-python-app pytest tests.py
    ```

## Usage

Once the Docker container is running, you can access the application by navigating to `http://localhost:5734` in your web browser or using tools like `curl` or Postman to interact with the API.

## Dependencies

The project uses the following dependencies:

- FastAPI
- Pydantic
- Pytest
- Websockets
- Numpy

These are specified in the `requirements.txt` file and are installed automatically when you build the Docker image.
