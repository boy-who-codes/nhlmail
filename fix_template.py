
path = r"d:\00wrap\meip\templates\web\batch_detail.html"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    stripped = line.strip()
    # Check for the broken start
    if "{% if result.catch_all == 'Yes' or result.catch_all == 'Possible' or result.is_catch_all" in line and not "%}" in line:
        # Check if next line is the closing %}
        if i + 1 < len(lines) and "%}" in lines[i+1]:
            # Merge them
            indent = line[:line.find("{%")]
            merged = indent + "{% if result.catch_all == 'Yes' or result.catch_all == 'Possible' or result.is_catch_all %}\n"
            new_lines.append(merged)
            skip_next = True # Skip the next line which was just %}
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("File patched.")
