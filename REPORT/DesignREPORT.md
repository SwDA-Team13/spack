# Software Design Analysis

## Dependencies

The dependency analysis was carried out using two complementary views of the Spack codebase. The first view concerns code dependencies, reconstructed from Python import statements in the source code. The analysis script parses Python files with the standard `ast` module, extracts `import` and `from ... import ...` statements, and maps local modules to the files that implement them. In this view, a directed edge `A -> B` means that file `A` imports a local module implemented by file `B`.

The second view concerns knowledge dependencies, reconstructed from Git co-change. Here, two files are considered related when they are modified in the same non-merge commit. This relation is not directional: it does not show that one file calls or imports another one, but that developers historically had to change them together. This is useful because maintenance dependencies can exist even when the import graph does not show a direct relationship.

The import analysis was preferred over plain text search because it follows Python syntax and avoids treating comments or unrelated text as dependencies. The co-change analysis was kept separate because Git history gives a different kind of evidence: it does not describe how modules call each other, but it can show where developers repeatedly needed to coordinate changes.

Both analyses used the same scope: `bin/spack`, `lib/spack/spack`, and `lib/spack/llnl`. Tests, mock repositories, vendored code, caches, generated files, virtual environments, and build folders were excluded. For co-change, commits touching more than 50 selected files were skipped to reduce the effect of broad mechanical changes. The import analysis considered 327 files and found 1984 local import edges. The co-change analysis scanned 40771 non-merge commits, found 5551 commits touching selected source files, skipped 27 broad commits, and used 5524 commits for pair counting.

Using both views gives a more complete picture of dependency structure. Imports show explicit source-level coupling and identify modules that statically depend on many collaborators. Co-change shows maintenance coupling and identifies files that tend to evolve together because they participate in the same workflows or share design knowledge. The comparison is therefore more informative than either analysis alone.

### Code Dependencies

Files with many outgoing local imports usually act as coordination points. They assemble behavior from several local modules and therefore require broader architectural knowledge to understand or modify.

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

The highest outgoing values are consistent with Spack's architecture. `package.py`, `package_base.py`, and `spec.py` belong to the package/spec model. `solver/asp.py` is related to concretization, while `new_installer.py`, `installer.py`, and `environment/environment.py` coordinate installation and environment workflows. This does not automatically indicate poor design, because these files have broad responsibilities by nature. It does indicate, however, that changes in these areas may require knowledge of several neighboring modules.

This interpretation is important because dependency counts alone are not a quality judgment. In a package manager, some modules necessarily connect package definitions, dependency solving, installation planning, source retrieval, and environment management. The relevant design observation is that these files are likely to have higher cognitive load and should be treated as architectural coordination points.

Incoming imports show the opposite side of the dependency graph: files that are used by many local clients. These files are often shared utilities, common abstractions, or services that support many workflows.

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

The most imported files are common infrastructure and core abstractions: terminal output, error handling, filesystem utilities, configuration, repositories, command argument handling, the install store, and `Spec`. Their high fan-in is expected because they provide facilities reused across the project. It also means that their interfaces should remain stable, since changes can affect many clients.

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

The analysis found 53 files with zero outgoing local imports and 92 files with zero incoming local imports. This should not be interpreted as lack of importance. Low dependency count can indicate narrow platform-specific code, package marker files, dynamically loaded commands, or small leaf modules.

This also explains why low-dependency files were considered separately instead of being treated as unimportant modules. Some files may be invoked through command discovery, package loading, or platform-specific execution paths rather than through direct imports visible in this analysis.

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

These pairs mainly involve package modeling, concretization, build environments, staging, fetching, binary distribution, and command workflows. This is coherent with Spack's domain: installing software requires package metadata, concrete specs, source preparation, binary cache behavior, and command behavior to evolve together. The co-change graph therefore confirms that the most active maintenance relations are concentrated around Spack's central package-management workflow.

Several high co-change pairs are also consistent with direct imports. `solver/asp.py` imports `spec.py`; `package.py` imports `spec.py`; `concretize.py` imports `spec.py`; `database.py` imports `spec.py`; `stage.py` imports `fetch_strategy.py`. These cases show both structural and historical dependency. The files are connected in the source code, and Git history confirms that they often had to be maintained together.

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

These pairs reveal knowledge dependencies that are not visible as direct imports. `package.py` and `stage.py` both participate in source preparation and installation. Command modules can co-change with package or database modules because they implement the user-facing side of the same workflows. The opposite situation also exists: some direct imports have little or no co-change, especially when a file imports a stable utility. This means that imports and co-change should be read together. Imports describe static structure, while co-change highlights historical maintenance coupling.

From a design perspective, the inconsistent pairs are useful because they identify relations that may deserve documentation, integration tests, or architectural discussion. A developer modifying one file may need to understand another related file even if the dependency is not expressed through an import statement.

The opposite case is also informative. A direct import with little or no co-change usually indicates a stable provider, such as a utility module or a common service, whose interface has not forced frequent joint changes. This does not remove the structural dependency, but it suggests that the relation is less active from a maintenance point of view.

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

Spack uses Strategy for source fetching because the general task is stable, while the concrete behavior depends on the source type. Archive URLs, cached archives, Git, Subversion, Mercurial, S3, GCS, Go resources, and OCI registry content require different operations, but the rest of the system expects the same lifecycle: fetch, check, expand, reset, and archive.

`FetchStrategy` defines the common interface, while concrete strategies localize protocol-specific behavior and validation rules. `PackageBase.fetcher` selects the appropriate fetcher for a package version, and `Stage` stores and invokes it. The registration and selection logic, based on decorators and helper functions, lets the client workflow remain stable while the concrete fetching mechanism varies.

The helper functions involved in strategy selection connect package metadata or URL schemes to concrete strategy objects. This keeps selection separate from execution. After the fetcher has been chosen, the stage can use the common interface without embedding protocol decisions in the staging workflow.

An alternative would be a single fetcher with many conditional branches. That would reduce the number of classes, but it would couple unrelated protocols in one module and make every new source type modify central logic. The current design has more classes and some selection logic, but it separates variation points and is easier to extend.

This pattern is especially visible because the concrete strategies are not superficial subclasses. They represent different fetching mechanisms and different validation rules. For instance, archive fetching, cache reuse, version-control fetching, cloud storage fetching, and expanded-file verification are separate concerns. Keeping them behind the same lifecycle lets `Stage` work with a fetcher without knowing which protocol-specific behavior is being executed.

### Singleton: Shared Global Services

| Class | Line | Role |
|---|---:|---|
| `Singleton` | `lang.py:713` | Singleton controller with lazy instance creation. |
| `Configuration` / `CONFIG` | `config.py:514`, `1563` | Shared configuration service. |
| `Store` / `STORE` | `store.py:135`, `299` | Shared installation store. |
| `RepoPath` / `PATH` | `repo.py:697`, `2104` | Shared package repository path. |
| `FileCache` / `MISC_CACHE` | `file_cache.py:88`, `caches.py:33` | Shared cache for persistent Spack data. |
| `FsCache` / `FETCH_CACHE` | `fetch_strategy.py:1786`, `caches.py:68` | Shared cache for downloaded sources. |

Spack uses a Python-specific Singleton wrapper for shared services that should have one main instance during normal execution. Instead of using the textbook form with a private constructor, `Singleton` stores a factory function, creates the real object lazily, and keeps the created instance for later access.

The pattern is used for process-wide concepts such as configuration, the installation store, repository paths, and caches. If different parts of the program freely created separate instances of these services, they could observe inconsistent global state. Lazy creation also avoids initializing these services before they are needed.

An alternative would be eager module-level objects. This would be simpler to read, but it could make imports heavier and introduce initialization-order problems. Another alternative would be explicit dependency passing. That would make dependencies clearer and reduce global state, but it would require changing many call sites and would make common operations more verbose. The chosen design gives compact access to shared services, with the trade-off that tests and context changes must reset global state carefully.

In this case, the Singleton role is not limited to a single class instance in isolation. The wrapper provides a consistent access point for several shared services, including configuration, store, repository path, and caches. This matches the course idea of controlling access to a unique object, adapted to Python through lazy factories and module-level variables.

### Adapter: Legacy Compiler Access

| Class | Line | Role |
|---|---:|---|
| `Package.compiler` | `package_base.py:547` | Target interface expected by legacy package code. |
| `CompilerAdaptor` | `adaptor.py:19` | Adapter exposing old compiler-style properties. |
| `Languages` | `adaptor.py:13` | Language keys used by the adapter. |
| Compiler dependency specs | `adaptor.py:25`, `218-223` | Adaptee data used internally by the adapter. |
| `DeprecatedCompiler` | `adaptor.py:209` | Descriptor that creates the adapter on access. |
| `DeprecatedCompiler.factory()` | `adaptor.py:213` | Factory method collecting compiler specs and returning the adapter. |

Spack uses Adapter to preserve the old `Package.compiler` interface while compiler information is now represented through compiler dependency specs. The target interface is the property expected by existing package code. `CompilerAdaptor` is the adapter, and the concrete compiler specs are the adaptee data used internally.

The pattern is used because existing package code may still ask for old-style compiler attributes. Rewriting all clients at once would be risky and expensive. The adapter translates those requests into the newer compiler dependency model and raises an error when a requested language compiler is not available, avoiding silent incorrect results.

An alternative would be to remove `Package.compiler` and update every client to use compiler dependencies directly. This would make the model cleaner and reduce compatibility code, but it would require many coordinated changes and could break packages that still depend on the old interface. Another alternative would be to duplicate compiler information in both old and new forms, but that would risk inconsistency. The adapter centralizes the translation in one place.

The design is therefore mainly a compatibility solution. The old package-facing interface remains available, while the adapter obtains the actual data from the newer dependency representation. This avoids spreading migration code through package clients and keeps the translation close to the compiler access mechanism.

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

Spack uses Composite for package staging because a package may require one stage or several related stages. A build can involve the main source stage, resource stages, and patch stages. `StageComposite` groups these stage objects and forwards lifecycle operations such as create, fetch, check, expand, restage, cache, and destroy to all contained stages.

The client does not need to know how many stages are present. Package operations can call the staging object directly, while the composite handles iteration over children. Properties that belong to the root source are forwarded to the first contained stage, including values such as source path, archive file, and patch-success requirements. This matches the Composite idea of treating a group of objects through an interface similar to the individual objects.

An alternative would be to keep a plain list of stages in `PackageBase` and iterate over it wherever staging operations are needed. That would be simpler as a data structure, but it would spread lifecycle logic across several methods and expose staging internals to clients. Separate methods for root, resource, and patch stages would be explicit, but would duplicate behavior. Composite centralizes group behavior, with the trade-off of one additional wrapper.

The grouping is created in `PackageBase._make_stages()`, where Spack builds the main source stage, adds needed resource stages, and includes patch stages when remote patches must be fetched. The result is returned through `PackageBase.stage`, so later package operations work with one staging object instead of manually coordinating each stage category.

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

Spack uses Visitor through Python's AST visitor infrastructure when processing package source files for package hashing. The object structure is the parsed Python syntax tree, composed of node types such as modules, classes, functions, assignments, and conditionals. The operations are Spack-specific transformations and analyses over that structure.

The pattern is useful because Spack needs several operations over the same AST: removing docstrings, removing directives and metadata not relevant to hashing, detecting conditional multi-methods, and resolving which implementations can affect the current hash. These operations depend on node types, but the AST node classes are part of Python and should not contain Spack-specific hashing logic.

An alternative would be a manual recursive traversal with many type checks. That could be simpler for a small operation, but it would mix traversal logic with all package-hash transformations. Another alternative would be several independent `ast.walk()` loops, but each loop would repeat traversal decisions and state handling. The Visitor approach keeps the operations more modular, with the cost of several small visitor classes.

The concrete visitors also separate different reasons for traversing the same object structure. `RemoveDocstrings`, `RemoveDirectives`, `TagMultiMethods`, and `ResolveMultiMethods` each focus on a distinct package-hash concern. The client logic can parse the source and apply these visitors in sequence instead of embedding all cases in one large traversal.

## Summary

The dependency analysis shows a dense architectural core around packages, specs, concretization, installation, staging, fetching, configuration, and command workflows. Import dependencies expose explicit structural coupling: workflow modules have many outgoing imports, while shared utilities and abstractions have high incoming imports. Co-change dependencies expose historical maintenance coupling: files involved in the same workflow often evolve together even without direct imports. The inconsistent pairs are important because they reveal design knowledge that the import graph alone does not show.

This is also why the dependency results are useful for architecture diagrams: they identify both explicit module relations and less visible maintenance relations.

The pattern analysis shows that Spack uses design patterns pragmatically. Strategy separates source-fetching variants behind a common lifecycle. Singleton controls access to shared process-wide services. Adapter preserves compatibility while the compiler model evolves. Composite lets package staging handle a group of stages through one staging object. Visitor structures AST-based package hashing without modifying Python AST classes. Overall, these patterns support extensibility, compatibility, and control of workflow complexity, while accepting trade-offs such as more classes, global state management, wrappers, and compatibility layers.

Together, the dependency and pattern analyses describe a design centered on complex package-management workflows. Spack is not free from coupling, but much of the coupling is concentrated around responsibilities that are central to its domain. The detected patterns help organize this complexity by separating variable behavior, centralizing shared services, and hiding repeated workflow logic behind stable interfaces.
