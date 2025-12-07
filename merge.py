import json

def deep_merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        result = dict(a)
        for k, v in b.items():
            if k in result:
                result[k] = deep_merge(result[k], v)
            else:
                result[k] = v
        return result
    elif isinstance(a, list) and isinstance(b, list):
        # Concatenate and deduplicate by value
        return a + [item for item in b if item not in a]
    else:
        # Prefer b's value (svg_system_config.json) for override
        return b

with open("config/system_config.json", "r", encoding="utf-8") as f1, \
     open("config/svg_system_config.json", "r", encoding="utf-8") as f2:
    system_config = json.load(f1)
    svg_config = json.load(f2)

merged = deep_merge(system_config, svg_config)

with open("config/system_config.json", "w", encoding="utf-8") as fout:
    json.dump(merged, fout, indent=2)
print("Merged svg_system_config.json into system_config.json")
