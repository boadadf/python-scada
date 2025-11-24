import os

LICENSE_FILE = "license_header.txt"
PROJECT_ROOT = "openscada_lite"

with open(LICENSE_FILE, "r", encoding="utf-8") as f:
    license_text = f.read()

for root, dirs, files in os.walk(PROJECT_ROOT):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Avoid duplicating the header
            if not content.startswith(license_text):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(license_text + "\n" + content)
