# Deployment: Raspberry Pi Auto-Update

This guide explains how to set up the Daily Audio Update to run automatically every day on your Raspberry Pi.

## Prerequisites

1.  **Clone the Repository**: Ensure the repository is cloned to your Pi.
    ```bash
    git clone https://github.com/deankiwi/daily-audio-update.git
    cd daily-audio-update
    ```
2.  **Environment Setup**: Ensure `.env` and Google credentials (`credentials.json`, `token.json`) are present in the project root.
3.  **Install `uv`**: Ensure `uv` is installed on your Pi.
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

## Setup Auto-Update Script

We've provided a script at `scripts/update_and_run.sh` that handles updating the code and running the application.

1.  **Make it Executable**:
    ```bash
    chmod +x scripts/update_and_run.sh
    ```

## Configure Cron Job

We use `cron` to schedule the script to run daily.

1.  **Open Crontab**:
    ```bash
    crontab -e
    ```

2.  **Add the Schedule**:
    Add the following line to the bottom of the file to run the script every day at 6:00 AM.
    *Replace `/home/pi/daily-audio-update` with the actual path to your repository.*

    ```cron
    0 6 * * * /home/pi/daily-audio-update/scripts/update_and_run.sh >> /home/pi/daily-audio-update/cron.log 2>&1
    ```

    **Explanation:**
    *   `0 6 * * *`: Run at 06:00 AM every day.
    *   `/path/to/script`: The full path to the update script.
    *   `>> .../cron.log 2>&1`: Redirects both standard output and error output to a log file for debugging.

3.  **Save and Exit**: The cron service will automatically pick up the changes.

## Verification

To verify it works immediately:

1.  Run the script manually:
    ```bash
    ./scripts/update_and_run.sh
    ```
2.  Check `cron.log` for output.
