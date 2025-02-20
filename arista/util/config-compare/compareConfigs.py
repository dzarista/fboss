#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
from pathlib import Path
from deepdiff import DeepDiff
import textwrap
import argparse
import sys

LOCAL_REPO = "../../../"
UPSTREAM_REPO_URL = "https://github.com/facebook/fboss.git"
CONFIG_DIR = "fboss/platform/configs"

def parse_path(path):
    """Convert a DeepDiff path to dot notation."""
    path = path.replace("root", "", 1)
    path = path.replace("['", ".").replace("']", "")
    return path.lstrip('.')

def get_nested_value(obj, path):
    """Retrieve a nested value from a dict given a dot-notated path."""
    current = obj
    for part in path.split('.'):
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return None
    return current

def format_diff(diff_dict, local_json, upstream_json):
    """
    Reformat DeepDiff output into a structured dictionary.
    Keys include: added_in_upstream, removed_from_upstream,
                  value_changes, and type_changes.
    """
    result = {}

    # Items added in upstream
    if 'dictionary_item_added' in diff_dict:
        added = {}
        for path in diff_dict['dictionary_item_added']:
            clean_path = parse_path(path)
            parent_path = '.'.join(clean_path.split('.')[:-1])
            key = clean_path.split('.')[-1]
            if parent_path:
                parent = get_nested_value(upstream_json, parent_path)
                if isinstance(parent, dict):
                    added[clean_path] = parent.get(key, None)
            else:
                added[clean_path] = upstream_json.get(key, None)
        if added:
            result['added_in_upstream'] = added

    # Items removed from upstream
    if 'dictionary_item_removed' in diff_dict:
        removed = {}
        for path in diff_dict['dictionary_item_removed']:
            clean_path = parse_path(path)
            parent_path = '.'.join(clean_path.split('.')[:-1])
            key = clean_path.split('.')[-1]
            if parent_path:
                parent = get_nested_value(local_json, parent_path)
                if isinstance(parent, dict):
                    removed[clean_path] = parent.get(key, None)
            else:
                removed[clean_path] = local_json.get(key, None)
        if removed:
            result['removed_from_upstream'] = removed

    # Value changes
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

    # Type changes
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
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def get_json_files(base_path, platform_filter=None, config_filter=None):
    """
    Return a sorted list of JSON files (relative paths) from CONFIG_DIR
    within the given base path, filtered by platform and config if provided.
    
    Args:
        base_path: Base repository path
        platform_filter: If provided, only include directories matching this pattern
                         (exact match, or prefix match if ends with *)
        config_filter: If provided, only include files starting with this string
    """
    json_files = []
    configs_path = Path(base_path) / CONFIG_DIR

    if not configs_path.exists():
        print(f"Directory not found: {configs_path}", file=sys.stderr)
        return []

    platform_is_prefix = False
    
    if platform_filter and platform_filter.endswith('*'):
        platform_filter = platform_filter[:-1]  # Remove the *
        platform_is_prefix = True
    
    platform_filter_lower = platform_filter.lower() if platform_filter else None
    config_filter_lower = config_filter.lower() if config_filter else None

    for root, _, files in os.walk(configs_path):
        root_path = Path(root)
        
        if platform_filter_lower:
            try:
                platform_dir = root_path.relative_to(configs_path).parts[0]
                platform_dir_lower = platform_dir.lower()
                
                if platform_is_prefix:
                    if not platform_dir_lower.startswith(platform_filter_lower):
                        continue
                else:
                    if platform_dir_lower != platform_filter_lower:
                        continue
            except (IndexError, ValueError):
                pass
        
        for file in files:
            if not file.endswith('.json'):
                continue
                
            if config_filter_lower and not file.lower().startswith(config_filter_lower):
                continue
                    
            full_path = root_path / file
            rel_path = full_path.relative_to(configs_path)
            json_files.append(str(rel_path))
    
    return sorted(json_files)

def format_value(value, indent=4):
    """Format a value for display, with proper indentation for objects/arrays."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=indent)
    return str(value)

def side_by_side(left, right, width=40, separator="│", include_header=False):
    """Format two strings side by side.
    
    Args:
        left: Left side content
        right: Right side content
        width: Width of each column
        separator: Character to use as column separator
        include_header: Whether to include LOCAL/UPSTREAM headers
    """
    left_lines = format_value(left).split('\n')
    right_lines = format_value(right).split('\n')
    
    max_lines = max(len(left_lines), len(right_lines))
    left_lines += [''] * (max_lines - len(left_lines))
    right_lines += [''] * (max_lines - len(right_lines))
    
    wrapped_left = []
    for line in left_lines:
        if len(line) > width:
            wrapped_left.extend(textwrap.wrap(line, width))
        else:
            wrapped_left.append(line.ljust(width))
            
    wrapped_right = []
    for line in right_lines:
        if len(line) > width:
            wrapped_right.extend(textwrap.wrap(line, width))
        else:
            wrapped_right.append(line)
    
    max_wrapped_lines = max(len(wrapped_left), len(wrapped_right))
    wrapped_left += [''] * (max_wrapped_lines - len(wrapped_left))
    wrapped_right += [''] * (max_wrapped_lines - len(wrapped_right))
    
    result = []
    if include_header:
        result.append(f"{'LOCAL'.ljust(width)} {separator} {'UPSTREAM'}")
        result.append(f"{'-' * width} {separator} {'-' * width}")
    
    for l, r in zip(wrapped_left, wrapped_right):
        result.append(f"{l.ljust(width)} {separator} {r}")
    
    return result

def diff_to_text(file_path, diff_dict):
    """
    Convert the diff dictionary into a human-readable text format
    with sections for added, removed, value changes, and type changes.
    """
    lines = []
    lines.append(f"==== Diff for file: {file_path} ====")

    if 'added_in_upstream' in diff_dict:
        lines.append("Added in upstream:")
        for key, value in diff_dict['added_in_upstream'].items():
            lines.append(f"  {key}: {format_value(value)}")
        lines.append("")

    if 'removed_from_upstream' in diff_dict:
        lines.append("Removed from upstream:")
        for key, value in diff_dict['removed_from_upstream'].items():
            lines.append(f"  {key}: {format_value(value)}")
        lines.append("")

    indent = "    "
    width = 40
    separator = "│"
    
    if 'value_changes' in diff_dict:
        lines.append("Value changes:")
        lines.append(f"{indent}{'LOCAL'.ljust(width)} {separator} {'UPSTREAM'}")
        lines.append(f"{indent}{'-' * width} {separator} {'-' * width}")
        lines.append("")
        
        for key, change in diff_dict['value_changes'].items():
            lines.append(f"  {key}:")
            comparison = side_by_side(change['local'], change['upstream'], include_header=False)
            for comp_line in comparison:
                lines.append(f"{indent}{comp_line}")
            lines.append("")

    if 'type_changes' in diff_dict:
        lines.append("Type changes:")
        lines.append(f"{indent}{'LOCAL'.ljust(width)} {separator} {'UPSTREAM'}")
        lines.append(f"{indent}{'-' * width} {separator} {'-' * width}")
        lines.append("")
        
        for key, change in diff_dict['type_changes'].items():
            lines.append(f"  {key}:")
            local_val = f"{change['local']['value']} (type: {change['local']['type']})"
            upstream_val = f"{change['upstream']['value']} (type: {change['upstream']['type']})"
            comparison = side_by_side(local_val, upstream_val, include_header=False)
            for comp_line in comparison:
                lines.append(f"{indent}{comp_line}")
            lines.append("")

    lines.append("-" * 40)
    lines.append("")
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Compare JSON configurations between local and upstream repositories.')
    parser.add_argument('--platform', help='Filter by platform directory (exact match, or prefix match if ends with *)')
    parser.add_argument('--config', help='Filter by config file prefix')
    args = parser.parse_args()
    
    local_files = get_json_files(LOCAL_REPO, args.platform, args.config)
    
    if args.platform or args.config:
        filter_msg = []
        if args.platform:
            filter_type = "prefix" if args.platform.endswith('*') else "exact"
            filter_msg.append(f"platform='{args.platform}' ({filter_type} match)")
        if args.config:
            filter_msg.append(f"config='{args.config}' (prefix match)")
        print(f"Filtering files with {' and '.join(filter_msg)}", file=sys.stderr)
    
    with tempfile.TemporaryDirectory() as upstream_temp_dir:
        print(f"Cloning upstream repository into temporary directory: {upstream_temp_dir}", file=sys.stderr)
        subprocess.run(["git", "clone", UPSTREAM_REPO_URL, upstream_temp_dir], check=True, 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        upstream_files = get_json_files(upstream_temp_dir, args.platform, args.config)
        common_files = set(local_files) & set(upstream_files)

        if not common_files:
            print("No common JSON files found between local and upstream repositories.")
            return

        diffs_found = False
        diff_lines = []
        diff_lines.append("Diffs between local and upstream repositories")
        diff_lines.append("=" * 50)
        diff_lines.append("")
        for file_path in sorted(common_files):
            local_json = load_json(Path(LOCAL_REPO) / CONFIG_DIR / file_path)
            upstream_json = load_json(Path(upstream_temp_dir) / CONFIG_DIR / file_path)
            if local_json is None or upstream_json is None:
                continue

            diff = DeepDiff(local_json, upstream_json, ignore_order=True)
            if diff:
                diffs_found = True
                formatted_diff = format_diff(diff.to_dict(), local_json, upstream_json)
                diff_lines.append(diff_to_text(file_path, formatted_diff))

        if diffs_found:
            print("\n".join(diff_lines))
        else:
            print("No differences found between local and upstream repositories.")

        print(f"Analysis complete", file=sys.stderr)

if __name__ == "__main__":
    main()
