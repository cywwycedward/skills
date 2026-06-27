import json
import subprocess
import sys
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent
RUNFILE_PATH = SKILL_PATH / "state" / "runs"


def parse_feed_ids(value):
    text = value.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("feed_ids must be a JSON list") from error

    if not isinstance(parsed, list):
        raise ValueError("feed_ids must be a JSON list")

    feed_ids = [str(feed_id).strip() for feed_id in parsed if str(feed_id).strip()]
    if not feed_ids:
        raise ValueError("feed_ids must contain at least one feed id")
    return feed_ids


def parse_args(argv):
    if len(argv) != 3:
        raise SystemExit("Expected arguments: feed_ids date output")

    try:
        feed_ids = parse_feed_ids(argv[0])
    except ValueError as error:
        raise SystemExit(str(error)) from error

    output = argv[2]
    output_path = Path(output)
    if output_path.is_absolute() or output_path.name != output or output in (".", ".."):
        raise SystemExit("output must be a name, not a path")

    return {
        "feed_ids": feed_ids,
        "date": argv[1],
        "output": output,
    }


def run_zotero(args):
    completed = subprocess.run(
        ["zotero-cli", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"Failed to parse zotero-cli JSON output: {error}\n{completed.stderr}"
        ) from error


def ensure_ok(payload, fallback_message):
    if payload and payload.get("ok"):
        return payload
    error = payload.get("error") if isinstance(payload, dict) else None
    message = error.get("message") if isinstance(error, dict) else None
    raise RuntimeError(message or fallback_message)


def collect_feed_items(feed_ids, date_filter, output, run_zotero=run_zotero):
    output_dir = RUNFILE_PATH / output
    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(f"output must be a directory path: {output_dir}")
    output_path = output_dir / "process-items.json"

    for feed_id in feed_ids:
        payload = run_zotero(["--json", "feeds", "show", feed_id])
        ensure_ok(payload, f"Feed {feed_id} validation failed")

    items_by_doi = {}
    skipped_without_doi = 0

    for feed_id in feed_ids:
        payload = run_zotero(["--json", "feeds", "items", feed_id, "--date", date_filter])
        ensure_ok(payload, f"Failed to list feed {feed_id} items")

        for item in payload.get("data") or []:
            doi = str(item.get("DOI") or item.get("doi") or "").strip()
            if not doi:
                skipped_without_doi += 1
                continue
            items_by_doi[doi] = {
                "title": str(item.get("title") or ""),
                "url": str(item.get("url") or ""),
                "filePath": "",
                "markdownPath": "",
                "reportPath": "",
                "downloadRulePath": "",
                "downloadMethod": "",
                "downloadTrigger": "",
                "downloadOriginalFilename": "",
                "status": "new",
                "zoteroItemKey": "",
                "skipReason": "",
                "failureStage": "",
                "lastError": "",
            }

    output_dir.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(items_by_doi, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return {
        "outputPath": str(output_path),
        "itemCount": len(items_by_doi),
        "skippedWithoutDoi": skipped_without_doi,
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        options = parse_args(argv)
        result = collect_feed_items(
            feed_ids=options["feed_ids"],
            date_filter=options["date"],
            output=options["output"],
        )
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, SystemExit, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
