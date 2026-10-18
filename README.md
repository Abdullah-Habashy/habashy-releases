# habashy-releases

Update feed for my Windows desktop tools.

This repository holds **no source code**. It has one small JSON file per
app under `apps/`, and the built executables as release assets. Programs
read their JSON file over plain HTTPS, compare versions, download the
files listed there and verify each one against its SHA-256 before
replacing anything.

It is public so the apps can update themselves without carrying a token.

## Feed format

`apps/<app-id>.json`

```json
{
  "name": "App Timer",
  "version": "1.0.0",
  "released": "2026-10-18",
  "notes": "What changed, in one or two lines.",
  "files": [
    {
      "target": "AppTimer.exe",
      "url": "https://github.com/Abdullah-Habashy/habashy-releases/releases/download/app-timer-v1.0.0/AppTimer.exe",
      "sha256": "…",
      "size": 19916701
    }
  ]
}
```

| Field | Meaning |
|---|---|
| `version` | Compared number by number against what the app is running |
| `files[].target` | File name to replace inside the app's folder |
| `files[].url` | Where to download it, a release asset of this repository |
| `files[].sha256` | Checked before the file is used; a mismatch cancels the update |
| `files[].size` | Checked too, as a cheap first guard |

## Apps

| App | Feed |
|---|---|
| App Timer | [`apps/app-timer.json`](apps/app-timer.json) |

## Publishing a new version

From the app's own (private) repository, after building:

```
python E:\HABASHY\Python Codes\_shared\habashy-releases\publish.py ^
    --app app-timer --version 1.1.0 --notes "..." ^
    dist\AppTimer.exe dist\AppTimerGuard.exe
```

The script uploads the files as a release here, writes the checksums into
the feed, and pushes. The apps pick it up on their next check.
