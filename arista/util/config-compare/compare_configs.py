#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path
from deepdiff import DeepDiff
from datetime import datetime

# Hardcoded or configurable paths/URLs
LOCAL_REPO = "../../../"
UPSTREAM_REPO_URL = "https://github.com/facebook/fboss.git"
CONFIG_DIR = "fboss/platform/configs"

def parse_path(path):
    path = path.replace("root", "", 1)
    path = path.replace("['", ".").replace("']", "")
    return path.lstrip('.')

def get_nested_value(obj, path):
    current = obj
    for part in path.split('.'):
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return None
    return current

def convert_to_serializable(obj):
    if hasattr(obj, 'items'):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, set, tuple)) or (hasattr(obj, '__iter__') and not isinstance(obj, (str, dict))):
        return [convert_to_serializable(i) for i in obj]
    return obj

def format_diff(diff_dict, local_json, upstream_json):
    result = {}
    if 'dictionary_item_added' in diff_dict:
        added = {}
        for path in diff_dict['dictionary_item_added']:
            clean_path = parse_path(path)
            parent_path = '.'.join(clean_path.split('.')[:-1])
            key = clean_path.split('.')[-1]
            if parent_path:
                parent = get_nested_value(upstream_json, parent_path)
                if isinstance(parent, dict):
                    added[clean_path] = parent[key]
            else:
                added[clean_path] = upstream_json[key]
        if added:
            result['added_in_upstream'] = added

    if 'dictionary_item_removed' in diff_dict:
        removed = {}
        for path in diff_dict['dictionary_item_removed']:
            clean_path = parse_path(path)
            parent_path = '.'.join(clean_path.split('.')[:-1])
            key = clean_path.split('.')[-1]
            if parent_path:
                parent = get_nested_value(local_json, parent_path)
                if isinstance(parent, dict):
                    removed[clean_path] = parent[key]
            else:
                removed[clean_path] = local_json[key]
        if removed:
            result['removed_from_upstream'] = removed

    if 'values_changed' in diff_dict:
        changes = {}
        for path, change in diff_dict['values_changed'].items():
            clean_path = parse_path(path)
            changes[clean_path] = {
                'local': change['old_value'],
                'upstream': change['new_value']
            }
        if changes:
            result['value_changes'] = changes

    if 'type_changes' in diff_dict:
        type_changes = {}
        for path, change in diff_dict['type_changes'].items():
            clean_path = parse_path(path)
            type_changes[clean_path] = {
                'local': {
                    'value': change['old_value'],
                    'type': str(change['old_type'])
                },
                'upstream': {
                    'value': change['new_value'],
                    'type': str(change['new_type'])
                }
            }
        if type_changes:
            result['type_changes'] = type_changes

    return result

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_json_files(base_path):
    json_files = []
    configs_path = Path(base_path) / CONFIG_DIR

    if not configs_path.exists():
        print(f"Directory not found: {configs_path}")
        return []

    for root, _, files in os.walk(configs_path):
        for file in files:
            if file.endswith('.json'):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(configs_path)
                json_files.append(str(rel_path))
    return sorted(json_files)

def main():
    output_dir = Path('diffs')
    output_dir.mkdir(exist_ok=True)
    print(f"\nDiffs will be saved to: {output_dir.absolute()}")

    with tempfile.TemporaryDirectory() as tmp_upstream_dir:
        print(f"Cloning {UPSTREAM_REPO_URL} into {tmp_upstream_dir} ...")
        subprocess.run(["git", "clone", UPSTREAM_REPO_URL, tmp_upstream_dir], check=True)
        print("Clone complete.\n")

        local_files = get_json_files(LOCAL_REPO)
        upstream_files = get_json_files(tmp_upstream_dir)

        common_files = set(local_files) & set(upstream_files)

        print("Comparing files...")
        for file_path in sorted(common_files):
            local_json = load_json(Path(LOCAL_REPO) / CONFIG_DIR / file_path)
            upstream_json = load_json(Path(tmp_upstream_dir) / CONFIG_DIR / file_path)

            if local_json is None or upstream_json is None:
                continue

            diff = DeepDiff(local_json, upstream_json, ignore_order=True)
            if diff:
                print(f"Found differences in: {file_path}")

                diff_file = output_dir / file_path
                diff_file.parent.mkdir(parents=True, exist_ok=True)

                formatted_diff = format_diff(diff.to_dict(), local_json, upstream_json)
                with open(diff_file.with_suffix('.diff.json'), 'w') as f:
                    json.dump(formatted_diff, f, indent=2)

        print("\nAll comparisons complete. Temporary clone removed.")

if __name__ == "__main__":
    main()
