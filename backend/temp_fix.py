import re, os, glob

base_path = r'c:\projects\genai\AI Data Analyst Agent\frontend\src'
files = glob.glob(base_path + '/**/*.tsx', recursive=True)

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = re.sub(
        r'["`]http://localhost:8000([^"`]*)["`]', 
        r'`http://${window.location.hostname}:8000\1`', 
        content
    )
    
    if new_content != content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated {f}")
