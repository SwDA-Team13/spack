# Dependencies

## Method and Tools

The dependency analysis uses two views of the Spack source code. The first view is based on imports in the source code. The second view is based on Git co-change, meaning that two files are considered related when they are modified in the same commit.

For code dependencies, `scripts/import_dependency_analysis.py` parses Python files with the standard `ast` module and extracts `import` and `from ... import ...` statements. A directed edge `A -> B` means that file `A` imports a local module implemented by file `B`. This is more reliable than plain text search because it follows Python syntax.

For knowledge dependencies, `scripts/cochange_import_comparison.py` scans Git history with `git log --no-merges --name-only`. For each non-merge commit, it keeps selected source files changed in that commit and counts every pair of files changed together. Co-change pairs are unordered because Git history only shows that files changed in the same commit, not that one file depends directionally on the other.

Both analyses use the same source scope: `bin/spack`, `lib/spack/spack`, and `lib/spack/llnl`. Vendored code, tests, mock repositories, caches, virtual environments, and generated/build folders were excluded. In the co-change analysis, commits touching more than 50 selected files were skipped to reduce the effect of broad mechanical changes such as large refactorings or formatting.

The import analysis considered 327 files and found 1984 local import edges. The co-change analysis scanned 40771 non-merge commits, found 5551 commits touching selected source files, skipped 27 broad commits, and used 5524 commits for pair counting.

## Code Dependencies

Files with many outgoing imports usually coordinate several parts of the system. This can increase cognitive load because understanding the file may require understanding many imported modules.

| File | Local imports |
|---|---:|
| `lib/spack/spack/package.py` | 40 |
| `lib/spack/spack/binary_distribution.py` | 39 |
| `lib/spack/spack/solver/asp.py` | 37 |
| `lib/spack/spack/config.py` | 35 |
| `lib/spack/spack/package_base.py` | 35 |
| `lib/spack/spack/new_installer.py` | 32 |
| `lib/spack/spack/environment/environment.py` | 31 |
| `lib/spack/spack/spec.py` | 30 |
| `lib/spack/spack/ci/__init__.py` | 27 |
| `lib/spack/spack/installer.py` | 27 |

The highest outgoing values are in central modules. `package.py`, `package_base.py`, and `spec.py` belong to the package/spec model. `solver/asp.py`, `new_installer.py`, `installer.py`, and `environment/environment.py` implement workflows that connect package modeling, concretization, installation, and environment management. This suggests structural coupling, but not automatically poor design, because these files also have broad coordinating responsibilities.

Files with many incoming imports are used by many other files. These are often shared utilities, shared abstractions, or common services.

| File | Imported by local files |
|---|---:|
| `lib/spack/spack/llnl/util/tty/__init__.py` | 136 |
| `lib/spack/spack/spec.py` | 99 |
| `lib/spack/spack/error.py` | 89 |
| `lib/spack/spack/config.py` | 87 |
| `lib/spack/spack/llnl/util/filesystem.py` | 69 |
| `lib/spack/spack/repo.py` | 67 |
| `lib/spack/spack/llnl/util/lang.py` | 62 |
| `lib/spack/spack/cmd/common/arguments.py` | 52 |
| `lib/spack/spack/cmd/__init__.py` | 51 |
| `lib/spack/spack/store.py` | 48 |

The most imported files are common infrastructure and core abstractions: terminal output, filesystem utilities, configuration, repositories, the install store, command arguments, and `Spec`.

The analysis also found 53 files with zero outgoing local imports and 92 files with zero incoming local imports. Examples include `cmd/docs.py`, `cmd/pydoc.py`, several `__init__.py` files, and `platforms/cray.py`. Low dependency count can indicate small leaf modules, package marker files, dynamically loaded command modules, or narrow platform-specific files. It does not mean the files are unimportant.

## Knowledge Dependencies

The co-change analysis found 14330 distinct file pairs changed together at least once. The highest pairs are:

| File A | File B | Co-changed commits |
|---|---|---:|
| `lib/spack/spack/solver/asp.py` | `lib/spack/spack/spec.py` | 101 |
| `lib/spack/spack/package.py` | `lib/spack/spack/spec.py` | 92 |
| `lib/spack/spack/concretize.py` | `lib/spack/spack/spec.py` | 87 |
| `lib/spack/spack/build_environment.py` | `lib/spack/spack/package.py` | 77 |
| `lib/spack/spack/database.py` | `lib/spack/spack/spec.py` | 70 |
| `lib/spack/spack/package.py` | `lib/spack/spack/stage.py` | 70 |
| `lib/spack/spack/build_environment.py` | `lib/spack/spack/spec.py` | 59 |
| `lib/spack/spack/fetch_strategy.py` | `lib/spack/spack/stage.py` | 57 |
| `lib/spack/spack/binary_distribution.py` | `lib/spack/spack/cmd/buildcache.py` | 56 |
| `lib/spack/spack/cmd/__init__.py` | `lib/spack/spack/spec.py` | 55 |

These pairs mainly involve package modeling, concretization, build environments, staging, binary distribution, and command workflows. This is consistent with Spack's domain: installation requires package metadata, concrete specs, source fetching/staging, binary caches, and command behavior to evolve together.

## Comparison

Many high co-change pairs also have a direct import edge. These cases are consistent because the static code relation and historical change relation point to the same dependency.

| File A | File B | Co-changed commits | Import relation |
|---|---|---:|---|
| `solver/asp.py` | `spec.py` | 101 | `solver/asp.py` imports `spec.py` |
| `package.py` | `spec.py` | 92 | `package.py` imports `spec.py` |
| `concretize.py` | `spec.py` | 87 | `concretize.py` imports `spec.py` |
| `build_environment.py` | `package.py` | 77 | `package.py` imports `build_environment.py` |
| `database.py` | `spec.py` | 70 | `database.py` imports `spec.py` |
| `fetch_strategy.py` | `stage.py` | 57 | `stage.py` imports `fetch_strategy.py` |

The main inconsistencies are high co-change pairs without direct imports:

| File A | File B | Co-changed commits |
|---|---|---:|
| `package.py` | `stage.py` | 70 |
| `cmd/install.py` | `package.py` | 55 |
| `__init__.py` | `package.py` | 48 |
| `directory_layout.py` | `package.py` | 46 |
| `fetch_strategy.py` | `package.py` | 46 |
| `database.py` | `package.py` | 43 |
| `compilers/__init__.py` | `spec.py` | 39 |
| `cmd/uninstall.py` | `package.py` | 35 |
| `cmd/create.py` | `package.py` | 34 |
| `cmd/uninstall.py` | `database.py` | 34 |

These pairs may indicate knowledge dependencies not visible as direct imports. For example, `package.py` and `stage.py` both participate in source preparation and installation. Command modules such as `cmd/install.py`, `cmd/uninstall.py`, and `cmd/create.py` can co-change with package or database modules because they depend on the same workflows, even when no direct import is detected.

The opposite case also exists: some direct imports have little or no co-change. This often happens when a module imports a stable utility. In that case, the structural dependency exists, but the two files may evolve independently.

## Summary

The import graph shows Spack's structural dependencies: central workflow files have many outgoing imports, while shared utilities and core abstractions have many incoming imports. The co-change graph shows historical maintenance dependencies: files involved in package modeling, concretization, staging, installation, and binary distribution often change together. The comparison shows that the two views are partly consistent, especially around `spec.py`, `package.py`, and `solver/asp.py`, but some important maintenance relationships are not visible from direct imports alone.
