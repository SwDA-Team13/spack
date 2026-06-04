# Software Design Analysis

## Dependencies

The dependency analysis was based on two complementary views of the Spack codebase. Code dependencies were reconstructed from imports in the source code. The used script parses Python files with the standard `ast` module, extracts `import` and `from ... import ...` statements, and maps local modules to their source files. A directed edge `A -> B` therefore means that file `A` imports a local module implemented by file `B`. Knowledge dependencies were reconstructed from Git co-change using another script: two files are considered historically related when they are modified in the same non-merge commit. Co-change is intentionally undirected, because it describes maintenance relation rather than call or import direction.

Both analyses used the same project scope: `bin/spack`, `lib/spack/spack`, and `lib/spack/llnl`. Tests, mock repositories, vendored code, caches, generated files, virtual environments, and build folders were excluded. Commits touching more than 50 selected files were also skipped in the co-change phase to reduce the impact of broad mechanical changes. The import analysis considered 327 files and found 1984 local import edges. The co-change analysis scanned 40771 non-merge commits, found 5551 commits touching selected source files, skipped 27 broad commits, and used 5524 commits for pair counting.

Using both views is important because each one has a different bias. Imports expose explicit structural dependencies, but they can miss relations mediated by shared data models, command workflows, conventions, or runtime composition. Co-change can reveal those relations, but it can also include files changed together for planning or release reasons. The comparison is therefore more informative than either measure alone.

### Code Dependencies

Files with the highest number of outgoing local imports are mainly coordination modules. They connect several parts of the system and therefore require broader knowledge to understand or modify.

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

The highest outgoing values are coherent with Spack's architecture. `package.py`, `package_base.py`, and `spec.py` are central to the package/spec model. `solver/asp.py`, `new_installer.py`, `installer.py`, and `environment/environment.py` coordinate concretization, installation, and environment workflows. Their high dependency count is not automatically a design defect, but it identifies files where changes can require more architectural context.

The distinction between outgoing and incoming dependencies is relevant. High outgoing imports indicate modules that assemble behavior from many collaborators. High incoming imports indicate modules that many other modules trust as stable infrastructure. A file can therefore be central for different reasons: it may coordinate a workflow, or it may provide a common abstraction used across workflows.

Files with the highest incoming imports are shared abstractions and infrastructure used by many clients.

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

The result highlights stable services and core abstractions: terminal output, error handling, filesystem utilities, configuration, repository access, command arguments, the install store, and the `Spec` model. These files have high fan-in because they provide common facilities rather than isolated features.

The files with the least dependencies have total degree 0 or 1 in the local import graph.

| File | Out | In | Total |
|---|---:|---:|---:|
| `lib/spack/spack/cmd/docs.py` | 0 | 0 | 0 |
| `lib/spack/spack/cmd/pydoc.py` | 0 | 0 | 0 |
| `lib/spack/spack/hooks/windows_runtime_linkage.py` | 0 | 0 | 0 |
| `lib/spack/spack/mirrors/__init__.py` | 0 | 0 | 0 |
| `lib/spack/spack/oci/__init__.py` | 0 | 0 | 0 |
| `lib/spack/spack/platforms/cray.py` | 0 | 0 | 0 |
| `lib/spack/spack/compilers/__init__.py` | 0 | 1 | 1 |
| `lib/spack/spack/package_completions.py` | 0 | 1 | 1 |

Overall, the analysis found 53 files with zero outgoing local imports and 92 files with zero incoming local imports. Low dependency count usually reflects a narrow role, a package marker file, dynamic loading, or platform-specific code. It should not be read as low importance by itself.

### Knowledge Dependencies and Comparison

The co-change analysis found 14330 distinct file pairs changed together at least once. The strongest pairs were:

| File A | File B | Co-changed commits |
|---|---|---:|
| `lib/spack/spack/solver/asp.py` | `lib/spack/spack/spec.py` | 101 |
| `lib/spack/spack/package.py` | `lib/spack/spack/spec.py` | 92 |
| `lib/spack/spack/concretize.py` | `lib/spack/spack/spec.py` | 87 |
| `lib/spack/spack/build_environment.py` | `lib/spack/spack/package.py` | 77 |
| `lib/spack/spack/database.py` | `lib/spack/spack/spec.py` | 70 |
| `lib/spack/spack/package.py` | `lib/spack/spack/stage.py` | 70 |
| `lib/spack/spack/fetch_strategy.py` | `lib/spack/spack/stage.py` | 57 |
| `lib/spack/spack/binary_distribution.py` | `lib/spack/spack/cmd/buildcache.py` | 56 |
| `lib/spack/spack/cmd/install.py` | `lib/spack/spack/package.py` | 55 |

The highest co-change values are concentrated around package modeling, concretization, build environments, staging, fetching, binary distribution, and command workflows. This is expected for Spack: installing software requires package metadata, concrete specs, source preparation, cache behavior, and command behavior to evolve together.

Several high co-change pairs are consistent with direct imports. `solver/asp.py` imports `spec.py`; `package.py` imports `spec.py`; `concretize.py` imports `spec.py`; `database.py` imports `spec.py`; `stage.py` imports `fetch_strategy.py`. In these cases, the code dependency and the historical maintenance dependency confirm each other.

The main inconsistencies are high co-change pairs without a direct import edge:

| File A | File B | Co-changed commits |
|---|---|---:|
| `package.py` | `stage.py` | 70 |
| `cmd/install.py` | `package.py` | 55 |
| `directory_layout.py` | `package.py` | 46 |
| `fetch_strategy.py` | `package.py` | 46 |
| `database.py` | `package.py` | 43 |
| `compilers/__init__.py` | `spec.py` | 39 |
| `cmd/uninstall.py` | `package.py` | 35 |
| `cmd/create.py` | `package.py` | 34 |
| `cmd/uninstall.py` | `database.py` | 34 |

These pairs identify knowledge dependencies that imports do not expose. For instance, command modules co-change with package or database modules because they implement the user-facing side of the same workflows, even when direct imports are absent. The opposite case also appears: some direct imports have little or no co-change, especially when a module imports a stable utility. Therefore, import dependencies describe static structure, while co-change captures historical coupling in maintenance work.

The inconsistent pairs are relevant from a design perspective because they indicate dependencies that are more conceptual than syntactic. They are useful candidates for documentation, integration tests, or architectural discussion: a developer modifying one file may need to understand the other even without an import relation. Conversely, direct imports with low co-change usually point to stable services whose interfaces have not forced frequent joint evolution.

## Pattern Usage

### Strategy: Source Fetching

| Class | Line | Role |
|---|---:|---|
| `FetchStrategy` | `fetch_strategy.py:92` | Strategy interface defining the common fetch lifecycle. |
| `BundleFetchStrategy` | `fetch_strategy.py:193` | Concrete strategy for no-code packages. |
| `URLFetchStrategy` | `fetch_strategy.py:336` | Concrete strategy for archive URLs. |
| `CacheURLFetchStrategy` | `fetch_strategy.py:627` | Concrete strategy for cached archives. |
| `OCIRegistryFetchStrategy` | `fetch_strategy.py:659` | Concrete strategy for OCI registry sources. |
| `VCSFetchStrategy` | `fetch_strategy.py:686` | Intermediate strategy for version-control fetchers. |
| `GoFetchStrategy` | `fetch_strategy.py:743` | Concrete strategy for Go resources. |
| `GitFetchStrategy` | `fetch_strategy.py:812` | Concrete strategy for Git repositories. |
| `CvsFetchStrategy` | `fetch_strategy.py:1052` | Concrete strategy for CVS repositories. |
| `SvnFetchStrategy` | `fetch_strategy.py:1170` | Concrete strategy for Subversion repositories. |
| `HgFetchStrategy` | `fetch_strategy.py:1263` | Concrete strategy for Mercurial repositories. |
| `S3FetchStrategy` | `fetch_strategy.py:1375` | Concrete strategy for S3 archives. |
| `GCSFetchStrategy` | `fetch_strategy.py:1397` | Concrete strategy for Google Cloud Storage archives. |
| `FetchAndVerifyExpandedFile` | `fetch_strategy.py:1421` | Concrete strategy for expanded-file checksum verification. |
| `PackageBase.fetcher` / `Stage` | `package_base.py:1374`, `stage.py:381` | Context/client selecting, storing, and invoking the strategy. |

Spack uses Strategy because fetching source code is a stable operation with many protocol-specific variants. The pattern keeps the common lifecycle (`fetch`, `check`, `expand`, `reset`, `archive`) uniform while localizing protocol behavior in separate classes. A single fetcher with conditional branches would reduce class count, but it would mix unrelated protocols and make new source types modify central logic. Strategy is therefore more suitable for extension, at the cost of more classes and registration logic.

This is a strong use of Strategy because the variation is not accidental: protocol-specific fetching is a recurring extension point in the project. The design protects `Stage` and package code from knowing the details of each source mechanism.

### Singleton: Shared Global Services

| Class | Line | Role |
|---|---:|---|
| `Singleton` | `lang.py:713` | Singleton controller with lazy instance creation. |
| `Configuration` / `CONFIG` | `config.py:514`, `1563` | Shared configuration service. |
| `Store` / `STORE` | `store.py:135`, `299` | Shared installation store. |
| `RepoPath` / `PATH` | `repo.py:697`, `2104` | Shared package repository path. |
| `FileCache` / `MISC_CACHE` | `file_cache.py:88`, `caches.py:33` | Shared cache for persistent Spack data. |
| `FsCache` / `FETCH_CACHE` | `fetch_strategy.py:1786`, `caches.py:68` | Shared cache for downloaded sources. |

The Singleton wrapper is used for services that represent process-wide state. Configuration, store, repositories, and caches should not be independently recreated by unrelated clients, because this could produce inconsistent views of the same execution context. Eager module-level objects would be simpler, but could create import-time initialization problems. Explicit dependency passing would make dependencies clearer and reduce global state, but would require extensive call-site changes. Singleton gives compact access to shared services, with the trade-off that tests and context changes must reset global state carefully.

The important architectural point is the controlled access to one lazily created shared instance, not the presence of a private constructor.

### Adapter: Legacy Compiler Access

| Class | Line | Role |
|---|---:|---|
| `Package.compiler` | `package_base.py:547` | Target interface expected by legacy package code. |
| `CompilerAdaptor` | `adaptor.py:19` | Adapter exposing old compiler-style properties. |
| `Languages` | `adaptor.py:13` | Language keys used by the adapter. |
| Compiler dependency specs | `adaptor.py:25`, `218-223` | Adaptee data used internally by the adapter. |
| `DeprecatedCompiler` | `adaptor.py:209` | Descriptor that creates the adapter on access. |
| `DeprecatedCompiler.factory()` | `adaptor.py:213` | Factory method collecting compiler specs and returning the adapter. |

Spack uses Adapter because compiler information moved toward compiler dependency specs, while existing package code may still access `self.compiler`. `CompilerAdaptor` translates the old interface into the newer model and validates that the requested compiler language is available. Removing `Package.compiler` would make the model cleaner, but would require coordinated changes across existing packages and could break compatibility. Keeping duplicated old and new compiler data would reduce migration effort, but would risk inconsistent sources of truth.

The adapter therefore solves a migration problem: it allows the internal representation to evolve while preserving the client interface expected by older package logic. This reduces the risk of changing a broad package ecosystem at once.

### Composite: Package Staging

| Class | Line | Role |
|---|---:|---|
| `AbstractStage` | `stage.py:221` | Component interface for stage-like objects. |
| `Stage` | `stage.py:381` | Leaf representing a normal source or archive stage. |
| `DevelopStage` | `stage.py:968` | Leaf representing a development source stage. |
| `StageComposite` | `stage.py:836` | Composite storing several stages and forwarding operations. |
| `StageComposite._stages` | `stage.py:842` | Children collection. |
| `PackageBase._make_stages()` | `package_base.py:1192` | Client logic creating source, resource, and patch stages. |
| `PackageBase.stage` | `package_base.py:1267` | Client access point for staging operations. |

Composite is used because package staging can be either single or made of several related stages. `StageComposite` forwards lifecycle operations to all contained stages and exposes root-source properties through the first stage. Without this pattern, `PackageBase` would need to keep a plain list and repeat loops across staging operations. Separate methods for root, resource, and patch stages would be explicit, but would duplicate lifecycle logic. Composite centralizes group behavior, with the trade-off of an additional wrapper and a Python implementation that follows the interface operationally rather than by formal inheritance.

The design is especially appropriate because the client is interested in the staging lifecycle, not in the internal number of stages. This reduces the amount of conditional logic in package-level operations.

### Visitor: Package AST Processing

| Class | Line | Role |
|---|---:|---|
| Python AST node classes | `stdlib` | Element structure visited during package hashing. |
| `ast.NodeVisitor` / `ast.NodeTransformer` | `stdlib` | Visitor base interfaces. |
| `RemoveDocstrings` | `package_hash.py:34` | Concrete visitor removing docstrings. |
| `RemoveDirectives` | `package_hash.py:62` | Concrete visitor removing Spack directives not relevant to hashing. |
| `TagMultiMethods` | `package_hash.py:178` | Concrete visitor recording conditional multi-methods. |
| `ResolveMultiMethods` | `package_hash.py:236` | Concrete visitor resolving methods relevant to the current hash. |
| `package_hash()` logic | `package_hash.py:380-392` | Client applying visitors to the parsed source tree. |

Spack uses Visitor through Python's AST visitor infrastructure. The object structure is the parsed syntax tree of a package file, while the operations are hash-related transformations and analyses. The pattern is useful because these operations depend on node types, but the AST node classes belong to Python and should not contain Spack-specific hashing logic. A manual recursive traversal would reduce the number of classes, but would mix traversal, transformation, and state handling in one place. Another alternative would be several independent `ast.walk()` loops. That would be straightforward, but each loop would repeat traversal decisions and state handling. The Visitor approach makes the operations more modular, at the cost of several small classes and some dependence on the AST node structure.

## Summary

The dependency analysis shows a dense architectural core around packages, specs, concretization, installation, staging, fetching, configuration, and command workflows. Import dependencies expose explicit structural coupling: central workflow modules have many outgoing imports, while shared utilities and core abstractions have high incoming imports. Co-change dependencies expose historical maintenance coupling: files involved in the same installation workflow often evolve together even without direct imports. The inconsistent pairs are especially useful because they reveal design knowledge that is not visible from source imports alone.

The pattern analysis shows that Spack uses design patterns pragmatically rather than mechanically. Strategy separates source-fetching variants; Singleton controls access to process-wide services; Adapter preserves compatibility during a compiler model transition; Composite manages groups of stages through a uniform interface; Visitor structures AST-based package hashing. These patterns mainly support extensibility, compatibility and control of workflow complexity. Their costs are also visible: more indirection, more classes, global state management and compatibility layers. Overall, the design favors modular handling of variable behavior while accepting controlled complexity in the infrastructure that coordinates Spack's main workflows.

