"""
Project Generator Module
"""
import json
import os
import shutil
from file_utils import ensure_directory, save_project_json, get_directory_tree, process_json_request
from dependency_manager import install_requirements
from ai_utils import get_first_response, get_error_response, get_modify_response, get_project_response, \
    code_detail_feedback
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from pathlib import Path


def _get_project_folder_name(project_data):
    """Ensure project_folder_name is valid"""
    import re
    name = project_data.get("project_folder_name", "") or "generated_project"
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
    return name or "generated_project"


def create_project_structure(base_dir, project_data):
    """
    Create project folder structure and files based on JSON data

    Args:
        base_dir (str): Base directory path
        project_data (dict): JSON data containing project structure

    Returns:
        tuple: (status_code, file_list, project_type, requirements_path, main_path) or (status_code, None, None, None, None)
    """
    try:
        # Check if project folder exists, create if not
        if not Path(base_dir).exists():
            Path(base_dir).mkdir(parents=True, exist_ok=True)

        # Parse file list
        file_list = project_data["out_file"]
        project_type = project_data["project_type"]

        # Initialize variables
        requirements_path = None
        file_name_list = []

        # Create or delete files
        for file_info in file_list:
            file_name = file_info["file_name"]
            operation = file_info["operation"]
            file_path = Path(base_dir) / file_name

            if operation == "write":
                # Write file
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_info["code"])

                file_name_list.append(file_name)

                # Check if it's a special file
                if "requirements.txt" in file_name:
                    requirements_path = str(file_path)

            elif operation == "delete":
                # Delete file
                if file_path.exists():
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
        return "success", file_name_list, project_type, requirements_path

    except Exception as e:
        print(f"Error processing project structure: {e}")
        return "error", None, None, None


def generate_initial_project(code_mission, project_root=None, api_key=None,
                             base_url=None,
                             model=None,
                             auto_install=True,
                             use_conda=False,
                             conda_env_name=None):
    """
    Generate complete project
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    print("\n=== Generating project ===")
    error_result, project_data, messages = get_first_response(
        code_mission=code_mission,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    if error_result == 'error':
        return error_result

    # Determine folder name and create root directory
    project_folder_name = _get_project_folder_name(project_data)

    actual_project_root = os.path.join(os.path.abspath(project_root), project_folder_name)
    ensure_directory(actual_project_root)

    # Create program files and save code
    create_state, file_name_list, project_type, require_path = create_project_structure(actual_project_root,
                                                                                        project_data)
    if create_state == "error":
        return {
            "success": False,
            "stage": "creation",
            "error": "failed to create project"
        }
    if require_path:
        requirements_path = os.path.join(actual_project_root, Path(require_path))
        # Auto-install dependencies
        if auto_install:
            install_requirements(
                requirements_path=requirements_path,
                auto_install=auto_install,
                use_conda=use_conda,
                conda_env_name=conda_env_name
            )
    # Save original project data (JSON format)
    save_project_json(project_data, actual_project_root)
    # Modified version
    return {
        "success": "success",
        "project_root": actual_project_root,  # main is at this level
        "project_folder_name": project_folder_name,
        "project_type": project_type,
        "messages": messages,  # First round conversation
    }


def generate_error_project(former_message, error_message, project_root=None, api_key=None,
                           base_url=None, model=None, auto_install=True,
                           use_conda=False, conda_env_name=None):
    """
    Main function to fix project
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    print("\n=== Generating project ===")
    error_result, project_data, messages = get_error_response(
        former_message=former_message,
        error_message=error_message,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    if error_result == 'error':
        return error_result

    # Determine folder name and create root directory
    project_folder_name = _get_project_folder_name(project_data)
    actual_project_root = os.path.join(os.path.abspath(project_root), project_folder_name)
    ensure_directory(actual_project_root)

    # Loop until LLM retrieves all the needed code
    read_file_status = "'operation': 'read'" in str(project_data)
    while read_file_status:
        code_detail = json.dumps(process_json_request(project_data, actual_project_root), indent=2, ensure_ascii=False)
        error_result, project_data, messages = code_detail_feedback(
            former_message=messages, code_detail=code_detail, api_key=api_key, base_url=base_url, model=model
        )
        if error_result == 'error':
            return error_result
        read_file_status = "'operation': 'read'" in str(project_data)

    # Create program files and save code
    create_state, file_name_list, project_type, require_path = create_project_structure(actual_project_root,
                                                                                        project_data)
    if create_state == "error":
        return {
            "success": False,
            "stage": "creation",
            "error": "failed to create project"
        }
    if require_path:
        requirements_path = os.path.join(actual_project_root, Path(require_path))
        # Auto-install dependencies
        if auto_install:
            install_requirements(
                requirements_path=requirements_path,
                auto_install=auto_install,
                use_conda=use_conda,
                conda_env_name=conda_env_name
            )
    # Save original project data (JSON format)
    save_project_json(project_data, actual_project_root)
    return {
        "success": "success",
        "project_root": actual_project_root,  # main is at this level
        "project_folder_name": project_folder_name,
        "project_type": project_type,
        "messages": messages,  # Previous conversation
    }


def generate_modify_project(former_message, modify_message, project_root=None, api_key=None,
                            base_url=None, model=None, auto_install=True,
                            use_conda=False, conda_env_name=None):
    """
    Main function to fix project
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    print("\n=== Generating project ===")
    error_result, project_data, messages = get_modify_response(
        former_message=former_message,
        modify_message=modify_message,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    if error_result == 'error':
        return error_result

    # Determine folder name and create root directory
    project_folder_name = _get_project_folder_name(project_data)
    actual_project_root = os.path.join(os.path.abspath(project_root), project_folder_name)
    ensure_directory(actual_project_root)

    # Loop until LLM retrieves all the needed coed
    read_file_status = "'operation': 'read'" in str(project_data)
    while read_file_status:
        code_detail = json.dumps(process_json_request(project_data, actual_project_root), indent=2, ensure_ascii=False)
        error_result, project_data, messages = code_detail_feedback(
            former_message=messages, code_detail=code_detail, api_key=api_key, base_url=base_url, model=model
        )
        if error_result == 'error':
            return error_result
        read_file_status = "'operation': 'read'" in str(project_data)

    # Create program files and save code
    create_state, file_name_list, project_type, require_path = create_project_structure(actual_project_root,
                                                                                        project_data)
    if create_state == "error":
        return {
            "success": False,
            "stage": "creation",
            "error": "failed to create project"
        }
    if require_path:
        requirements_path = os.path.join(actual_project_root, Path(require_path))
        # Auto-install dependencies
        if auto_install:
            install_requirements(
                requirements_path=requirements_path,
                auto_install=auto_install,
                use_conda=use_conda,
                conda_env_name=conda_env_name
            )
    # Save original project data (JSON format)
    save_project_json(project_data, actual_project_root)
    return {
        "success": "success",
        "project_root": actual_project_root,  # main is at this level
        "project_folder_name": project_folder_name,
        "project_type": project_type,
        "messages": messages,  # Previous conversation
    }


def generate_project_project(code_mission, project_folder, api_key=None,
                             base_url=None,
                             model=None,
                             auto_install=True,
                             use_conda=False,
                             conda_env_name=None):
    """
    Generate complete project
    """
    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL

    project_structure = get_directory_tree(project_folder)
    print("\n=== Generating project ===")
    error_result, project_data, messages = get_project_response(
        code_mission=code_mission,
        project_structure=project_structure,
        api_key=api_key,
        base_url=base_url,
        model=model
    )
    print(project_data)
    if error_result == 'error':
        return error_result

    # Determine folder name and create root directory
    project_folder_name = _get_project_folder_name(project_data)
    actual_project_root = os.path.abspath(project_folder)
    ensure_directory(actual_project_root)

    # Loop until LLM retrieves all the needed code
    read_file_status = "'operation': 'read'" in str(project_data)
    while read_file_status:
        code_detail = json.dumps(process_json_request(project_data, actual_project_root), indent=2, ensure_ascii=False)
        error_result, project_data, messages = code_detail_feedback(
            former_message=messages, code_detail=code_detail, api_key=api_key, base_url=base_url, model=model
        )

        if error_result == 'error':
            return error_result
        read_file_status = "'operation': 'read'" in str(project_data)

    # Create program files and save code
    create_state, file_name_list, project_type, require_path = create_project_structure(actual_project_root,
                                                                                        project_data)
    if create_state == "error":
        return {
            "success": False,
            "stage": "creation",
            "error": "failed to create project"
        }
    if require_path:
        requirements_path = os.path.join(actual_project_root, Path(require_path))
        # Auto-install dependencies
        if auto_install:
            install_requirements(
                requirements_path=requirements_path,
                auto_install=auto_install,
                use_conda=use_conda,
                conda_env_name=conda_env_name
            )
    # Save original project data (JSON format)
    save_project_json(project_data, actual_project_root)
    # Modified version
    return {
        "success": "success",
        "project_root": actual_project_root,  # main is at this level
        "project_folder_name": project_folder_name,
        "project_type": project_type,
        "messages": messages,  # First round conversation
    }
