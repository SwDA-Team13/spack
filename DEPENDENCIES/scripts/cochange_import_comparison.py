#!/usr/bin/env python3
"""Analyze Git co-change pairs and compare them with import dependencies."""

import argparse
import collections
import csv
import itertools
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


def run_git(repo_root, args):
    """Run a Git command in repo_root and return text output."""
    return subprocess.check_output(["git", *args], cwd=repo_root, text=True, errors="replace")


def tracked_files(repo_root):
    """Return current Git-tracked files in the selected source scope."""
    files = run_git(repo_root, ["ls-files"]).splitlines()
    return {path for path in files if is_in_scope(path)}


def is_in_scope(path_text):
    """Return True if a path belongs to the dependency-analysis source scope."""
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


def load_import_edges(path):
    """Load directed import edges as (source, target) tuples."""
    edges = set()
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            edges.add((row["source"], row["target"]))
    return edges


def read_commits(repo_root, valid_files, max_files_per_commit):
    """Yield selected files changed in each non-merge commit."""
    output = run_git(
        repo_root,
        ["log", "--no-merges", "--name-only", "--pretty=format:COMMIT:%H"],
    )

    current_hash = None
    current_files = set()
    commits_seen = 0
    commits_with_selected_files = 0
    commits_skipped_as_broad = 0
    selected_file_changes = 0

    def finish_commit():
        nonlocal commits_with_selected_files
        nonlocal commits_skipped_as_broad
        nonlocal selected_file_changes

        if current_hash is None:
            return None

        if not current_files:
            return None

        commits_with_selected_files += 1
        selected_file_changes += len(current_files)

        if len(current_files) > max_files_per_commit:
            commits_skipped_as_broad += 1
            return None

        return sorted(current_files)

    for line in output.splitlines():
        if line.startswith("COMMIT:"):
            finished = finish_commit()
            if finished:
                yield finished

            commits_seen += 1
            current_hash = line.removeprefix("COMMIT:")
            current_files = set()
            continue

        path = line.strip()
        if path in valid_files:
            current_files.add(path)

    finished = finish_commit()
    if finished:
        yield finished

    read_commits.stats = {
        "non_merge_commits_seen": commits_seen,
        "commits_with_selected_files": commits_with_selected_files,
        "commits_skipped_as_broad": commits_skipped_as_broad,
        "selected_file_changes_before_broad_filter": selected_file_changes,
        "max_files_per_commit": max_files_per_commit,
    }


def count_pairs(commits):
    """Count unordered file pairs changed together in the same commit."""
    pair_counts = collections.Counter()
    commits_used = 0

    for files in commits:
        commits_used += 1
        for file_a, file_b in itertools.combinations(files, 2):
            pair_counts[(file_a, file_b)] += 1

    return pair_counts, commits_used


def import_relation(file_a, file_b, import_edges):
    """Classify whether a co-change pair has a direct import relation."""
    a_to_b = (file_a, file_b) in import_edges
    b_to_a = (file_b, file_a) in import_edges

    if a_to_b and b_to_a:
        return "direct imports in both directions"
    if a_to_b:
        return "file_a imports file_b"
    if b_to_a:
        return "file_b imports file_a"
    return "no direct import"


def write_csv(path, headers, rows):
    """Write rows to a CSV file."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


def top_pair_rows(pair_counts, limit):
    """Return top co-change rows sorted by count and path."""
    rows = [(a, b, count) for (a, b), count in pair_counts.items()]
    return sorted(rows, key=lambda row: (-row[2], row[0], row[1]))[:limit]


def comparison_rows(pair_counts, import_edges, limit=None, relation_filter=None):
    """Return co-change rows enriched with import-relation classification."""
    rows = []
    for (file_a, file_b), count in pair_counts.items():
        relation = import_relation(file_a, file_b, import_edges)
        if relation_filter and relation != relation_filter:
            continue
        rows.append((file_a, file_b, count, relation))

    rows.sort(key=lambda row: (-row[2], row[3], row[0], row[1]))
    if limit is not None:
        return rows[:limit]
    return rows


def import_edges_with_cochange(import_edges, pair_counts, limit):
    """Return examples of direct import edges with low co-change counts."""
    rows = []
    for source, target in sorted(import_edges):
        pair = tuple(sorted((source, target)))
        rows.append((source, target, pair_counts.get(pair, 0)))
    rows.sort(key=lambda row: (row[2], row[0], row[1]))
    return rows[:limit]


def write_markdown_summary(path, stats, top_cochange, comparison_top, no_import_top, low_imports):
    """Write a compact Markdown summary of the analysis results."""
    lines = [
        "# Co-change and Import Comparison Summary",
        "",
        "## Method Snapshot",
        "",
        f"- Non-merge commits scanned: {stats['non_merge_commits_seen']}",
        f"- Commits touching selected source files: {stats['commits_with_selected_files']}",
        f"- Broad commits skipped: {stats['commits_skipped_as_broad']}",
        f"- Maximum selected files per commit: {stats['max_files_per_commit']}",
        f"- Commits used for pair counting: {stats['commits_used_for_pair_counting']}",
        f"- Distinct co-changed pairs found: {stats['distinct_cochanged_pairs']}",
        "",
        "## Top Co-changed Pairs",
        "",
        "| File A | File B | Commits |",
        "|---|---|---:|",
    ]

    for file_a, file_b, count in top_cochange:
        lines.append(f"| `{file_a}` | `{file_b}` | {count} |")

    lines.extend(
        [
            "",
            "## Top Co-changed Pairs Compared With Imports",
            "",
            "| File A | File B | Commits | Import relation |",
            "|---|---|---:|---|",
        ]
    )
    for file_a, file_b, count, relation in comparison_top:
        lines.append(f"| `{file_a}` | `{file_b}` | {count} | {relation} |")

    lines.extend(
        [
            "",
            "## High Co-change Without Direct Import",
            "",
            "| File A | File B | Commits |",
            "|---|---|---:|",
        ]
    )
    for file_a, file_b, count, _ in no_import_top:
        lines.append(f"| `{file_a}` | `{file_b}` | {count} |")

    lines.extend(
        [
            "",
            "## Direct Imports With Low Co-change",
            "",
            "| Source | Target | Co-changed commits |",
            "|---|---|---:|",
        ]
    )
    for source, target, count in low_imports:
        lines.append(f"| `{source}` | `{target}` | {count} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default="/home/noralea/Desktop/spack",
        help="Path to the Spack repository",
    )
    parser.add_argument(
        "--imports",
        default="/home/noralea/Desktop/UNI/SDA/Project workflow/CodeDependecyAnalysis/data/import_edges.csv",
        help="CSV import graph produced by the import dependency analysis",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/noralea/Desktop/UNI/SDA/Project workflow/CodeDependecyAnalysis/data",
        help="Directory where output files will be written",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of rows to write in the short result tables",
    )
    parser.add_argument(
        "--max-files-per-commit",
        type=int,
        default=50,
        help="Skip commits touching more than this number of selected files",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    import_path = Path(args.imports).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    valid_files = tracked_files(repo_root)
    import_edges = load_import_edges(import_path)

    commits = read_commits(repo_root, valid_files, args.max_files_per_commit)
    pair_counts, commits_used = count_pairs(commits)

    stats = dict(read_commits.stats)
    stats["current_selected_files"] = len(valid_files)
    stats["import_edges_loaded"] = len(import_edges)
    stats["commits_used_for_pair_counting"] = commits_used
    stats["distinct_cochanged_pairs"] = len(pair_counts)

    top_cochange = top_pair_rows(pair_counts, args.limit)
    comparison_top = comparison_rows(pair_counts, import_edges, args.limit)
    no_import_top = comparison_rows(
        pair_counts, import_edges, args.limit, relation_filter="no direct import"
    )
    with_import_top = [
        row for row in comparison_rows(pair_counts, import_edges) if row[3] != "no direct import"
    ][: args.limit]
    low_imports = import_edges_with_cochange(import_edges, pair_counts, args.limit)

    write_csv(
        output_dir / "cochange_pairs.csv",
        ["file_a", "file_b", "cochanged_commits"],
        [(a, b, count) for (a, b), count in sorted(pair_counts.items())],
    )
    write_csv(
        output_dir / "top_cochange_pairs.csv",
        ["file_a", "file_b", "cochanged_commits"],
        top_cochange,
    )
    write_csv(
        output_dir / "comparison_top_cochange.csv",
        ["file_a", "file_b", "cochanged_commits", "import_relation"],
        comparison_top,
    )
    write_csv(
        output_dir / "high_cochange_without_direct_import.csv",
        ["file_a", "file_b", "cochanged_commits", "import_relation"],
        no_import_top,
    )
    write_csv(
        output_dir / "high_cochange_with_direct_import.csv",
        ["file_a", "file_b", "cochanged_commits", "import_relation"],
        with_import_top,
    )
    write_csv(
        output_dir / "direct_imports_with_low_cochange.csv",
        ["source", "target", "cochanged_commits"],
        low_imports,
    )

    (output_dir / "cochange_summary.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown_summary(
        output_dir / "cochange_comparison_summary.md",
        stats,
        top_cochange,
        comparison_top,
        no_import_top,
        low_imports,
    )

    print(f"Wrote co-change and comparison outputs to {output_dir}")


if __name__ == "__main__":
    main()
