# Restful Booker date-validation tests

This small pytest project protects the booking-date rules in the
[Restful Booker API](https://restful-booker.herokuapp.com). It was built to
catch regressions that could allow invalid stays into downstream systems, where
they can appear as wrong arrival dates, zero or negative night counts, or
bookings that staff must repair manually.

Every test creates and sends its own uniquely named booking payload. The suite
does not rely on the API's preloaded records, which is important because the
public environment resets regularly and may sleep when idle.

## What is covered

- A valid booking is accepted and returned unchanged.
- Checkout before check-in is rejected.
- Same-day check-in and checkout (a zero-night stay) is rejected.
- An impossible calendar date is rejected.
- Non-date strings are rejected.
- A missing check-in date is rejected.
- A missing checkout date is rejected.

The validation contract used here is simple: a valid create request returns
HTTP 200, while invalid booking dates return HTTP 400. Assertion messages show
the scenario, actual status, and a short response body so a failure is useful
without extra debugging.

## Requirements

- Python 3.9 or newer
- Internet access to `https://restful-booker.herokuapp.com`

## Install

From the project directory, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run

Run the complete suite with verbose test names:

```bash
pytest -v
```

The public API can be slow on its first request after sleeping. Each request
allows up to 30 seconds and reports a clear connectivity failure if the service
cannot be reached.

To run the same checks against another deployment, set its base URL first:

```bash
RESTFUL_BOOKER_BASE_URL=https://example.test pytest -v
```

PowerShell equivalent:

```powershell
$env:RESTFUL_BOOKER_BASE_URL = "https://example.test"
pytest -v
```

## Interpreting failures

A failed negative test means the API did not reject that invalid payload with
HTTP 400. For example, HTTP 200 means the bad booking was created, while HTTP
500 means invalid client input reached an unhandled server error. Both results
are date-validation regressions worth investigating.
