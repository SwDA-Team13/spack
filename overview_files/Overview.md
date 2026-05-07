# Overview

## 1. Purpose and Stakeholders

Spack is a source-oriented package management and build system for scientific and high-performance computing software. Its purpose is to model software specifications, resolve dependencies, configure builds for particular compilers and platforms, and install reproducible software stacks. Its main stakeholders include HPC users, scientific software developers, package maintainers, system administrators, research institutions, and users of CI/build infrastructure that need repeatable builds across heterogeneous systems.

## 2. System Description

This repository is primarily a Python application with a shell/Python launcher in `bin/spack`. The launcher selects a Python interpreter, adds `lib/spack` to `sys.path`, and delegates to `spack.main`, which builds the command-line parser, discovers subcommands from `lib/spack/spack/cmd`, and routes user actions.

The core implementation is under `lib/spack/spack`. Package behavior is represented by modules such as `package.py`, `package_base.py`, `directives.py`, `variant.py`, `dependency.py`, `spec.py`, and `version`, which together describe package metadata, constraints, versions, variants, virtual providers, patches, and dependency edges. In this checkout, identifiable recipe files are test-repository recipes under `var/spack/test_repos/.../packages/*/package.py`; no tracked production `var/spack/repos/builtin` package catalog is present.

Concretization and dependency resolution are concentrated in `lib/spack/spack/solver`, including Python code and ASP/Clingo logic files such as `concretize.lp`, `heuristic.lp`, and compatibility rules. Build and install behavior is spread across `builder.py`, `installer.py`, `new_installer.py`, `build_environment.py`, `stage.py`, `fetch_strategy.py`, `store.py`, and package base classes. Environment management is implemented in `lib/spack/spack/environment`, using `spack.yaml` manifests and `spack.lock` lockfiles. Repository loading and package indexes are handled by `repo.py`, `provider_index.py`, and cache-related modules.

Configuration and machine adaptation are implemented through `config.py`, schemas in `schema`, defaults in `etc/spack/defaults`, and platform/compiler support in `platforms`, `operating_systems`, `compilers`, `archspec.py`, and `detection`. The repository also contains module generation, mirrors, binary distribution, container, OCI, reporting, and CI support. Tests are centered in `lib/spack/spack/test`, with mock package repositories in `var/spack/test_repos`; CI configuration appears in `.github/workflows`, `.ci`, `pytest.ini`, and `pyproject.toml`.

## 3. Basic Code Statistics

Statistics were computed from Git-tracked files at commit `2f9910ee1c`. The count excludes `.git` implicitly through `git ls-files`, and explicitly excludes vendored dependency folders (`lib/spack/spack/vendor`, `lib/spack/_vendoring`, `var/spack/vendoring`) plus common cache/build/virtual-environment names. Line counts are text-line counts used as a LOC proxy; 46 binary files and 35 non-regular entries were skipped for line counting.

| Metric | Value |
|---|---:|
| Total files analyzed | 1,581 |
| Total lines of code/text counted | 295,164 |
| Python files | 1,004 |
| Python lines of code | 223,275 |
| Package recipe files (`packages/*/package.py`) | 437 |
| Test Python files | 219 |
| Test directories | 85 |
| Top-level modules/packages under `lib/spack/spack` | 87 core, 89 including `test` and `vendor` |
| Git contributor identities | 1,954 |

The contributor count is based on unique Git author name/email identities from local history, so it may overcount people who committed with multiple email addresses.
