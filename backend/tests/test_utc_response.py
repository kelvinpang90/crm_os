"""Timestamps leave this system saying which timezone they are in.

Every datetime column is written with `datetime.utcnow()`, so it is naive UTC.
Sent without a `Z` the browser reads it as local time by specification, which is
why a card created at 16:49 showed as 08:49. These guard the one place that
fixes it, and -- more to the point -- the three things that place must never do.
"""
import datetime
import decimal
import json

from app.utils.response import _render, fail, ok
from app.utils.utc import mark_utc


class TestMarkUtc:
    def test_a_naive_timestamp_is_marked(self):
        assert mark_utc("2026-09-12T08:49:20") == "2026-09-12T08:49:20Z"

    def test_fractional_seconds_survive(self):
        assert mark_utc("2026-09-12T08:49:20.123456") == "2026-09-12T08:49:20.123456Z"

    def test_a_space_separator_is_still_a_timestamp(self):
        assert mark_utc("2026-09-12 08:49:20") == "2026-09-12 08:49:20Z"

    def test_it_is_idempotent(self):
        """The reason this is done at the wire rather than at the ~20 services
        that build these payloads: two of them already append a `Z` by hand
        (`routers/messages.py:188`, `services/whatsapp_service.py:385`) and must
        not end up with two."""
        once = mark_utc("2026-09-12T08:49:20")
        assert mark_utc(once) == once == "2026-09-12T08:49:20Z"

    def test_an_offset_is_left_alone(self):
        assert mark_utc("2026-09-12T16:49:20+08:00") == "2026-09-12T16:49:20+08:00"
        assert mark_utc("2026-09-12T08:49:20+00:00") == "2026-09-12T08:49:20+00:00"

    def test_a_plain_date_is_never_touched(self):
        """`last_contact` and `due_date` are `date` columns. Stamped as
        "...T00:00:00Z" they read as the previous day on any browser west of
        Greenwich, and a task would fall due a day early."""
        assert mark_utc("2026-09-12") == "2026-09-12"

    def test_a_time_of_day_is_never_touched(self):
        assert mark_utc("08:49:20") == "08:49:20"

    def test_prose_that_merely_contains_a_timestamp_is_untouched(self):
        """Deal titles here carry order numbers and free text. The pattern is
        anchored at both ends so none of that is mistaken for a timestamp."""
        title = "[DEMO] Sony WF-C710N x 3 (order SO-2026-00002 at 2026-09-12T08:49:20)"
        assert mark_utc(title) == title

    def test_prose_that_ends_in_a_timestamp_is_untouched(self):
        """Separate from the case above, and not redundant: a pattern anchored
        only at the tail passes that one and mangles this one. AutoCount sync
        notes end in a time."""
        note = "Imported from AutoCount at 2026-09-12T08:49:20"
        assert mark_utc(note) == note

    def test_prose_that_starts_with_a_timestamp_is_untouched(self):
        """The mirror image, for a pattern anchored only at the head."""
        line = "2026-09-12T08:49:20 lead created from WhatsApp"
        assert mark_utc(line) == line

    def test_it_reaches_into_nested_structures(self):
        payload = {
            "items": [
                {"created_at": "2026-09-12T08:49:20", "last_contact": "2026-09-12"},
                {"created_at": "2026-09-12T08:50:00", "won_at": None},
            ],
            "meta": {"synced_at": "2026-09-12T10:00:00", "total": 2},
        }
        marked = mark_utc(payload)
        assert marked["items"][0]["created_at"] == "2026-09-12T08:49:20Z"
        assert marked["items"][0]["last_contact"] == "2026-09-12"
        assert marked["items"][1]["won_at"] is None
        assert marked["meta"]["synced_at"] == "2026-09-12T10:00:00Z"
        assert marked["meta"]["total"] == 2

    def test_non_strings_pass_through(self):
        assert mark_utc(None) is None
        assert mark_utc(42) == 42
        assert mark_utc(True) is True


class TestRender:
    """Through the envelope every response in this codebase is built with."""

    def test_ok_marks_the_timestamps_it_carries(self):
        body = json.loads(ok({"created_at": "2026-09-12T08:49:20"}).body)
        assert body["data"]["created_at"] == "2026-09-12T08:49:20Z"
        assert body["success"] is True

    def test_fail_goes_through_the_same_pass(self):
        body = json.loads(fail("no", fields={"seen_at": "2026-09-12T08:49:20"}).body)
        assert body["error"]["fields"]["seen_at"] == "2026-09-12T08:49:20Z"

    def test_a_list_payload_is_covered(self):
        body = json.loads(ok([{"created_at": "2026-09-12T08:49:20"}]).body)
        assert body["data"][0]["created_at"] == "2026-09-12T08:49:20Z"

    def test_a_raw_datetime_no_longer_explodes(self):
        """It used to be a 500: the encoder only knew `Decimal`. Passing one
        through now works, and arrives marked like everything else."""
        rendered = json.loads(_render({"at": datetime.datetime(2026, 9, 12, 8, 49, 20)}))
        assert rendered["at"] == "2026-09-12T08:49:20Z"

    def test_a_raw_date_stays_a_date(self):
        rendered = json.loads(_render({"due": datetime.date(2026, 9, 12)}))
        assert rendered["due"] == "2026-09-12"

    def test_decimals_still_work(self):
        """The behaviour that was already here, and must survive the change."""
        rendered = json.loads(_render({"amount": decimal.Decimal("986.70")}))
        assert rendered["amount"] == 986.70


def test_everything_marked_parses_back_as_utc():
    """The point of the exercise: a browser can now read the instant rather than
    guess at it."""
    parsed = datetime.datetime.fromisoformat(
        mark_utc("2026-09-12T08:49:20").replace("Z", "+00:00")
    )
    assert parsed.utcoffset() == datetime.timedelta(0)
    assert parsed.astimezone(datetime.timezone(datetime.timedelta(hours=8))).hour == 16
