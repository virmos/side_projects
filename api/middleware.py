import fastapi
import loguru
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, Response


class EntityDoesNotExist(Exception):
    pass


class StripeCurrencyException(Exception):
    pass


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except EntityDoesNotExist as e:
            return Response(repr(e), status_code=fastapi.status.HTTP_400_BAD_REQUEST)
        except StripeCurrencyException as e:
            return Response(repr(e), status_code=fastapi.status.HTTP_400_BAD_REQUEST)
        except fastapi.HTTPException as err:
            loguru.logger.error(err)
            return Response(err.detail if hasattr(err, "detail") else repr(err), status_code=err.status_code)
        except Exception as err:
            loguru.logger.error(err)
            return Response(repr(err), status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR)


