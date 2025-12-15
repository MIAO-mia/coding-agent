"""
Intelligent Agent Entry Point
"""

from config import DEFAULT_PROJECT_ROOT, AUTO_INSTALL, USE_CONDA, DEFAULT_TIMEOUT, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, \
    DEEPSEEK_MODEL
from project_generator import generate_initial_project, generate_error_project, generate_modify_project, \
    generate_project_project
from code_runner import run_main_web_app, run_main_as_console_app, _kill_process_tree


def generate_project(code_mission, project_root=None, api_key=None,
                     base_url=None, model=None, auto_install=True,
                     use_conda=False, conda_env_name=None):
    """
    Main function to generate a project
    """

    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL
    project_root = project_root or DEFAULT_PROJECT_ROOT
    auto_install = AUTO_INSTALL if auto_install is None else auto_install
    use_conda = USE_CONDA if use_conda is None else use_conda

    result = generate_initial_project(
        code_mission=code_mission,
        project_root=project_root,
        api_key=api_key,
        base_url=base_url,
        model=model,
        auto_install=auto_install,
        use_conda=use_conda,
        conda_env_name=conda_env_name
    )

    return result


def error_project(former_message, error_message, project_root=None, api_key=None,
                  base_url=None, model=None, auto_install=True,
                  use_conda=False, conda_env_name=None):
    """
    Main function to fix a project
    """

    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL
    project_root = project_root or DEFAULT_PROJECT_ROOT
    auto_install = AUTO_INSTALL if auto_install is None else auto_install
    use_conda = USE_CONDA if use_conda is None else use_conda

    result = generate_error_project(
        former_message=former_message,
        error_message=error_message,
        project_root=project_root,
        api_key=api_key,
        base_url=base_url,
        model=model,
        auto_install=auto_install,
        use_conda=use_conda,
        conda_env_name=conda_env_name
    )

    return result


def modify_project(former_message, modify_message, project_root=None, api_key=None,
                   base_url=None, model=None, auto_install=True,
                   use_conda=False, conda_env_name=None):
    """
    Main function to fix a project
    """

    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL
    project_root = project_root or DEFAULT_PROJECT_ROOT
    auto_install = AUTO_INSTALL if auto_install is None else auto_install
    use_conda = USE_CONDA if use_conda is None else use_conda

    result = generate_modify_project(
        former_message=former_message,
        modify_message=modify_message,
        project_root=project_root,
        api_key=api_key,
        base_url=base_url,
        model=model,
        auto_install=auto_install,
        use_conda=use_conda,
        conda_env_name=conda_env_name
    )

    return result


def run_project(result, run_main=True, is_web_app=None,
                open_browser=None, run_timeout=DEFAULT_TIMEOUT):
    """
    Main function to run a project
    """
    # Determine the running method
    if is_web_app is None:
        run_as_web = (result.get("project_type", "python") == "web")
    else:
        run_as_web = is_web_app

    # Decide whether to open the browser
    if open_browser is None:
        open_browser_effective = run_as_web
    else:
        open_browser_effective = open_browser

    server_process = None
    error_message = None

    if run_main:
        main_path = result.get("project_root") + "/main.py"
        if not main_path:
            error_message = "can't find main.py"
        else:
            if run_as_web:
                result_container = {}
                web_app_success = run_main_web_app(main_path, open_browser_effective, run_timeout, result_container)

                # Check not only the function return value but also if there is an error message in the container
                if not web_app_success or "server_error" in result_container:
                    error_message = result_container.get("server_error", "failed to run web server")
                    # Ensure marked as failure
                    web_app_success = False

                server_process = result_container.get("server_process")

                if not web_app_success:
                    # Clean up immediately
                    if server_process and server_process.poll() is None:
                        _kill_process_tree(server_process)
            else:
                console_result = run_main_as_console_app(main_path, run_timeout)
                if not console_result["success"]:
                    # Preferentially use stderr, if not available, use the error field
                    error_message = console_result.get("stderr") or console_result.get("error", "failed to run")

    # Clean up
    if server_process and server_process.poll() is None:
        _kill_process_tree(server_process)

    # Return the result
    if error_message:
        return {
            "success": False,
            "error": error_message,
            "project_root": result.get("project_root", ""),
            "project_folder_name": result.get("project_folder_name", "")
        }
    else:
        return {"success": True}


def project_project(code_mission, project_folder, api_key=None,
                    base_url=None, model=None, auto_install=True,
                    use_conda=False, conda_env_name=None):
    """
    Main function to fix a project
    """

    api_key = api_key or DEEPSEEK_API_KEY
    base_url = base_url or DEEPSEEK_BASE_URL
    model = model or DEEPSEEK_MODEL
    auto_install = AUTO_INSTALL if auto_install is None else auto_install
    use_conda = USE_CONDA if use_conda is None else use_conda

    result = generate_project_project(
        code_mission=code_mission,
        project_folder=project_folder,
        api_key=api_key,
        base_url=base_url,
        model=model,
        auto_install=auto_install,
        use_conda=use_conda,
        conda_env_name=conda_env_name
    )

    return result
