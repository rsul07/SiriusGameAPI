import datetime
from unittest import TestCase

from events.schemas import SEvent

class TestSEventState(TestCase):
    def test_state(self):
        now = datetime.datetime.now(datetime.timezone.utc)

        future_kwargs = {
            "date": (now + datetime.timedelta(days=1)).date()
        }

        current_kwargs = {
            "date": now.date(),
            "start_time": datetime.time(0, 0),
            "end_time":   datetime.time(23, 59),
        }

        past_kwargs = {
            "date": (now - datetime.timedelta(days=1)).date()
        }

        cases = [
            (future_kwargs, "future"),
            (current_kwargs, "current"),
            (past_kwargs,   "past"),
        ]

        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                ev = SEvent(
                    id=1,
                    title="Test",
                    is_team=False,
                    max_members=10,
                    media=[],
                    **kwargs,
                )
                print(kwargs)
                self.assertEqual(ev.state, expected)