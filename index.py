import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== CONFIG =====
ROOT_DIR = "bank-statement/"   # change if needed
OLD = b"bank-bank-statement.html"
NEW = b"business-bank-statement.html"
EXTENSIONS = {".html"}                             # limit to these extensions
MAX_WORKERS = min(64, (os.cpu_count() or 4) * 8)   # IO-bound: more threads is fine
DRY_RUN = False                                    # True => don't write, just report

def should_edit(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in EXTENSIONS)

def process_file(path: str) -> tuple[int, int]:
    # returns (files_changed(0/1), occurrences_replaced)
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception:
        return (0, 0)

    # quick skip
    cnt = data.count(OLD)
    if cnt == 0:
        return (0, 0)

    new_data = data.replace(OLD, NEW)
    if not DRY_RUN:
        tmp_path = path + ".tmp___"
        try:
            with open(tmp_path, "wb") as f:
                f.write(new_data)
            # atomic on most OSes
            os.replace(tmp_path, path)
        except Exception:
            # cleanup on failure
            try: os.remove(tmp_path)
            except Exception: pass
            raise
    return (1, cnt)

def iter_files(root: str):
    for subdir, _, files in os.walk(root):
        for name in files:
            if should_edit(name):
                yield os.path.join(subdir, name)

def main():
    paths = list(iter_files(ROOT_DIR))
    if not paths:
        print("No matching files found.")
        return

    files_changed = 0
    total_replacements = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(process_file, p): p for p in paths}
        for fut in as_completed(futures):
            try:
                changed, cnt = fut.result()
                files_changed += changed
                total_replacements += cnt
            except Exception as e:
                print(f"⚠️ Error: {futures[fut]} -> {e}")

    action = "Scanned"
    print(f"✅ {action} {len(paths)} files. "
          f"Replaced {total_replacements} occurrence(s) in {files_changed} file(s). "
          f"{'(dry run)' if DRY_RUN else ''}")

if __name__ == "__main__":
    main()
