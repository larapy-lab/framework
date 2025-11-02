from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import traceback


class DatabaseFailedJobProvider:

    def __init__(self, database, table: str = "failed_jobs"):
        self.database = database
        self.table = table

    def log(self, connection: str, queue: str, payload: Any, exception: Exception) -> int:
        failed_at = datetime.now()

        if isinstance(payload, dict):
            payload = json.dumps(payload)
        elif isinstance(payload, str):
            pass
        else:
            payload = str(payload)

        exception_str = "".join(
            traceback.format_exception(type(exception), exception, exception.__traceback__)
        )

        return self.database.table(self.table).insert_get_id(
            {
                "uuid": self.generate_uuid(),
                "connection": connection,
                "queue": queue,
                "payload": payload,
                "exception": exception_str,
                "failed_at": failed_at,
            }
        )

    def all(self) -> List[Dict[str, Any]]:
        return list(self.database.table(self.table).order_by("id", "desc").get())

    def find(self, id: int) -> Optional[Dict[str, Any]]:
        return self.database.table(self.table).find(id)

    def forget(self, id: int) -> bool:
        return self.database.table(self.table).where("id", id).delete() > 0

    def flush(self, hours: Optional[int] = None) -> int:
        query = self.database.table(self.table)

        if hours:
            from datetime import timedelta

            cutoff = datetime.now() - timedelta(hours=hours)
            query = query.where("failed_at", "<", cutoff)

        return query.delete()

    def prune(self, before: datetime) -> int:
        return self.database.table(self.table).where("failed_at", "<", before).delete()

    def generate_uuid(self) -> str:
        import uuid

        return str(uuid.uuid4())
