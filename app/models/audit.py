from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, index=True)

    # Request information
    method = Column(String(10), nullable=False, index=True)
    path = Column(String(500), nullable=False, index=True)
    query_params = Column(Text, nullable=True)

    # Response information
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=False) #in MS

    # Client information
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    error_detail = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, method={self.method}, path={self.path}, status={self.status_code}, time={self.response_time_ms}ms)>"
