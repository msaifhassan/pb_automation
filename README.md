# pb_automation
Reserve pickleball when it opens up

## Goal
Build automated steps to reserve a court at centrecourt.clubautomation.com using Playwright (Python async).

## Setup (recommended: uv)

This project uses `uv` as the Python package/project manager. If you don't have `uv`, you can use pip or pipx.

1. Install uv (if not already installed):

	For Windows PowerShell:

	```powershell
	python -m pip install --user uv
	```

2. Create a virtual environment and install dependencies with uv:

	```powershell
	uv install
	```

	Alternatively, to install packages manually with pip:

	```powershell
	python -m pip install playwright python-dotenv
	python -m playwright install
	```

3. Copy `.env.example` to `.env` and fill in your `USERNAME` and `PASSWORD`.

4. Run the script using uv's script entry (recommended):

	```powershell
	uv run run
	```

	Or run the script directly with Python:

	```powershell
	python scripts\run.py
	```

Note: Playwright will prompt during `playwright install` to download browser binaries. If you used `uv install`, run `python -m playwright install` afterwards.

## What we added

- `pyproject.toml` - configuration for uv and dependencies
- `.env.example` - example environment file
- `src/pb_automation/auto.py` - async Playwright login implementation
- `scripts/run.py` - simple runner for the login flow

## Next steps

After you provide credentials (or put them into `.env`) we'll iterate on the booking flow: selecting date/time, court type, and confirming reservations. The code is modular so we'll add `navigate_to_booking_page()` and other helpers next.
