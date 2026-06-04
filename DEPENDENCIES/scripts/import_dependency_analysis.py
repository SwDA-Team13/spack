#!/usr/bin/env python3
"""Build a local import-dependency graph for the Spack source code."""

import argparse
import ast
import collections
import csv
import json
import subprocess
from pathlib import Path


INCLUDED_FILES = {"bin/spack"}
INCLUDED_PREFIXES = ("lib/spack/spack/", "lib/spack/llnl/")

EXCLUDED_PREFIXES = (
    "lib/spack/spack/vendor/",
    "lib/spack/_vendoring/",
    "var/spack/vendoring/",
    "lib/spack/spack/test/",
    "var/spack/test_repos/",
)
EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "node_modules",
    "build",
    "dist",
}
EXCLUDED_MODULE_PREFIXES = ("spack.vendor",)


def tracked_files(repo_root):
    """Return files tracked by Git, using paths relative to repo_root."""
    output = subprocess.check_output(["git", "ls-files"], cwd=repo_root, text=True)
    return output.splitlines()


def is_in_scope(path_text):
    """Return True if a tracked file belongs to the selected analysis scope."""
    path = Path(path_text)

    if path_text in INCLUDED_FILES:
        return True

    if path.suffix != ".py":
        return False

    if not path_text.startswith(INCLUDED_PREFIXES):
        return False

    if path_text.startswith(EXCLUDED_PREFIXES):
        return False

    if set(path.parts) & EXCLUDED_PARTS:
        return False

    return True


def module_name_for(path_text):
    """Map a repository path to the Python module name it defines."""
    path = Path(path_text)

    if path_text == "bin/spack":
        return "bin.spack", False

    if path_text.startswith("lib/spack/spack/"):
        relative_path = path.relative_to("lib/spack/spack")
        root_module = "spack"
    elif path_text.startswith("lib/spack/llnl/"):
        relative_path = path.relative_to("lib/spack/llnl")
        root_module = "llnl"
    else:
        return None, False

    parts = list(relative_path.parts)
    is_package = parts[-1] == "__init__.py"

    if is_package:
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem

    module = ".".join([root_module] + parts) if parts else root_module
    return module, is_package


def resolve_absolute(module_name, module_to_file):
    """Resolve an absolute import such as ``spack.config`` to a local file."""
    if not module_name:
        return None

    if module_name.startswith(EXCLUDED_MODULE_PREFIXES):
        return None

    return module_to_file.get(module_name)


def resolve_import_from(node, current_module, current_is_package, module_to_file):
    """Resolve a ``from ... import ...`` statement to local files."""
    targets = set()

    if node.level:
        parts = current_module.split(".")
        if not current_is_package:
            parts = parts[:-1]

        keep = max(0, len(parts) - node.level + 1)
        base_parts = parts[:keep]
        if node.module:
            base_parts.extend(node.module.split("."))
        base_module = ".".join(base_parts)
    else:
        base_module = node.module or ""

    if base_module.startswith(EXCLUDED_MODULE_PREFIXES):
        return targets

    for alias in node.names:
        candidate = f"{base_module}.{alias.name}" if base_module else alias.name
        candidate_file = resolve_absolute(candidate, module_to_file)
        if candidate_file:
            targets.add(candidate_file)
            continue

        base_file = resolve_absolute(base_module, module_to_file)
        if base_file:
            targets.add(base_file)

    return targets


def analyze_imports(repo_root):
    """Parse source files and return outgoing and incoming import edges."""
    source_files = sorted(path for path in tracked_files(repo_root) if is_in_scope(path))

    module_to_file = {}
    file_to_module = {}
    file_is_package = {}

    for path_text in source_files:
        module_name, is_package = module_name_for(path_text)
        if not module_name:
            continue
        module_to_file[module_name] = path_text
        file_to_module[path_text] = module_name
        file_is_package[path_text] = is_package

    outgoing = collections.defaultdict(set)
    parse_errors = []

    for path_text in source_files:
        source_path = repo_root / path_text
        try:
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=path_text)
        except Exception as exc:
            parse_errors.append({"file": path_text, "error": str(exc)})
            continue

        current_module = file_to_module[path_text]
        current_is_package = file_is_package[path_text]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = resolve_absolute(alias.name, module_to_file)
                    if target and target != path_text:
                        outgoing[path_text].add(target)

            elif isinstance(node, ast.ImportFrom):
                targets = resolve_import_from(
                    node, current_module, current_is_package, module_to_file
                )
                for target in targets:
                    if target != path_text:
                        outgoing[path_text].add(target)

    incoming = collections.defaultdict(set)
    for source, targets in outgoing.items():
        for target in targets:
            incoming[target].add(source)

    return {
        "files": source_files,
        "outgoing": outgoing,
        "incoming": incoming,
        "parse_errors": parse_errors,
    }


def sorted_by_dependency_count(files, dependency_map, limit):
    """Sort files by descending dependency count, then by path."""
    rows = [(path, len(dependency_map.get(path, set()))) for path in files]
    return sorted(rows, key=lambda row: (-row[1], row[0]))[:limit]


def low_dependency_rows(files, outgoing, incoming, limit):
    """Return examples with the smallest number of local dependencies."""
    rows = []
    for path in files:
        out_count = len(outgoing.get(path, set()))
        in_count = len(incoming.get(path, set()))
        rows.append((path, out_count, in_count, out_count + in_count))
    return sorted(rows, key=lambda row: (row[3], row[1], row[2], row[0]))[:limit]


def write_edges_csv(output_path, outgoing):
    """Write one row per direct import edge."""
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["source", "target"])
        for source in sorted(outgoing):
            for target in sorted(outgoing[source]):
                writer.writerow([source, target])


def write_count_csv(output_path, rows, headers):
    """Write a small CSV table."""
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def write_summary_json(output_path, result, top_outgoing, top_incoming, low_rows):
    """Write the main counts and selected result tables as JSON."""
    files = result["files"]
    outgoing = result["outgoing"]
    incoming = result["incoming"]
    total_edges = sum(len(targets) for targets in outgoing.values())

    summary = {
        "scope": {
            "included_files": sorted(INCLUDED_FILES),
            "included_prefixes": INCLUDED_PREFIXES,
            "excluded_prefixes": EXCLUDED_PREFIXES,
            "excluded_parts": sorted(EXCLUDED_PARTS),
        },
        "counts": {
            "files_analyzed": len(files),
            "local_import_edges": total_edges,
            "files_with_zero_outgoing": sum(1 for path in files if not outgoing.get(path)),
            "files_with_zero_incoming": sum(1 for path in files if not incoming.get(path)),
        },
        "top_outgoing": [{"file": path, "local_imports": count} for path, count in top_outgoing],
        "top_incoming": [{"file": path, "imported_by": count} for path, count in top_incoming],
        "low_dependency_examples": [
            {
                "file": path,
                "outgoing": outgoing_count,
                "incoming": incoming_count,
                "total": total,
            }
            for path, outgoing_count, incoming_count, total in low_rows
        ],
        "parse_errors": result["parse_errors"],
    }

    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def write_markdown_summary(output_path, result, top_outgoing, top_incoming, low_rows):
    """Write a compact Markdown summary of the generated results."""
    files = result["files"]
    outgoing = result["outgoing"]
    incoming = result["incoming"]
    total_edges = sum(len(targets) for targets in outgoing.values())

    lines = [
        "# Import Dependency Analysis Summary",
        "",
        "## Scope",
        "",
        "- Included: `bin/spack`, `lib/spack/spack`, `lib/spack/llnl`.",
        "- Excluded: vendored code, tests, mock repositories, caches, virtual environments, and generated/build folders.",
        "",
        "## Counts",
        "",
        f"- Files analyzed: {len(files)}",
        f"- Local import edges: {total_edges}",
        f"- Files with zero outgoing local imports: {sum(1 for path in files if not outgoing.get(path))}",
        f"- Files with zero incoming local imports: {sum(1 for path in files if not incoming.get(path))}",
        "",
        "## Top Outgoing Dependencies",
        "",
        "| File | Local imports |",
        "|---|---:|",
    ]

    for path, count in top_outgoing:
        lines.append(f"| `{path}` | {count} |")

    lines.extend(["", "## Top Incoming Dependencies", "", "| File | Imported by local files |", "|---|---:|"])
    for path, count in top_incoming:
        lines.append(f"| `{path}` | {count} |")

    lines.extend(
        [
            "",
            "## Lowest Total Dependency Examples",
            "",
            "| File | Outgoing | Incoming | Total |",
            "|---|---:|---:|---:|",
        ]
    )
    for path, outgoing_count, incoming_count, total in low_rows:
        lines.append(f"| `{path}` | {outgoing_count} | {incoming_count} | {total} |")

    if result["parse_errors"]:
        lines.extend(["", "## Parse Errors", ""])
        for error in result["parse_errors"]:
            lines.append(f"- `{error['file']}`: {error['error']}")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default="/home/noralea/Desktop/spack",
        help="Path to the Spack repository",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/noralea/Desktop/UNI/SDA/Project workflow/CodeDependecyAnalysis/data",
        help="Directory where analysis outputs will be written",
    )
    parser.add_argument("--limit", type=int, default=15, help="Rows for each result table")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    result = analyze_imports(repo_root)
    top_outgoing = sorted_by_dependency_count(
        result["files"], result["outgoing"], args.limit
    )
    top_incoming = sorted_by_dependency_count(
        result["files"], result["incoming"], args.limit
    )
    low_rows = low_dependency_rows(
        result["files"], result["outgoing"], result["incoming"], args.limit
    )

    write_edges_csv(output_dir / "import_edges.csv", result["outgoing"])
    write_count_csv(
        output_dir / "top_outgoing_imports.csv",
        top_outgoing,
        ["file", "local_imports"],
    )
    write_count_csv(
        output_dir / "top_incoming_imports.csv",
        top_incoming,
        ["file", "imported_by_local_files"],
    )
    write_count_csv(
        output_dir / "low_dependency_examples.csv",
        low_rows,
        ["file", "outgoing_local_imports", "incoming_local_imports", "total"],
    )
    write_summary_json(
        output_dir / "import_dependency_summary.json",
        result,
        top_outgoing,
        top_incoming,
        low_rows,
    )
    write_markdown_summary(
        output_dir / "import_dependency_summary.md",
        result,
        top_outgoing,
        top_incoming,
        low_rows,
    )

    print(f"Wrote import dependency outputs to {output_dir}")


if __name__ == "__main__":
    main()
