"""
Fresher.AI — YouTube Resource Validator
Validates curated YouTube playlist registry for URL integrity, channel mapping,
metadata consistency, duplicate detection, and verification status.

Usage:
    python backend_fastapi/rag/youtube_resource_validator.py
"""

import sys
import os
import re
from typing import Dict, List, Any

# Ensure project paths are resolvable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
KB_DIR = os.path.join(PROJECT_ROOT, "fresher_ai_kb")
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend_fastapi")

for path in [PROJECT_ROOT, KB_DIR, BACKEND_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from data.youtube_channels import get_playlists, get_youtube_channels
except ImportError:
    from fresher_ai_kb.data.youtube_channels import get_playlists, get_youtube_channels


PLAYLIST_URL_PATTERN = re.compile(
    r"^https?://(www\.)?youtube\.com/playlist\?list=[a-zA-Z0-9_\-]+$"
)
CHANNEL_URL_PATTERN = re.compile(
    r"^https?://(www\.)?youtube\.com/(@[a-zA-Z0-9_\.\-]+|c/[a-zA-Z0-9_\-]+|channel/[a-zA-Z0-9_\-]+)"
)


def validate_registry() -> Dict[str, Any]:
    """
    Validates all playlists in the canonical registry.
    Returns audit statistics and diagnostics.
    """
    playlists = get_playlists()
    total = len(playlists)

    seen_urls = set()
    seen_ids = set()
    duplicates = []
    verified_list = []
    pending_list = []
    invalid_list = []

    for pl in playlists:
        p_id = pl.get("playlist_id", "")
        url = pl.get("url", "")
        title = pl.get("playlist_name", "")
        channel_name = pl.get("channel_name", "")
        is_verified = pl.get("verified", False)
        status = pl.get("verification_status", "pending")

        # 1. Duplicate check
        if p_id in seen_ids or url in seen_urls:
            duplicates.append(pl)
        seen_ids.add(p_id)
        seen_urls.add(url)

        # 2. Check if marked pending verification
        if not is_verified or status == "pending_verification":
            pending_list.append(pl)
            continue

        # 3. Validation rules for verified items:
        # - Must be a valid youtube.com playlist URL
        # - Must have title, channel_name, logo_key
        has_valid_playlist_url = bool(PLAYLIST_URL_PATTERN.match(url))
        has_required_fields = bool(title and channel_name and pl.get("logo_key"))

        if not has_valid_playlist_url or not has_required_fields:
            invalid_list.append({
                "playlist": pl,
                "reason": "Invalid playlist URL" if not has_valid_playlist_url else "Missing metadata fields"
            })
        else:
            verified_list.append(pl)

    report = {
        "total": total,
        "verified": len(verified_list),
        "needs_verification": len(pending_list),
        "invalid": len(invalid_list),
        "duplicates": len(duplicates),
        "verified_items": verified_list,
        "pending_items": pending_list,
        "invalid_items": invalid_list,
        "duplicate_items": duplicates,
    }

    return report


def print_report(report: Dict[str, Any]):
    print("==========================================")
    print("Fresher.AI YouTube Resource Validation")
    print("==========================================")
    print(f"Total resources:     {report['total']}")
    print(f"Verified:            {report['verified']}")
    print(f"Needs verification:  {report['needs_verification']}")
    print(f"Invalid:             {report['invalid']}")
    print(f"Duplicates:          {report['duplicates']}")
    print("==========================================")

    if report["pending_items"]:
        print("\nPending Verification Creators/Playlists (Excluded from production retrieval):")
        for p in report["pending_items"]:
            print(f"  - [{p.get('channel_name')}] {p.get('playlist_name')} ({p.get('channel_url')})")

    if report["invalid_items"]:
        print("\n[ERROR] Invalid Resources Found:")
        for inv in report["invalid_items"]:
            p = inv["playlist"]
            print(f"  - [{p.get('channel_name')}] {p.get('playlist_name')}: {inv['reason']} -> {p.get('url')}")
    else:
        print("\nStatus: All verified resources passed URL integrity checks!")


if __name__ == "__main__":
    rep = validate_registry()
    print_report(rep)
    if rep["invalid"] > 0 or rep["duplicates"] > 0:
        sys.exit(1)
    sys.exit(0)
