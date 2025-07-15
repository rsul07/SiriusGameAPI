import datetime
from unittest import TestCase
from db.events import EventOrm


class TestEventState(TestCase):
    def test_state(self):
        now = datetime.datetime.now(datetime.timezone.utc)

        base_event_kwargs = {
            "title": "Test", "is_team": False, "max_members": 10
        }

        # --- Тестовые случаи ---
        future_kwargs = {
            "date": (now + datetime.timedelta(days=1)).date(),
            "start_time": datetime.time(10, 0),
            "end_time": datetime.time(12, 0),
        }
        current_kwargs = {
            "date": now.date(),
            "start_time": (now - datetime.timedelta(hours=1)).time(),
            "end_time": (now + datetime.timedelta(hours=1)).time(),
        }
        past_kwargs = {
            "date": (now - datetime.timedelta(days=1)).date(),
            "start_time": None,
            "end_time": None,
        }

        cases = [
            (future_kwargs, "future"),
            (current_kwargs, "current"),
            (past_kwargs, "past"),
        ]

        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                orm_event = EventOrm(**base_event_kwargs, **kwargs)
                self.assertEqual(orm_event.state, expected)
