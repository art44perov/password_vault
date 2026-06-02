import json
import csv
import os
from datetime import datetime
from io import StringIO, BytesIO

def create_backup(entries: list, backup_dir: str) -> str:
    os.makedirs(backup_dir, exist_ok=True)
    filename = f"vault_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(backup_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'entries': entries
        }, f, indent=2, ensure_ascii=False)
    
    return filepath

def export_json(entries: list) -> str:
    return json.dumps({
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'entries': entries
    }, indent=2, ensure_ascii=False)

def export_csv(entries: list) -> str:
    output = StringIO()
    if not entries:
        return ""
    
    fieldnames = ['title', 'username', 'password', 'url', 'description', 'category', 'tags']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for entry in entries:
        row = {k: entry.get(k, '') for k in fieldnames}
        if isinstance(row.get('tags'), list):
            row['tags'] = ','.join(row['tags'])
        writer.writerow(row)
    
    return output.getvalue()

def import_json(data: str) -> list:
    parsed = json.loads(data)
    if isinstance(parsed, dict) and 'entries' in parsed:
        return parsed['entries']
    if isinstance(parsed, list):
        return parsed
    return []

def import_csv(data: str) -> list:
    reader = csv.DictReader(StringIO(data))
    entries = []
    for row in reader:
        entry = dict(row)
        if 'tags' in entry and isinstance(entry['tags'], str):
            entry['tags'] = [t.strip() for t in entry['tags'].split(',') if t.strip()]
        entries.append(entry)
    return entries
