# Pattern 4: Composite for package staging

**Pattern identified:** Composite  
**Main files:** `lib/spack/spack/stage.py`, `lib/spack/spack/package_base.py`

Spack uses `StageComposite` to manage package staging when a package needs several related stages: the main source stage, optional resource stages, and optional patch stages. Instead of making client code handle this list directly, Spack groups the stages in one object and exposes the main operations used for a normal stage.

| Class / element | Line | Role / purpose |
|---|---:|---|
| `AbstractStage` | `stage.py:221` | Component interface: defines the common operations expected from stage-like objects. |
| `Stage` | `stage.py:381` | Leaf: represents a normal source or archive stage. |
| `DevelopStage` | `stage.py:968` | Leaf: represents a development source stage. |
| `StageComposite` | `stage.py:836` | Composite: stores several stages and applies operations to all of them. |
| `StageComposite._stages` | `stage.py:842` | Children collection used by the composite. |
| `PackageBase._make_stages()` | `package_base.py:1192` | Client logic: creates the composite and adds source, resource, and patch stages. |
| `PackageBase.stage` | `package_base.py:1267` | Client access point: returns the staging object used by package operations. |

The pattern is used because a package staging area may be single or composite, but the package workflow should not repeat the same loops every time it creates, fetches, expands, restages, caches, or destroys sources. `StageComposite` solves this by forwarding operations such as `create()`, `fetch()`, `check()`, `expand_archive()`, `restage()`, `destroy()`, and `cache_local()` to each contained stage.

This keeps the client code simple: package operations call `self.stage.create()`, `self.stage.fetch()`, or `self.stage.expand_archive()` without checking whether the package has only a source archive or also resources and remote patches. Properties that belong to the root source, such as `source_path`, `path`, `archive_file`, and `requires_patch_success`, are forwarded to the first stage in the composite.

An alternative would be to store a plain list of stages in `PackageBase` and iterate over it wherever staging operations are needed. That would be simpler as a data structure, but it would spread the same control logic across several methods and expose staging internals to clients. Another alternative would be separate methods for root stages, resources, and patch stages. This would make each case explicit, but it would duplicate lifecycle logic and make future changes harder to keep consistent.

The Composite approach centralizes the group behavior in `StageComposite`. The main trade-off is that it adds one extra wrapper object and, in this Python implementation, the composite does not formally inherit from `AbstractStage`; it follows the same operational interface by exposing compatible methods.

## Code references to link later

| File | Line(s) | Element |
|---|---:|---|
| `stage.py` | 221 | `class AbstractStage` |
| `stage.py` | 305-341 | common stage operations such as `create`, `destroy`, `fetch`, `restage` |
| `stage.py` | 381 | `class Stage(AbstractStage)` |
| `stage.py` | 836 | `class StageComposite` |
| `stage.py` | 841-842 | `StageComposite.__init__` stores child stages |
| `stage.py` | 851-857 | `append()` and `extend()` add children to the composite |
| `stage.py` | 871-879 | context manager operations delegated to all stages |
| `stage.py` | 882-915 | lifecycle operations delegated to all stages |
| `stage.py` | 937-965 | root-stage properties forwarded to the first child |
| `stage.py` | 968 | `class DevelopStage(AbstractStage)` |
| `package_base.py` | 1192 | `PackageBase._make_stages()` |
| `package_base.py` | 1222-1265 | source, resource, and patch stages are added to the composite |
| `package_base.py` | 1267-1279 | `PackageBase.stage` returns the composite staging object |
| `package_base.py` | 1656-1680 | package workflow uses `self.stage` without handling the child list directly |
