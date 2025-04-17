#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path
from deepdiff import DeepDiff
import argparse
import sys
import difflib

DEFAULT_LOCAL_REPO = "../../../"
UPSTREAM_REPO_URL = "https://github.com/facebook/fboss.git"
CONFIG_DIR = "fboss/platform/configs"


def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None

def get_json_files(base_path, workspace_path=DEFAULT_LOCAL_REPO, platform_filter=None, config_filter=None):
    configs_path = Path(base_path) / CONFIG_DIR
    if not configs_path.exists():
        print(f"Directory not found: {configs_path}", file=sys.stderr)
        return []

    platform_is_prefix = platform_filter and platform_filter.endswith('*')
    if platform_is_prefix:
        platform_filter = platform_filter[:-1]

    json_files = []
    for root, _, files in os.walk(configs_path):
        root_path = Path(root)
        try:
            platform_dir = root_path.relative_to(configs_path).parts[0].lower()
            arista_platforms_path = Path(workspace_path) / "arista/platform"
            if not (arista_platforms_path / platform_dir).is_dir():
               continue
            if platform_filter and ((platform_is_prefix and not platform_dir.startswith(platform_filter.lower())) or
                                     (not platform_is_prefix and platform_dir != platform_filter.lower())):
                continue
        except (IndexError, ValueError):
            pass

        for file in files:
            if file.endswith('.json') and (not config_filter or file.lower().startswith(config_filter.lower())):
                json_files.append(str(root_path.relative_to(configs_path) / file))
    return sorted(json_files)

def format_diff(diff, local_json, upstream_json):
    formatted_diff = {}

    added_items = {}
    removed_items = {}

    if 'dictionary_item_added' in diff:
        added_items.update({
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                get_nested_value(upstream_json, '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]))
            for path in diff['dictionary_item_added']
        })

    if 'dictionary_item_removed' in diff:
        removed_items.update({
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                get_nested_value(local_json, '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]))
            for path in diff['dictionary_item_removed']
        })

    if 'iterable_item_added' in diff:
        added_items.update({
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                get_nested_value(upstream_json, '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]))
            for path in diff['iterable_item_added']
        })

    if 'iterable_item_removed' in diff:
        removed_items.update({
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                get_nested_value(local_json, '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]))
            for path in diff['iterable_item_removed']
        })

    if added_items:
        formatted_diff['added_in_upstream'] = added_items
    if removed_items:
        formatted_diff['removed_from_upstream'] = removed_items

    if 'values_changed' in diff:
        formatted_diff['value_changes'] = {
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                {'local': change['old_value'], 'upstream': change['new_value']}
            for path, change in diff['values_changed'].items()
        }

    if 'type_changes' in diff:
        formatted_diff['type_changes'] = {
            '.'.join(path.replace("root", "").replace("['", ".").replace("']", "").split('.')[1:]):
                {'local': {'value': change['old_value'], 'type': str(change['old_type'])},
                 'upstream': {'value': change['new_value'], 'type': str(change['new_type'])}}
            for path, change in diff['type_changes'].items()
        }

    return formatted_diff

def get_nested_value(obj, path):
    current = obj
    for part in path.split('.'):
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return None
    return current

def format_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=4).splitlines()
    return str(value).splitlines()

def print_formatted_diff(file_path, formatted_diff):
    print(f"==== Diff for file: {file_path} ====")

    if 'added_in_upstream' in formatted_diff:
        print("Added in upstream:")
        for key, value in formatted_diff['added_in_upstream'].items():
            print(f"  {key}: {value}")

    if 'removed_from_upstream' in formatted_diff:
        print("Removed from upstream:")
        for key, value in formatted_diff['removed_from_upstream'].items():
            print(f"  {key}: {value}")

    if 'value_changes' in formatted_diff:
        print("Value changes:")
        for key, change in formatted_diff['value_changes'].items():
            print(f"  {key}:")
            local_lines = format_value(change['local'])
            upstream_lines = format_value(change['upstream'])
            diff_lines = difflib.unified_diff(local_lines, upstream_lines, fromfile='local', tofile='upstream', lineterm='')
            for line in diff_lines:
                print(f"    {line}")

    if 'type_changes' in formatted_diff:
        print("Type changes:")
        for key, change in formatted_diff['type_changes'].items():
            print(f"  {key}:")
            local_val = f"{change['local']['value']} (type: {change['local']['type']})"
            upstream_val = f"{change['upstream']['value']} (type: {change['upstream']['type']})"
            local_lines = local_val.splitlines()
            upstream_lines = upstream_val.splitlines()
            diff_lines = difflib.unified_diff(local_lines, upstream_lines, fromfile='local', tofile='upstream', lineterm='')
            for line in diff_lines:
                print(f"    {line}")

    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description='Compare JSON configurations between local and upstream repositories.')
    parser.add_argument('--platform', help='Filter by platform directory (exact or prefix with *)')
    parser.add_argument('--config', help='Filter by config file prefix')
    parser.add_argument('--workspace', help='Path to the local repository workspace')
    args = parser.parse_args()

    local_repo_path = args.workspace if args.workspace else DEFAULT_LOCAL_REPO

    local_files = get_json_files(local_repo_path, local_repo_path, args.platform, args.config)

    if args.platform or args.config:
        filters = []
        if args.platform:
            filters.append(f"platform='{args.platform}' ({'prefix' if args.platform.endswith('*') else 'exact'} match)")
        if args.config:
            filters.append(f"config='{args.config}' (prefix match)")
        print(f"Filtering files with {' and '.join(filters)}", file=sys.stderr)

    with tempfile.TemporaryDirectory() as upstream_temp_dir:
        print(f"Cloning upstream repository into: {upstream_temp_dir}", file=sys.stderr)
        subprocess.run(["git", "clone", UPSTREAM_REPO_URL, upstream_temp_dir], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        upstream_files = get_json_files(upstream_temp_dir, local_repo_path, args.platform, args.config)
        common_files = set(local_files) & set(upstream_files)

        if not common_files:
            print("No common JSON files found.")
            return

        diffs_found = False
        for file_path in sorted(common_files):
            local_full_path = Path(local_repo_path) / CONFIG_DIR / file_path
            upstream_full_path = Path(upstream_temp_dir) / CONFIG_DIR / file_path

            local_json = load_json(local_full_path)
            upstream_json = load_json(upstream_full_path)

            if not local_json or not upstream_json:
                continue

            diff = DeepDiff(local_json, upstream_json, ignore_order=True).to_dict()

            if diff:
                diffs_found = True
                formatted_diff = format_diff(diff, local_json, upstream_json)
                print_formatted_diff(file_path, formatted_diff)

        if not diffs_found:
            print("No differences found.")

        print("Analysis complete", file=sys.stderr)

if __name__ == "__main__":
    main()
