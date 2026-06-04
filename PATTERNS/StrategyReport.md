# Pattern 1: Strategy in source fetching

**Pattern identified:** Strategy  
**Main files:** `lib/spack/spack/fetch_strategy.py`, `lib/spack/spack/package_base.py`, `lib/spack/spack/stage.py`

Spack applies a Strategy-like design to source fetching. The stable task is obtaining and preparing package source code; the concrete behavior changes for archive URLs, Git, SVN, Mercurial, S3, GCS, and other source types.

`FetchStrategy` plays the Strategy interface role; `VCSFetchStrategy` is an intermediate base for version-control strategies; the other fetcher classes listed below are Concrete Strategies. The Context/client role is played by package and stage code: `PackageBase.fetcher` selects a fetcher for the package version, and `Stage` stores and calls the selected fetcher.

| Class | Line | Purpose |
|---|---:|---|
| `FetchStrategy` | 92 | Defines the common fetcher lifecycle: `fetch`, `check`, `expand`, `reset`, and `archive`. |
| `BundleFetchStrategy` | 193 | Used for no-code packages; it keeps the same workflow but has no source archive to fetch. |
| `URLFetchStrategy` | 336 | Downloads source archives from normal URLs and handles checksum, expansion, reset, and archive creation. |
| `CacheURLFetchStrategy` | 627 | Reuses a local cached archive instead of downloading it again. |
| `OCIRegistryFetchStrategy` | 659 | Fetches content from an OCI registry; it is used by the OCI-specific stage creation code. |
| `VCSFetchStrategy` | 686 | Collects behavior shared by version-control fetchers, such as already-expanded sources and no checksum requirement. |
| `GoFetchStrategy` | 743 | Fetches Go resources through the Go toolchain. |
| `GitFetchStrategy` | 812 | Fetches source code from Git repositories. |
| `CvsFetchStrategy` | 1052 | Fetches source code from CVS repositories. |
| `SvnFetchStrategy` | 1170 | Fetches source code from Subversion repositories. |
| `HgFetchStrategy` | 1263 | Fetches source code from Mercurial repositories. |
| `S3FetchStrategy` | 1375 | Fetches archives from S3 storage. |
| `GCSFetchStrategy` | 1397 | Fetches archives from Google Cloud Storage. |
| `FetchAndVerifyExpandedFile` | 1421 | Downloads an archive and verifies the checksum of the expanded file. |

The `@fetcher` decorator registers most strategies, while `from_kwargs`, `for_package_version`, and `from_url_scheme` choose an appropriate strategy from package metadata or a URL scheme.

The pattern is used because Spack must support several fetching mechanisms while preserving a common lifecycle. The rest of the system can work with a fetcher through the same high-level operations, while each concrete strategy keeps the protocol-specific behavior and validation rules localized. This matches the course definition of Strategy: several behavioral variations are separated into objects sharing a common interface.

An alternative would be a single fetcher with many `if`/`elif` branches checking URL schemes or package attributes. It would be simpler for a very small number of protocols and would keep logic in one place. In Spack, however, it would likely become harder to maintain: unrelated protocols would be coupled in the same method, and every new source type would modify central code.

The current design has more classes and some selection logic, but it keeps variations separated and easier to extend.

## Code references to link later

| File | Line(s) | Class / function |
|---|---:|---|
| `fetch_strategy.py` | 86 | `def fetcher(cls)` |
| `fetch_strategy.py` | 92 | `class FetchStrategy` |
| `fetch_strategy.py` | 120-145 | `FetchStrategy.fetch`, `check`, `expand`, `reset`, `archive` |
| `fetch_strategy.py` | 193 | `class BundleFetchStrategy(FetchStrategy)` |
| `fetch_strategy.py` | 336 | `class URLFetchStrategy(FetchStrategy)` |
| `fetch_strategy.py` | 627 | `class CacheURLFetchStrategy(URLFetchStrategy)` |
| `fetch_strategy.py` | 659 | `class OCIRegistryFetchStrategy(URLFetchStrategy)` |
| `fetch_strategy.py` | 686 | `class VCSFetchStrategy(FetchStrategy)` |
| `fetch_strategy.py` | 743 | `class GoFetchStrategy(VCSFetchStrategy)` |
| `fetch_strategy.py` | 812 | `class GitFetchStrategy(VCSFetchStrategy)` |
| `fetch_strategy.py` | 1052 | `class CvsFetchStrategy(VCSFetchStrategy)` |
| `fetch_strategy.py` | 1170 | `class SvnFetchStrategy(VCSFetchStrategy)` |
| `fetch_strategy.py` | 1263 | `class HgFetchStrategy(VCSFetchStrategy)` |
| `fetch_strategy.py` | 1375 | `class S3FetchStrategy(URLFetchStrategy)` |
| `fetch_strategy.py` | 1397 | `class GCSFetchStrategy(URLFetchStrategy)` |
| `fetch_strategy.py` | 1421 | `class FetchAndVerifyExpandedFile(URLFetchStrategy)` |
| `fetch_strategy.py` | 1482 | `def from_kwargs(**kwargs)` |
| `fetch_strategy.py` | 1579 | `def for_package_version(pkg, version=None)` |
| `fetch_strategy.py` | 1705 | `def from_url_scheme(url, **kwargs)` |
| `package_base.py` | 1374 | `PackageBase.fetcher` |
| `stage.py` | 381 | `class Stage` |
| `stage.py` | 470-475 | `Stage.__init__` stores the selected fetcher |
| `stage.py` | 608-609 | `Stage.fetch` calls `self.fetcher.fetch()` |
