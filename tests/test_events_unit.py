from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens.events import EventBus

from tests.support import make_store


class EventBusPersistenceTests(unittest.TestCase):
    def test_events_are_persisted_via_sink(self):
        with tempfile.TemporaryDirectory() as directory:
            store = make_store(Path(directory))
            bus = EventBus("run-events", on_event=lambda event: store.append_event("run-events", event))
            bus.publish("started", {"source": "demo"})
            bus.publish("done", {"ok": True})
            bus.close()
            events = store.events("run-events")
            self.assertEqual([event["type"] for event in events], ["started", "done"])
            self.assertEqual([event["seq"] for event in events], [0, 1])
            self.assertTrue(bus.closed)
