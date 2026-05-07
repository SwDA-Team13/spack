# Overview Methodology

This file records how the final Markdown report's statistics were collected.

## Commands and Collection Method

Repository and commit:

```bash
git rev-parse --show-toplevel
git rev-parse --short HEAD
```

Architecture inspection used directory and file listing commands such as:

```bash
find lib/spack/spack -maxdepth 2 -type d | sort
find var/spack -maxdepth 5 -type d | sort
git ls-files 'etc/spack/defaults/**' '.github/workflows/**' '.ci/**'
sed -n '1,180p' bin/spack
sed -n '1,220p' lib/spack/spack/main.py
sed -n '1,180p' lib/spack/spack/package_base.py
sed -n '1,180p' lib/spack/spack/solver/asp.py
sed -n '1,180p' lib/spack/spack/environment/environment.py
sed -n '1,200p' lib/spack/spack/repo.py
sed -n '1,180p' lib/spack/spack/config.py
```

The statistics were computed with this Python script over `git ls-files` output:

```python
import re
import subprocess
from pathlib import Path

tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
exclude_prefixes = (
    "lib/spack/spack/vendor/",
    "lib/spack/_vendoring/",
    "var/spack/vendoring/",
)
exclude_parts = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".venv", "venv", "node_modules", "build", "dist",
}

files = []
for path in tracked:
    if path.startswith(exclude_prefixes):
        continue
    if set(Path(path).parts) & exclude_parts:
        continue
    files.append(path)

def text_line_count(paths):
    lines = counted = binary = nonregular = 0
    for path_text in paths:
        path = Path(path_text)
        if not path.is_file():
            nonregular += 1
            continue
        data = path.read_bytes()
        if b"\0" in data[:4096]:
            binary += 1
            continue
        lines += data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
        counted += 1
    return lines, counted, binary, nonregular

py_files = [p for p in files if p.endswith(".py")]
recipe_files = [p for p in files if re.search(r"(^|/)packages/[^/]+/package\.py$", p)]
test_py = [
    p for p in files
    if p.endswith(".py") and re.search(r"(^|/)tests?/|^lib/spack/spack/test/", p)
]
test_dirs = {
    str(Path(p).parent)
    for p in files
    if re.search(r"(^|/)tests?/|^lib/spack/spack/test/", p)
}

base = Path("lib/spack/spack")
top = []
for child in base.iterdir():
    if child.is_file() and child.suffix == ".py":
        top.append(str(child))
    elif child.is_dir() and (child / "__init__.py").exists():
        top.append(str(child))
core_top = [p for p in top if not p.endswith("/test") and not p.endswith("/vendor")]

print("total_files_analyzed", len(files))
print("total_text_lines", text_line_count(files))
print("python_files", len(py_files))
print("python_text_lines", text_line_count(py_files))
print("recipe_files", len(recipe_files))
print("test_python_files", len(test_py))
print("test_directories", len(test_dirs))
print("top_level_all", len(top))
print("top_level_core_excluding_test_vendor", len(core_top))
```

Contributor identities were counted from Git history:

```bash
git shortlog -sne HEAD | wc -l
```

Assumptions: `git ls-files` excludes `.git` and untracked build/cache artifacts. The script also excludes vendored dependency directories and common generated/cache/virtual-environment names. The total line metric counts text lines in the analyzed tracked files as a practical LOC proxy; binary and non-regular entries are excluded from the line total. Contributor identities are not normalized across multiple email addresses.
