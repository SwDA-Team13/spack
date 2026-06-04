# Pattern 2: Singleton for shared global services

**Pattern identified:** Singleton  
**Main files:** `lib/spack/spack/llnl/util/lang.py`, `lib/spack/spack/config.py`, `lib/spack/spack/store.py`, `lib/spack/spack/repo.py`

Spack uses a reusable `Singleton` wrapper to manage shared objects that should have one main instance during normal execution. The implementation is Python-specific: instead of a private constructor and a static `getInstance()` method, `Singleton` stores a factory function, creates the object lazily, and keeps it in `_instance`.

| Class / element | Line | Role / purpose |
|---|---:|---|
| `Singleton` | `lang.py:713` | Singleton controller: stores the factory and exposes the lazily created instance. |
| `Configuration` / `CONFIG` | `config.py:514`, `1563` | Shared configuration object used through `spack.config.CONFIG`. |
| `Store` / `STORE` | `store.py:135`, `299` | Shared installation store object used through `spack.store.STORE`. |
| `RepoPath` / `PATH` | `repo.py:697`, `2104` | Shared package repository path used through `spack.repo.PATH`. |
| `FileCache` / `MISC_CACHE` | `util/file_cache.py:88`, `caches.py:33` | Shared cache for small persistent Spack data. |
| `FsCache` / `FETCH_CACHE` | `fetch_strategy.py:1786`, `caches.py:68` | Shared cache for downloaded source archives. |

The pattern is used because these services represent process-wide concepts. Configuration, the install store, the package repository path, and caches should not be recreated independently in different parts of the program, because that could give clients different views of the same global state. Lazy creation also avoids initializing these services before they are needed.

A class represents a concept that requires a single instance, and clients could use it incorrectly if they freely created separate instances. In Spack, clients access the shared object through module-level variables such as `CONFIG`, `STORE`, and `PATH`; the `Singleton` wrapper creates the real object only on first use and then returns the same object through `instance`.

An alternative would be to create normal module-level objects eagerly at import time. This would be simpler to read, but it could make imports heavier and introduce initialization-order problems, especially because configuration, repository paths, and stores depend on runtime setup. Another alternative would be explicit dependency passing, where functions receive configuration, store, and cache objects as parameters. That would reduce global state and make dependencies clearer, but it would require changing many call sites and would make common operations more verbose.

The Singleton approach gives Spack a compact access point for shared services, with the trade-off that global state must be reset carefully in tests or when Spack intentionally changes configuration or store context.

## Code references to link later

| File | Line(s) | Element |
|---|---:|---|
| `llnl/util/lang.py` | 713 | `class Singleton` |
| `llnl/util/lang.py` | 733-734 | `factory` and `_instance` fields |
| `llnl/util/lang.py` | 736-756 | `Singleton.instance` creates and stores the object lazily |
| `llnl/util/lang.py` | 758-765 | `__getattr__` delegates access to the singleton instance |
| `config.py` | 514 | `class Configuration` |
| `config.py` | 1563 | `CONFIG = Singleton(create_incremental)` |
| `store.py` | 135 | `class Store` |
| `store.py` | 299 | `STORE = Singleton(_create_global)` |
| `repo.py` | 697 | `class RepoPath` |
| `repo.py` | 2104 | `PATH = Singleton(...)` |
| `util/file_cache.py` | 88 | `class FileCache` |
| `caches.py` | 33 | `MISC_CACHE = Singleton(_misc_cache)` |
| `fetch_strategy.py` | 1786 | `class FsCache` |
| `caches.py` | 68 | `FETCH_CACHE = Singleton(_fetch_cache)` |
