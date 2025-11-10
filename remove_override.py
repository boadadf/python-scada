import os
import re

BASE_DIR = "./openscada_lite"  # Change if needed

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove standalone @override decorator lines
            content = re.sub(r"^\s*@override\s*$\n?", "", content, flags=re.MULTILINE)

            # Remove 'override' from typing imports but keep other imports
            def remove_override_from_import(match):
                imports = match.group(1).split(",")
                imports = [imp.strip() for imp in imports if imp.strip() != "override"]
                if not imports:
                    return ""  # remove entire line if nothing left
                return f"from typing import {', '.join(imports)}"

            content = re.sub(
                r"^from\s+typing\s+import\s+([^\n]+)",
                remove_override_from_import,
                content,
                flags=re.MULTILINE
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"Processed {path}")

