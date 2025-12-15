"""
File utility module
"""

import os
import json
from collections import OrderedDict
from typing import Dict, List, Any

def ensure_directory(dir_path):
    """
    Unified directory creation function
    """
    if not dir_path:
        return False
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        return False

def save_project_json(project_data: Dict[str, Any], project_root: str) -> None:
    """
    Save project data to JSON file, removing code and operation fields during processing
    Use operation field to handle deletions during merging, but do not include operation field when saving

    Args:
        project_data: Dictionary containing complete project data
        project_root: Project root directory path
    """
    # Define JSON file path
    project_file = os.path.join(project_root, "project_detail.json")

    # Create a copy of data without code fields for merging logic
    data_for_merge = project_data.copy()

    # Remove code field from each file in out_file
    if "out_file" in data_for_merge:
        for file_info in data_for_merge["out_file"]:
            if "code" in file_info:
                del file_info["code"]

    # Create a copy of data without code and operation fields for final saving
    data_for_save = OrderedDict()

    # Add top-level fields in specified order
    if "project_folder_name" in project_data:
        data_for_save["project_folder_name"] = project_data["project_folder_name"]
    if "project_type" in project_data:
        data_for_save["project_type"] = project_data["project_type"]

    # Process out_file, removing code and operation fields
    if "out_file" in project_data:
        # Process each file, arranging in specified order
        processed_files = []

        for file_info in project_data["out_file"]:
            # Only keep file_name and description fields, arranged in specified order
            processed_file = OrderedDict()
            if "file_name" in file_info:
                processed_file["file_name"] = file_info["file_name"]
            if "description" in file_info:
                processed_file["description"] = file_info["description"]

            processed_files.append(processed_file)

        data_for_save["out_file"] = processed_files

    # Check if JSON file already exists
    if os.path.exists(project_file):
        try:
            # Read existing JSON data
            with open(project_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f, object_pairs_hook=OrderedDict)

            # Merge data: Use data_for_merge (with operation field) for merging logic
            if "out_file" in existing_data and "out_file" in data_for_merge:
                new_out_files = []
                processed_files = set()

                # First process existing files
                for existing_file in existing_data["out_file"]:
                    file_name = existing_file["file_name"]

                    # Check if there is a corresponding file in new data
                    matching_new_file = None
                    for merge_file in data_for_merge["out_file"]:
                        if merge_file["file_name"] == file_name:
                            matching_new_file = merge_file
                            processed_files.add(file_name)
                            break

                    if matching_new_file:
                        if matching_new_file.get("operation") == "delete":
                            continue
                        else:
                            # Non-delete operation, create entry without operation
                            updated_file = OrderedDict()
                            updated_file["file_name"] = file_name
                            if "description" in matching_new_file:
                                updated_file["description"] = matching_new_file["description"]
                            elif "description" in existing_file:
                                updated_file["description"] = existing_file["description"]
                            new_out_files.append(updated_file)
                    else:
                        # No corresponding new file, keep as is (without operation)
                        if "operation" in existing_file:
                            # If existing file contains operation field, remove it
                            file_without_operation = OrderedDict()
                            file_without_operation["file_name"] = existing_file["file_name"]
                            if "description" in existing_file:
                                file_without_operation["description"] = existing_file["description"]
                            new_out_files.append(file_without_operation)
                        else:
                            new_out_files.append(existing_file)

                # Then process newly added files in new data (files not recorded in processed_files)
                for merge_file in data_for_merge["out_file"]:
                    file_name = merge_file["file_name"]
                    if (file_name not in processed_files and
                            merge_file.get("operation") != "delete"):
                        # Newly added file and not a delete operation
                        new_file = OrderedDict()
                        new_file["file_name"] = file_name
                        if "description" in merge_file:
                            new_file["description"] = merge_file["description"]
                        new_out_files.append(new_file)

                # Create final merged data
                merged_data = OrderedDict()

                # Add fields in specified order
                if "project_folder_name" in data_for_save:
                    merged_data["project_folder_name"] = data_for_save["project_folder_name"]
                elif "project_folder_name" in existing_data:
                    merged_data["project_folder_name"] = existing_data["project_folder_name"]

                if "project_type" in data_for_save:
                    merged_data["project_type"] = data_for_save["project_type"]
                elif "project_type" in existing_data:
                    merged_data["project_type"] = existing_data["project_type"]

                merged_data["out_file"] = new_out_files

                data_to_save = merged_data
            else:
                data_to_save = data_for_save

        except (json.JSONDecodeError, KeyError) as e:
            data_to_save = data_for_save
    else:
        data_to_save = data_for_save

    if "out_file" in data_to_save:
        for file_info in data_to_save["out_file"]:
            if "operation" in file_info:
                del file_info["operation"]
            if "code" in file_info:
                del file_info["code"]

    with open(project_file, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2, sort_keys=False)


# Helper function: Create data containing operation field for merging logic
def create_project_data(project_folder_name: str,
                        project_type: str,
                        out_files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create project data structure containing operation field for merging logic

    Args:
        project_folder_name: Project folder name
        project_type: Project type
        out_files: File list, each file contains file_name, operation, description

    Returns:
        Dictionary containing complete data
    """
    data = OrderedDict()
    data["project_folder_name"] = project_folder_name
    data["project_type"] = project_type

    ordered_files = []
    for file_info in out_files:
        ordered_file = OrderedDict()
        ordered_file["file_name"] = file_info.get("file_name", "")
        ordered_file["operation"] = file_info.get("operation", "")
        ordered_file["description"] = file_info.get("description", "")
        ordered_files.append(ordered_file)

    data["out_file"] = ordered_files
    return data


def get_directory_tree_str(root_dir, indent='', is_last=True, show_files=True, max_depth=None, current_depth=0,
                           output_lines=None):
    """
    Recursively generate a string representation of a directory tree

    Args:
        root_dir: Root directory path
        indent: Current level indentation
        is_last: Whether current item is the last in parent directory
        show_files: Whether to show files
        max_depth: Maximum display depth, None means unlimited
        current_depth: Current depth
        output_lines: List to store output lines

    Returns:
        List of strings representing directory tree
    """
    if output_lines is None:
        output_lines = []

    if max_depth is not None and current_depth > max_depth:
        return output_lines

    # Get all items in directory and sort them
    items = []
    try:
        items = sorted(os.listdir(root_dir))
    except (PermissionError, OSError):
        output_lines.append(f"{indent}└── [权限不足，无法访问]")
        return output_lines

    # Separate files and folders
    dirs = []
    files = []
    for item in items:
        item_path = os.path.join(root_dir, item)
        if os.path.isdir(item_path):
            dirs.append(item)
        else:
            files.append(item)

    # Combine lists: directories first, then files
    all_items = dirs + files if show_files else dirs

    # Calculate total items
    total_items = len(all_items)

    for i, item in enumerate(all_items):
        item_path = os.path.join(root_dir, item)
        is_item_last = (i == total_items - 1)

        # Determine connector for current item
        if is_last:
            connector = '└── '
            next_indent = indent + '    '
        else:
            connector = '├── '
            next_indent = indent + '│   '

        # Process current item
        if os.path.isdir(item_path):
            output_lines.append(f"{indent}{connector}{item}/")
            # Recursively process subdirectory
            get_directory_tree_str(item_path, next_indent, is_item_last,
                                   show_files, max_depth, current_depth + 1, output_lines)
        elif show_files:
            # Get file size
            try:
                size = os.path.getsize(item_path)
                # Convert to appropriate unit with 2 decimal places
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size < 1024.0 or unit == 'TB':
                        if unit == 'B':
                            size_str = f"{size} B"
                        else:
                            size_str = f"{size:.2f} {unit}"
                        break
                    size /= 1024.0
                output_lines.append(f"{indent}{connector}{item} ({size_str})")
            except (PermissionError, OSError):
                output_lines.append(f"{indent}{connector}{item} [无法获取大小]")

    return output_lines


def get_directory_tree(folder_path, show_files=True, max_depth=None, return_as_string=True):
    """
    Get string representation of directory tree

    Args:
        folder_path: Folder path
        show_files: Whether to show files
        max_depth: Maximum depth
        return_as_string: Whether to return as string (True returns string, False returns list)

    Returns:
        String or list representing directory tree
    """
    if not os.path.exists(folder_path):
        return f"Error: Folder '{folder_path}' does not exist"

    if not os.path.isdir(folder_path):
        return f"Error: '{folder_path}' is not a folder"

    # Build directory tree
    output_lines = [f"{os.path.basename(folder_path)}/"]
    output_lines.extend(get_directory_tree_str(folder_path, '', True, show_files, max_depth, 0, []))

    if return_as_string:
        return "\n".join(output_lines)
    else:
        return output_lines


def process_json_request(json_request, actual_project_root):
    """
    Process JSON request, read files with operation "read"

    Args:
        json_request: JSON dictionary containing file operation information
        actual_project_root: Actual path of project root directory

    Returns:
        JSON dictionary containing read file contents
    """
    try:
        if isinstance(json_request, str):
            request_data = json.loads(json_request)
        else:
            request_data = json_request

        corresponding_code = []

        if "out_file" not in request_data:
            return {"error": "Missing 'out_file' field in request"}

        for file_request in request_data["out_file"]:
            if "file_name" not in file_request or "operation" not in file_request:
                print(f"Warning: Skipping file request with missing fields: {file_request}")
                continue

            file_name = file_request["file_name"]
            operation = file_request["operation"]

            if operation == "read":
                file_path = os.path.join(os.path.abspath(actual_project_root), file_name)

                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        file_content = file.read()

                    corresponding_code.append({
                        "file_name": file_name,
                        "code": file_content
                    })

                    print(f"Successfully read: {file_name}")

                except FileNotFoundError:
                    print(f"Error: File not found: {file_path}")
                    corresponding_code.append({
                        "file_name": file_name,
                        "code": f"# Error: File '{file_name}' not found at {file_path}"
                    })
                except PermissionError:
                    print(f"Error: Permission denied: {file_path}")
                    corresponding_code.append({
                        "file_name": file_name,
                        "code": f"# Error: Permission denied for file '{file_name}'"
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    corresponding_code.append({
                        "file_name": file_name,
                        "code": f"# Error reading file: {str(e)}"
                    })

        return {"corresponding_code": corresponding_code}

    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}