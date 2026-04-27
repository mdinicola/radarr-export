#!/usr/bin/env python3
"""Export downloaded Radarr movies to CSV or JSON."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


FIELDNAMES = [
    "radarr_link",
    "title",
    "genre",
    "quality",
    "resolution",
    "format",
    "videoDynamicRangeType",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export downloaded Radarr movies to CSV or JSON."
    )
    parser.add_argument(
        "--radarr-url",
        required=True,
        help="Base URL of the Radarr instance, for example http://localhost:7878",
    )
    parser.add_argument(
        "--export-format",
        required=True,
        choices=("csv", "json"),
        help="Output format.",
    )
    parser.add_argument(
        "--export-filename",
        required=True,
        help="Absolute or relative path to write the export file.",
    )
    parser.add_argument(
        "--api-key",
        help=(
            "Radarr API key. Not recommended because command-line arguments can "
            "be visible to other processes; prefer an environment variable."
        ),
    )
    parser.add_argument(
        "--api-key-env-var",
        default="RADARR_API_KEY",
        help=(
            "Name of the environment variable containing the Radarr API key. "
            "Defaults to RADARR_API_KEY."
        ),
    )
    return parser.parse_args()


def normalize_base_url(radarr_url: str) -> str:
    return radarr_url.rstrip("/") + "/"


def fetch_movies(radarr_url: str, api_key: str) -> list[dict[str, Any]]:
    api_url = urljoin(normalize_base_url(radarr_url), "api/v3/movie")
    request = Request(api_url, headers={"X-Api-Key": api_key, "Accept": "application/json"})

    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"Radarr API returned HTTP {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to connect to Radarr: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Timed out while connecting to Radarr") from exc

    try:
        movies = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Radarr returned invalid JSON") from exc

    if not isinstance(movies, list):
        raise RuntimeError("Radarr movie API returned an unexpected response")

    return movies


def resolve_api_key(args: argparse.Namespace) -> str | None:
    if args.api_key:
        return args.api_key

    return os.environ.get(args.api_key_env_var)


def is_downloaded(movie: dict[str, Any]) -> bool:
    movie_file = movie.get("movieFile")
    movie_file_id = movie.get("movieFileId")
    return bool(movie_file) or bool(movie_file_id)


def get_nested(data: dict[str, Any], path: list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_resolution(movie_file: dict[str, Any]) -> str:
    resolution = get_nested(movie_file, ["quality", "quality", "resolution"])
    if resolution:
        return str(resolution)

    quality_name = get_nested(movie_file, ["quality", "quality", "name"])
    if isinstance(quality_name, str):
        for token in ("2160p", "1080p", "720p", "576p", "480p"):
            if token in quality_name:
                return token

    return ""


def extract_format(movie_file: dict[str, Any]) -> str:
    custom_formats = movie_file.get("customFormats")
    if isinstance(custom_formats, list) and custom_formats:
        names = [
            item.get("name")
            for item in custom_formats
            if isinstance(item, dict) and item.get("name")
        ]
        if names:
            return ", ".join(str(name) for name in names)

    media_info = movie_file.get("mediaInfo")
    if isinstance(media_info, dict):
        video_codec = media_info.get("videoCodec")
        if video_codec:
            return str(video_codec)

    release_group = movie_file.get("releaseGroup")
    if release_group:
        return str(release_group)

    return ""


def extract_video_dynamic_range_type(movie_file: dict[str, Any]) -> str:
    video_dynamic_range_type = get_nested(
        movie_file, ["mediaInfo", "videoDynamicRangeType"]
    )
    return str(video_dynamic_range_type or "")


def movie_link(radarr_url: str, movie: dict[str, Any]) -> str:
    slug = movie.get("titleSlug")
    if slug:
        return urljoin(normalize_base_url(radarr_url), f"movie/{slug}")

    movie_id = movie.get("id")
    if movie_id:
        return urljoin(normalize_base_url(radarr_url), f"movie/{movie_id}")

    return normalize_base_url(radarr_url).rstrip("/")


def export_row(radarr_url: str, movie: dict[str, Any]) -> dict[str, str]:
    movie_file = movie.get("movieFile")
    if not isinstance(movie_file, dict):
        movie_file = {}

    genres = movie.get("genres")
    genre = ", ".join(str(item) for item in genres) if isinstance(genres, list) else ""

    quality = get_nested(movie_file, ["quality", "quality", "name"])

    return {
        "radarr_link": movie_link(radarr_url, movie),
        "title": str(movie.get("title") or ""),
        "genre": genre,
        "quality": str(quality or ""),
        "resolution": extract_resolution(movie_file),
        "format": extract_format(movie_file),
        "videoDynamicRangeType": extract_video_dynamic_range_type(movie_file),
    }


def write_csv(filename: Path, rows: list[dict[str, str]]) -> None:
    with filename.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_json(filename: Path, rows: list[dict[str, str]]) -> None:
    with filename.open("w", encoding="utf-8") as output:
        json.dump(rows, output, indent=2)
        output.write("\n")


def main() -> int:
    args = parse_args()
    api_key = resolve_api_key(args)
    if not api_key:
        print(
            f"Error: Radarr API key not provided. Set {args.api_key_env_var} "
            "or pass --api-key.",
            file=sys.stderr,
        )
        return 1

    try:
        movies = fetch_movies(args.radarr_url, api_key)
        rows = [export_row(args.radarr_url, movie) for movie in movies if is_downloaded(movie)]

        output_path = Path(args.export_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.export_format == "csv":
            write_csv(output_path, rows)
        else:
            write_json(output_path, rows)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Error writing export file: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(rows)} downloaded movie(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
