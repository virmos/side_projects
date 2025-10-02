# PriceChecker Service (FastAPI)

## Quickstart

### For Windows users

1. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_test.txt
```

2. Run the server

```bash
source run.sh
```

```Command Prompt
run.bat
```

3. Instructions

Environments are put in run.sh/run.bat file
- If USE_DB_FAST_LOAD=True, then the program will load the database in to memory at once, then build datastructure from it. With the risk of memory overflow.
- If USE_DB_FAST_LOAD=False, then the program will asynchronously load the database by batch, memory safe, but slower.

Default data is loaded from src/static/db.txt

If we want to use production data:
- There is a larger testcase stored in testcase.txt. 
- Copy the content of such file in https://drive.google.com/file/d/1IXIotxzuS_iBRQKiv0CrzmcIi0QEvIDd/view?usp=drive_link
- Store it as src/static/testcase.txt
- Update environment variable USE_TEST_DB=False in run.sh/run.bat

=> Then the data will be loaded from src/static/testcase.txt


### Endpoints

- POST `/pricing/cheapest`: Get cheapest operator with phone number

### Sample payload

```json
{
    "phone_number": "+4612345678"
}
```
