with open(r"d:\00wrap\meip\templates\web\batch_detail.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 200 <= i+1 <= 220:
             print(f"{i+1}: {line}", end='')
