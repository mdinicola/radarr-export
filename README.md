Radarr export utilities.

## Scripts

- `scripts/radarr_export.py`
  - Exports downloaded Radarr movies to CSV or JSON.
  - Includes Radarr link, title, genre, quality, resolution, format, and video dynamic range type.
  - Requires Python 3.11+ and uses only the standard library.
  - Default API key source:

    ```powershell
    $env:RADARR_API_KEY="your-api-key"
    python scripts\radarr_export.py --radarr-url http://localhost:7878 --export-format csv --export-filename movies.csv
    ```

  - Use a different API key environment variable:

    ```powershell
    $env:MY_RADARR_KEY="your-api-key"
    python scripts\radarr_export.py --radarr-url http://localhost:7878 --export-format json --export-filename movies.json --api-key-env-var MY_RADARR_KEY
    ```

  - Pass the API key directly, not recommended because command-line arguments can be visible to other processes:

    ```powershell
    python scripts\radarr_export.py --radarr-url http://localhost:7878 --export-format csv --export-filename movies.csv --api-key your-api-key
    ```
