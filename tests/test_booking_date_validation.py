"""Regression tests for Restful Booker booking-date validation."""

import os
from datetime import date, timedelta
from uuid import uuid4

import pytest
import requests


BASE_URL = os.getenv(
    "RESTFUL_BOOKER_BASE_URL", "https://restful-booker.herokuapp.com"
).rstrip("/")
REQUEST_TIMEOUT_SECONDS = 30


def booking_payload(checkin: str, checkout: str) -> dict:
    """Return unique booking data so a test never relies on existing records."""
    unique_suffix = uuid4().hex[:8]
    return {
        "firstname": f"DateTest-{unique_suffix}",
        "lastname": "Regression",
        "totalprice": 250,
        "depositpaid": True,
        "bookingdates": {
            "checkin": checkin,
            "checkout": checkout,
        },
        "additionalneeds": "None",
    }


def create_booking(payload: dict) -> requests.Response:
    """Create one booking and turn connection problems into readable failures."""
    try:
        return requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        pytest.fail(
            f"Could not call POST {BASE_URL}/booking within "
            f"{REQUEST_TIMEOUT_SECONDS} seconds: {exc}",
            pytrace=False,
        )


def response_summary(response: requests.Response) -> str:
    """Keep assertion output useful without dumping an unbounded response."""
    return response.text[:500] or "<empty response body>"


def assert_booking_rejected(response: requests.Response, scenario: str) -> None:
    assert response.status_code == 400, (
        f"{scenario} should be rejected with HTTP 400, but the API returned "
        f"HTTP {response.status_code}. Response: {response_summary(response)}"
    )


def test_valid_booking_is_created() -> None:
    checkin = date.today() + timedelta(days=30)
    payload = booking_payload(
        checkin=checkin.isoformat(),
        checkout=(checkin + timedelta(days=3)).isoformat(),
    )

    response = create_booking(payload)

    assert response.status_code == 200, (
        "A valid booking should be created with HTTP 200, but the API returned "
        f"HTTP {response.status_code}. Response: {response_summary(response)}"
    )
    try:
        response_body = response.json()
    except ValueError:
        pytest.fail(
            "A successful booking response should contain JSON, but the API returned: "
            f"{response_summary(response)}",
            pytrace=False,
        )

    assert isinstance(response_body, dict), (
        "A successful booking response should be a JSON object. "
        f"Response: {response_body}"
    )
    assert isinstance(response_body.get("bookingid"), int), (
        "A successful booking response should include a numeric 'bookingid'. "
        f"Response: {response_body}"
    )
    assert response_body.get("booking") == payload, (
        "The API created a booking, but the stored values did not match the request. "
        f"Expected: {payload}. Actual: {response_body.get('booking')}"
    )


def test_checkout_before_checkin_is_rejected() -> None:
    checkin = date.today() + timedelta(days=30)
    payload = booking_payload(
        checkin=checkin.isoformat(),
        checkout=(checkin - timedelta(days=1)).isoformat(),
    )

    response = create_booking(payload)

    assert_booking_rejected(response, "A checkout date before the check-in date")


def test_same_day_checkin_and_checkout_are_rejected() -> None:
    same_day = (date.today() + timedelta(days=30)).isoformat()
    payload = booking_payload(checkin=same_day, checkout=same_day)

    response = create_booking(payload)

    assert_booking_rejected(
        response, "A same-day check-in and checkout (a zero-night stay)"
    )


def test_impossible_calendar_date_is_rejected() -> None:
    future_year = date.today().year + 1
    impossible_date = f"{future_year}-02-30"
    payload = booking_payload(
        checkin=impossible_date,
        checkout=f"{future_year}-03-03",
    )

    response = create_booking(payload)

    assert_booking_rejected(
        response, f"An impossible calendar date ({impossible_date})"
    )


def test_non_date_strings_are_rejected() -> None:
    payload = booking_payload(checkin="not-a-date", checkout="also-not-a-date")

    response = create_booking(payload)

    assert_booking_rejected(response, "Non-date strings in the booking date fields")


def test_missing_checkin_is_rejected() -> None:
    checkin = date.today() + timedelta(days=30)
    payload = booking_payload(
        checkin=checkin.isoformat(),
        checkout=(checkin + timedelta(days=3)).isoformat(),
    )
    del payload["bookingdates"]["checkin"]

    response = create_booking(payload)

    assert_booking_rejected(response, "A booking with no check-in date")


def test_missing_checkout_is_rejected() -> None:
    checkin = date.today() + timedelta(days=30)
    payload = booking_payload(
        checkin=checkin.isoformat(),
        checkout=(checkin + timedelta(days=3)).isoformat(),
    )
    del payload["bookingdates"]["checkout"]

    response = create_booking(payload)

    assert_booking_rejected(response, "A booking with no checkout date")
