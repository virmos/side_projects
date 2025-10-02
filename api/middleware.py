import fastapi
import loguru
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, Response


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except fastapi.HTTPException as err:
            loguru.logger.error(err)
            return Response(err.detail if hasattr(err, "detail") else repr(err), status_code=err.status_code)
        except Exception as err:
            loguru.logger.error(err)
            return Response(repr(err), status_code=fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR)

