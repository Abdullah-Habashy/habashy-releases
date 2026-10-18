"""Publish a new version of an app to the update feed.

    python publish.py --app app-timer --version 1.1.0 \
        --notes "What changed" dist\\AppTimer.exe dist\\AppTimerGuard.exe

Uploads the files as a GitHub release of this repository, writes their
checksums into apps/<app>.json, commits and pushes. Needs the gh CLI,
already signed in.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
OWNER = "Abdullah-Habashy"
REPO = "habashy-releases"
ASSET_URL = "https://github.com/{owner}/{repo}/releases/download/{tag}/{name}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("   $", " ".join(args))
    result = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
    if result.stdout.strip():
        print("    ", result.stdout.strip()[:400])
    if check and result.returncode != 0:
        print("    FAILED:", result.stderr.strip()[:600])
        sys.exit(1)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish an app update")
    parser.add_argument("--app", required=True, help="app id, e.g. app-timer")
    parser.add_argument("--version", required=True)
    parser.add_argument("--name", default="", help="display name, first time only")
    parser.add_argument("--notes", default="")
    parser.add_argument("files", nargs="+", help="built files to upload")
    args = parser.parse_args()

    paths = [Path(f).resolve() for f in args.files]
    for path in paths:
        if not path.exists():
            print(f"Missing file: {path}")
            return 1

    tag = f"{args.app}-v{args.version}"
    feed_path = HERE / "apps" / f"{args.app}.json"
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    previous = {}
    if feed_path.exists():
        previous = json.loads(feed_path.read_text(encoding="utf-8"))

    print(f"Publishing {args.app} {args.version}")
    print("1. creating the release")
    existing = run(["gh", "release", "view", tag, "--repo", f"{OWNER}/{REPO}"], check=False)
    if existing.returncode != 0:
        run(["gh", "release", "create", tag,
             "--repo", f"{OWNER}/{REPO}",
             "--title", f"{args.name or previous.get('name') or args.app} {args.version}",
             "--notes", args.notes or f"{args.app} {args.version}"])

    print("2. uploading the files")
    run(["gh", "release", "upload", tag, *[str(p) for p in paths],
         "--repo", f"{OWNER}/{REPO}", "--clobber"])

    print("3. writing the feed")
    feed = {
        "name": args.name or previous.get("name") or args.app,
        "version": args.version,
        "released": date.today().isoformat(),
        "notes": args.notes or previous.get("notes", ""),
        "files": [
            {
                "target": path.name,
                "url": ASSET_URL.format(owner=OWNER, repo=REPO, tag=tag, name=path.name),
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }
            for path in paths
        ],
    }
    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    for item in feed["files"]:
        print(f"     {item['target']}  {item['size']:,} bytes  {item['sha256'][:16]}…")

    print("4. pushing the feed")
    run(["git", "add", str(feed_path.relative_to(HERE))])
    status = run(["git", "status", "--porcelain"], check=False)
    if status.stdout.strip():
        run(["git", "commit", "-m", f"{args.app}: publish {args.version}"])
        run(["git", "push"])
    else:
        print("     nothing changed in the feed")

    print()
    print(f"Done. Apps on an older version will pick up {args.version} on their next check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
