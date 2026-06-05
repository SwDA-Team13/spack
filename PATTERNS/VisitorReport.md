# Pattern 4: Visitor for package AST processing

**Pattern identified:** Visitor  
**Main file:** `lib/spack/spack/util/package_hash.py`

Spack uses Python AST visitors to process `package.py` files when computing package hashes. The object structure is the Python AST produced from package source code; it contains many node classes such as `ast.Module`, `ast.ClassDef`, `ast.FunctionDef`, `ast.Assign`, and `ast.If`. The visitor classes define operations over that structure without putting package-hash logic inside the AST node classes.

| Class / element | Line | Role / purpose | 
|---|---:|---|
| Python AST node classes | stdlib | Element structure visited by the concrete visitors. |
| `ast.NodeVisitor` / `ast.NodeTransformer` | stdlib | Visitor base interfaces used by Spack visitors. |
| `RemoveDocstrings` | 34 | Concrete visitor/transformer that removes docstrings from the AST. |
| `RemoveDirectives` | 62 | Concrete visitor/transformer that removes Spack directives and metadata not relevant to package hashing. |
| `TagMultiMethods` | 178 | Concrete visitor that records `@when`-decorated methods and their conditions. |
| `ResolveMultiMethods` | 236 | Concrete visitor/transformer that removes method implementations that cannot affect the current package hash. |
| `package_hash()` logic | 380-392 | Client/context: parses source code and applies the visitors in sequence. |

The pattern is used because Spack needs several operations over the same object structure: removing docstrings, removing directives, detecting conditional multi-methods, and resolving which implementations may affect the hash. These operations depend on concrete AST node types, but the AST node classes are not Spack classes and should not be modified. This matches the Visitor problem from the course: many operations must be performed over an object structure, and putting all operations inside the elements would pollute those elements.

The visitor classes keep package-hash operations separated from the traversal mechanism. For example, `RemoveDirectives` defines behavior for nodes such as expressions, assignments, loops, and class definitions, while `TagMultiMethods` focuses on function definitions. Each operation is localized in a visitor class, and `package_hash()` composes them when preparing the source representation used for hashing.

An alternative would be to manually walk the AST with one large recursive function containing many `isinstance` checks. That could be simpler for a very small operation, but it would mix traversal logic with all package-hash transformations and become harder to extend. Another alternative would be several independent `ast.walk()` loops. That would be straightforward, but each loop would repeat traversal decisions and state handling. The Visitor approach makes the operations more modular, at the cost of several small classes and some dependence on the AST node structure.

## Code references to link later

| File | Line(s) | Element |
|---|---:|---|
| `util/package_hash.py` | 34 | `class RemoveDocstrings(ast.NodeTransformer)` |
| `util/package_hash.py` | 52-59 | `visit_FunctionDef`, `visit_ClassDef`, `visit_Module` |
| `util/package_hash.py` | 62 | `class RemoveDirectives(ast.NodeTransformer)` |
| `util/package_hash.py` | 94-170 | visitor methods for expressions, assignments, control flow, and class definitions |
| `util/package_hash.py` | 178 | `class TagMultiMethods(ast.NodeVisitor)` |
| `util/package_hash.py` | 222-233 | `TagMultiMethods.visit_FunctionDef()` |
| `util/package_hash.py` | 236 | `class ResolveMultiMethods(ast.NodeTransformer)` |
| `util/package_hash.py` | 312-330 | `ResolveMultiMethods.visit_FunctionDef()` |
| `util/package_hash.py` | 380-392 | package source is parsed and visitors are applied |
