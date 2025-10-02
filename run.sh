export TITLE=OrderApp
export VERSION=1.0.0
export TIMEZONE=UTC+7
export DESCRIPTION=Application
export DEBUG=False
export TEST_PRICING_DB=src\\static\\db.txt
export PROD_PRICING_DB=src\\static\\testcase.txt
export USE_DB_FAST_LOAD=True
export USE_TEST_DB=True

uvicorn src.main:backend_app --reload --workers 1 --port 8080