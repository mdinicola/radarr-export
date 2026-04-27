Goal:
- Provide a Python script named `radarr_export.py` in the `scripts` folder.
- Export a list of all downloaded movies from Radarr to either a CSV or JSON file.
- Only downloaded movies are included.
- The script should use only the Python standard library.

Language:
- Python 3.11+

Radarr API:
- Use the Radarr v3 API endpoint `GET /api/v3/movie`.
- Send the API key using the `X-Api-Key` request header.
- Send `Accept: application/json`.
- Treat the response as invalid if it is not a JSON array.
- A movie is considered downloaded when either `movieFile` or `movieFileId` is present.

Script Parameters:
- `--radarr-url`
    - Required.
    - Base URL of the Radarr instance.
    - Example: `http://localhost:7878`.
- `--export-format`
    - Required.
    - Must be either `csv` or `json`.
- `--export-filename`
    - Required.
    - Path for the script to write data to.
    - Path can be absolute or relative to the user's current directory.
    - Parent directories should be created when needed.
- `--api-key`
    - Optional.
    - Allows the Radarr API key to be passed directly.
    - This is not recommended because command-line arguments can be visible to other processes.
    - If provided, this value takes precedence over any environment variable.
- `--api-key-env-var`
    - Optional.
    - Name of the environment variable containing the Radarr API key.
    - Defaults to `RADARR_API_KEY`.

Authentication:
- API key lookup order:
    1. Use `--api-key` if provided.
    2. Otherwise, read from the environment variable named by `--api-key-env-var`.
    3. By default, read from `RADARR_API_KEY`.
- If no API key is available, print a clear error message and exit with a non-zero status.

Export Fields:
- `radarr_link`
    - Link to the Radarr movie page.
    - Prefer `<radarr-url>/movie/<titleSlug>` when `titleSlug` exists.
    - Fall back to `<radarr-url>/movie/<id>` when `id` exists.
- `title`
    - From movie `title`.
- `description`
    - From movie `overview`.
    - Empty string when unavailable.
- `genre`
    - From movie `genres`.
    - Join multiple genres with `, `.
- `quality`
    - From `movieFile.quality.quality.name`.
    - Empty string when unavailable.
- `resolution`
    - Prefer `movieFile.quality.quality.resolution`.
    - If unavailable, infer from the quality name when it contains one of `2160p`, `1080p`, `720p`, `576p`, or `480p`.
    - Empty string when unavailable.
- `format`
    - Prefer names from `movieFile.customFormats`, joined with `, `.
    - If unavailable, fall back to `movieFile.mediaInfo.videoCodec`.
    - If unavailable, fall back to `movieFile.releaseGroup`.
    - Empty string when unavailable.
- `videoDynamicRangeType`
    - From `movieFile.mediaInfo.videoDynamicRangeType`.
    - Empty string when unavailable.

Output:
- Write a CSV or JSON file depending on `--export-format`.
- CSV output must include a header row.
- JSON output must be an array of objects.
- Use this field order for CSV headers and JSON object keys:
    1. `radarr_link`
    2. `title`
    3. `description`
    4. `genre`
    5. `quality`
    6. `resolution`
    7. `format`
    8. `videoDynamicRangeType`

Error Handling:
- Print clear errors to stderr.
- Exit with a non-zero status for missing API key, Radarr connection errors, HTTP errors, invalid JSON, unexpected API response shape, and output file write errors.
