"""Check bundled PE import/export compatibility for packaging diagnostics."""
from pathlib import Path
import pefile

root = Path("dist/TelePutin/_internal")
files = {p.name.lower(): p for p in root.rglob("*") if p.suffix.lower() in (".dll", ".pyd")}
queue = [files[n] for n in ("qtcore.pyd", "pyside6.abi3.dll", "shiboken6.abi3.dll") if n in files]
seen = set()
exports = {}
while queue:
    path = queue.pop()
    if path in seen: continue
    seen.add(path)
    pe = pefile.PE(str(path), max_symbol_exports=100000)
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        name = entry.dll.decode().lower()
        if name not in files: continue
        target = files[name]
        queue.append(target)
        if target not in exports:
            lib = pefile.PE(str(target), max_symbol_exports=100000)
            exports[target] = {s.name for s in lib.DIRECTORY_ENTRY_EXPORT.symbols} if hasattr(lib, "DIRECTORY_ENTRY_EXPORT") else set()
        for symbol in entry.imports:
            if symbol.name and symbol.name not in exports[target]: print(path.name, "->", name, symbol.name.decode())
print("Checked", len(seen), "bundled libraries")
