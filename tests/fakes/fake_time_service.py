from dataclasses import dataclass

@dataclass
class FakeTimeInfo:
    hhmm: str

class FakeTimeService:
    def get_current_time(self, timezone: str):
        return FakeTimeInfo(hhmm="13:30")
