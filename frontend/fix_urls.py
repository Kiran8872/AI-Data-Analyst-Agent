
import os
import re

directory = "src"
pattern = re.compile(r"http://\$\{window\.location\.hostname\}:8000")
replacement = r"${process.env.NEXT_PUBLIC_API_URL || \"http://localhost:8000\"}"

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith(".tsx"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            new_content = pattern.sub(replacement, content)
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new_content)
                print(f"Updated {filepath}")

