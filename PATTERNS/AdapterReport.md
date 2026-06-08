# Pattern 3: Adapter for legacy compiler access

**Pattern identified:** Adapter  
**Main files:** `lib/spack/spack/compilers/adaptor.py`, `lib/spack/spack/package_base.py`

Spack uses `CompilerAdaptor` to preserve the old `Package.compiler` interface while compiler information is now represented through compiler dependency specs, such as the virtual C, CXX, and Fortran compiler dependencies. This matches the Adapter pattern: the available provider has useful data, but its interface is not the one expected by existing client code.

| Class / element | Line | Role / purpose |
|---|---:|---|
| `Package.compiler` | `package_base.py:547` | Target interface expected by legacy package code, accessed as `self.compiler`. |
| `CompilerAdaptor` | `adaptor.py:19` | Adapter: exposes old compiler-style properties using compiler dependency specs internally. |
| `Languages` | `adaptor.py:13` | Defines the compiler language keys used by the adapter. |
| `spack.spec.Spec` compiler dependencies | `adaptor.py:25`, `218-223` | Adaptee data: concrete compiler specs selected for C, CXX, and Fortran. |
| `DeprecatedCompiler` | `adaptor.py:209` | Descriptor that creates the adapter when `Package.compiler` is accessed. |
| `DeprecatedCompiler.factory()` | `adaptor.py:213` | Collects compiler dependencies from the package spec and returns a `CompilerAdaptor`. |
| Package code using `self.compiler` | `mixins.py:118` | Client example that continues to use the old interface. |

The pattern is used because Spack changed how compiler information is modeled, but existing package code may still ask for attributes such as `self.compiler.name`, `self.compiler.cc`, `self.compiler.cxx11_flag`, or `self.compiler.openmp_flag`. Rewriting all clients at once would be risky and expensive. The adapter lets that code keep using the old interface while internally retrieving information from the newer compiler dependency objects.

`CompilerAdaptor` translates old-style requests into calls on the appropriate compiler package. If a requested language compiler is not present, the adapter raises an error instead of silently returning incorrect data.

An alternative would be to remove `Package.compiler` and update every client to use `self.spec[language]` or direct compiler dependencies. This would avoid compatibility code, but it would require many coordinated changes and could break packages that still depend on the old interface.

## Code references to link later

| File | Line(s) | Element |
|---|---:|---|
| `compilers/adaptor.py` | 13 | `class Languages` |
| `compilers/adaptor.py` | 19 | `class CompilerAdaptor` |
| `compilers/adaptor.py` | 24-31 | `CompilerAdaptor.__init__` stores the compiled spec and compiler specs |
| `compilers/adaptor.py` | 33-42 | helper methods validate language availability and forward attributes |
| `compilers/adaptor.py` | 44-202 | old compiler-style properties exposed by the adapter |
| `compilers/adaptor.py` | 209 | `class DeprecatedCompiler` |
| `compilers/adaptor.py` | 213-224 | `DeprecatedCompiler.factory()` builds and returns `CompilerAdaptor` |
| `package_base.py` | 547 | `compiler = DeprecatedCompiler()` |
| `mixins.py` | 118 | client example using `pkg.compiler.name` |
