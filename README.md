# FastAPI MVC Project


## Setup


1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate # on Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Initialize the database:

```bash
python init_db.py
```

3. Run the application:
```bash
uvicorn main:app --reload
```
## API Documentation
You can find the swagger in the corresponding file.

## Running Tests
To run the tests, use the command:

```bash
    pytest .\tests\<your test path>
```

To run the tests with coverage report, use the command:

```bash
    pytest --cov=app .\tests\<your test path>
```