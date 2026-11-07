"""Plan native builds for nine languages across all six GitHub-hosted target systems."""
import json
import os

LANGUAGES = ("c", "cpp", "csharp", "rust", "go", "zig", "swift", "java", "kotlin")
RUNNERS = {
    "windows-x64": "windows-2025",
    "windows-arm64": "windows-11-arm",
    "linux-x64": "ubuntu-24.04",
    "linux-arm64": "ubuntu-24.04-arm",
    "macos-x64": "macos-15-intel",
    "macos-arm64": "macos-15",
}


def plan(language="all", target="all"):
    if language != "all" and language not in LANGUAGES:
        raise ValueError(f"Unknown language: {language!r}")
    if target != "all" and target not in RUNNERS:
        raise ValueError(f"Unknown target: {target!r}")
    languages = LANGUAGES if language == "all" else (language,)
    targets = tuple(RUNNERS) if target == "all" else (target,)
    jobs = [
        {"language": lang, "target": tgt, "runner": RUNNERS[tgt]}
        for lang in languages for tgt in targets
    ]
    if not jobs:
        raise ValueError("No valid builds were requested.")
    return {"include": jobs}


if __name__ == "__main__":
    print(json.dumps(plan(
        os.environ.get("REQ_LANGUAGE", "all"),
        os.environ.get("REQ_TARGET", "all"),
    ), separators=(",", ":")))
