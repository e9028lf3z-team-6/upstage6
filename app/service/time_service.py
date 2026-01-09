# app/service/time_service.py

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class TimeInfo:
    timezone: str
    datetime_iso: str
    hhmm: str


class TimeService:
    def get_current_time(self, timezone: str) -> TimeInfo:
        """
        주어진 timezone의 현재 시간을 반환한다.
        외부 API 의존 없음.
        """
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            raise ValueError(f"Invalid timezone: {timezone}")

        now = datetime.now(tz)

        return TimeInfo(
            timezone=timezone,
            datetime_iso=now.isoformat(),
            hhmm=now.strftime("%H:%M"),
        )
