import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.audit import AuditLog as AuditModel
import logging

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests with response time and store in audit table
    """

    # Paths to exclude from audit logging (health checks, docs, etc.)
    EXCLUDED_PATHS = {"/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        start_time = time.time()

        status_code = 500
        error_detail = None
        response = None

        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            error_detail = str(e)
            logger.error(f"Error processing request {request.url.path}: {error_detail}")
            raise

        finally:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {status_code} - "
                f"Time: {response_time_ms:.2f}ms"
            )

            try:
                self._save_audit_log(
                    method=request.method,
                    path=request.url.path,
                    query_params=(
                        str(dict(request.query_params))
                        if request.query_params
                        else None
                    ),
                    status_code=status_code,
                    response_time_ms=round(response_time_ms, 2),
                    client_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    error_detail=error_detail,
                )
            except Exception as db_error:
                logger.error(f"Failed to save audit log: {db_error}")

        return response

    def _save_audit_log(
        self,
        method: str,
        path: str,
        query_params: str,
        status_code: int,
        response_time_ms: float,
        client_ip: str,
        user_agent: str,
        error_detail: str = None,
    ):
        """
        Save audit log to database
        Uses a separate session to avoid interfering with request session
        """
        db: Session = SessionLocal()
        try:
            audit = AuditModel(
                method=method,
                path=path,
                query_params=query_params,
                status_code=status_code,
                response_time_ms=response_time_ms,
                client_ip=client_ip,
                user_agent=user_agent,
                error_detail=error_detail,
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database error saving audit: {e}")
        finally:
            db.close()
