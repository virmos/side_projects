@echo off
REM
set TITLE=OrderApp
set VERSION=1.0.0
set TIMEZONE=UTC+7
set DESCRIPTION=Application
set DEBUG=False
set TEST_PRICING_DB=src\static\db.txt
set PROD_PRICING_DB=src\static\testcase.txt
set USE_DB_FAST_LOAD=True
set USE_TEST_DB=True

REM
pytest tests
