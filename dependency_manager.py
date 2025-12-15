"""
Dependency Management Module
Provides functionality for checking, resolving, and installing Python package dependencies
Supports reading dependencies from requirements.txt files and installing them using pip or conda
"""

import os
import sys
import subprocess
import importlib.metadata
import packaging.version
import packaging.requirements
import packaging.specifiers


def parse_package_name(package_spec):
    """
    Extract the pure package name from a package specification string (removing version constraints)

    Parameters:
        package_spec (str): Package specification string, e.g., "numpy==1.21.0" or "pandas>=1.0.0"

    Returns:
        str: Extracted package name, e.g., "numpy"

    Examples:
        >>> parse_package_name("numpy==1.21.0")
        'numpy'
        >>> parse_package_name("pandas>=1.0.0,<2.0.0")
        'pandas'
    """
    # Remove leading/trailing whitespace
    package_spec = package_spec.strip()

    # Define all possible version comparison operators
    operators = ['==', '>=', '<=', '!=', '~=', '<', '>']

    # Iterate through operators, split the string if found, and take the part before the operator as the package name
    for op in operators:
        if op in package_spec:
            return package_spec.split(op)[0].strip()

    # If no version operator is found in the string, it's a pure package name; return as is
    return package_spec


def _parse_requirement_spec(package_spec):
    """
    Parse package specification string using the packaging.requirements library

    Parameters:
        package_spec (str): Package specification string

    Returns:
        tuple: (package_name, version_constraint_object)

    Exceptions:
        If parsing fails, returns package name and an unconstrained SpecifierSet

    Note:
        This is an internal helper function that uses the packaging library for more accurate parsing
    """
    package_spec = package_spec.strip()
    try:
        # Use packaging.requirements.Requirement for standard parsing
        req = packaging.requirements.Requirement(package_spec)
        # Return package name and version constraints
        return req.name, req.specifier
    except Exception:
        # Fall back to simple parsing if standard parsing fails
        # Return package name and an unconstrained version specifier
        return parse_package_name(package_spec), packaging.specifiers.SpecifierSet()


def _get_installed_version(package_name):
    """
    Get the version of a package installed in the current environment

    Parameters:
        package_name (str): Package name

    Returns:
        packaging.version.Version: Version object of the installed package

    Exceptions:
        importlib.metadata.PackageNotFoundError: If the package is not installed
    """
    # Get package distribution information via importlib.metadata
    dist = importlib.metadata.distribution(package_name)
    # Parse version string into a Version object for easy comparison
    return packaging.version.parse(dist.version)


def check_package_installed(package_spec):
    """
    Check if the specified package is installed and meets version requirements

    Parameters:
        package_spec (str): Package specification string, which may include version constraints

    Returns:
        bool: True if the package is installed and meets version requirements,
              False if not installed or does not meet requirements

    Note:
        This function swallows all exceptions to ensure dependency checks don't
        affect the main program flow
    """
    try:
        # Parse package specification to get package name and version constraints
        package_name, specifier = _parse_requirement_spec(package_spec)

        # Get installed package version
        installed_version = _get_installed_version(package_name)

        # If no version constraints, consider it passed as long as the package exists
        if not specifier:
            return True

        # Use SpecifierSet to check if installed version satisfies constraints
        # Syntax: version in specifier
        return installed_version in specifier

    except importlib.metadata.PackageNotFoundError:
        # Package not installed
        return False
    except Exception as e:
        # Catch all other exceptions, log but don't affect main flow
        print(f"Error checking package {package_spec}: {e}")
        return False


def parse_requirements(requirements_path):
    """
    Parse a requirements.txt file and extract a list of package specifications

    Parameters:
        requirements_path (str): Path to the requirements.txt file

    Returns:
        list: List of package specification strings

    Note:
        Skips comments, blank lines, -e installations, git repository links,
        index URLs, and other special lines
    """
    # Check if file exists
    if not os.path.exists(requirements_path):
        return []

    packages = []
    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip comment lines
            if line.startswith('#'):
                continue

            # Skip editable installations (-e)
            if line.startswith('-e'):
                continue

            # Skip direct git repository installations
            if line.startswith('git+'):
                continue

            # Skip custom index URLs
            if line.startswith('-i') or line.startswith('--index-url'):
                continue

            # Skip local file paths
            if line.startswith('-f') or line.startswith('--find-links'):
                continue

            # If it's a valid package specification, add to list
            packages.append(line)

    return packages


def _filter_packages_by_install_status(all_packages, quiet=False):
    """
    Separate already installed packages from packages to install based on current environment

    Parameters:
        all_packages (list): List of all package specifications to check
        quiet (bool): Whether to run in silent mode (no information output)

    Returns:
        tuple: (list of installed packages, list of packages to install)
    """
    installed_packages = []
    packages_to_install = []

    for package in all_packages:
        # Check if package is already installed
        if check_package_installed(package):
            installed_packages.append(package)
            if not quiet:
                print(f"✓ Already installed: {package}")
        else:
            packages_to_install.append(package)

    return installed_packages, packages_to_install


def _build_install_command(package, use_conda=False, conda_env_name=None, upgrade=False):
    """
    Build installation command (pip or conda) based on configuration

    Parameters:
        package (str): Package specification to install
        use_conda (bool): Whether to use conda for installation
        conda_env_name (str): Conda environment name; None means current environment
        upgrade (bool): Whether to upgrade already installed packages

    Returns:
        list: Command line argument list
    """
    if use_conda:
        # Build conda installation command
        if conda_env_name:
            # Specify conda environment
            cmd = ["conda", "install", "-n", conda_env_name, "-y"]
        else:
            # Current conda environment
            cmd = ["conda", "install", "-y"]

        # Conda handles version constraints slightly differently than pip
        if '==' in package:
            pkg_name, pkg_version = package.split('==', 1)
            cmd.append(f"{pkg_name}={pkg_version}")
        else:
            cmd.append(package)
    else:
        # Build pip installation command
        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package)

    return cmd


def _install_single_package(package, use_conda=False, conda_env_name=None, upgrade=False, quiet=False):
    """
    Install a single package

    Parameters:
        package (str): Package specification to install
        use_conda (bool): Whether to use conda
        conda_env_name (str): Conda environment name
        upgrade (bool): Whether to upgrade
        quiet (bool): Whether to run in silent mode

    Returns:
        tuple: (installation success status, error message or None)
    """
    if not quiet:
        print(f"Installing: {package}")

    # Build installation command
    cmd = _build_install_command(package, use_conda=use_conda,
                                 conda_env_name=conda_env_name,
                                 upgrade=upgrade)

    try:
        # Execute installation command
        result = subprocess.run(
            cmd,
            capture_output=True,  # Capture stdout and stderr
            text=True,            # Process output as text
            timeout=300,          # 5-minute timeout
            check=False           # Don't automatically raise exceptions
        )

        if result.returncode == 0:
            # Installation successful
            if not quiet:
                print(f"  ✓ Successfully installed: {package}")
            return True, None

        # Installation failed, extract error message
        error_msg = result.stderr.strip() or "Unknown error"
        if not quiet:
            print(f"  ✗ Failed to install: {package}")
            if result.stderr:
                # Show only first 200 characters of error message
                print(f"    Error: {result.stderr[:200]}")
        return False, error_msg

    except subprocess.TimeoutExpired:
        # Installation timeout
        if not quiet:
            print(f"  ✗ Installation timeout: {package}")
        return False, "Installation timeout (5 minutes)"
    except Exception as e:
        # Other exceptions
        if not quiet:
            print(f"  ✗ Installation exception: {package}")
            print(f"    Exception: {str(e)}")
        return False, str(e)


def install_requirements(requirements_path, use_conda=False, conda_env_name=None, upgrade=False, quiet=False,
                         auto_install=True):
    """
    Install dependencies from requirements.txt, supports automatic installation judgment

    Parameters:
        requirements_path (str): Path to requirements.txt file
        use_conda (bool): Whether to use conda for installation
        conda_env_name (str): Conda environment name to install into
        upgrade (bool): Whether to upgrade already installed packages
        quiet (bool): Whether to run in silent mode
        auto_install (bool): Whether to automatically install dependencies;
                             if False, skip installation step

    Returns:
        dict: Dictionary containing installation results with the following keys:
            - success: Whether all installations were successful
            - message: Result message
            - installed: List of installed packages
            - failed: List of failed installations (each element is a dict with package and error)
            - total: Total number of packages
            - success_count: Number of successful installations
            - failure_count: Number of failed installations
        Returns None if auto_install is False

    Exceptions:
        Does not raise exceptions; all errors are passed through return value
    """
    # 1. Automatic installation condition check
    if not (auto_install and requirements_path and os.path.exists(requirements_path)):
        return None

    # 2. Display installation step information
    if not quiet:
        print(f"Auto-installing dependencies...")
        print(f"Found requirements.txt: {requirements_path}")

        if use_conda:
            env_info = f"in conda environment '{conda_env_name}'" if conda_env_name else "in current conda environment"
            print(f"Using conda installation {env_info}")
        else:
            print("Using pip installation (current Python environment)")

    # 3. Check if requirements file exists
    if not os.path.exists(requirements_path):
        result = {
            "success": False,
            "error": f"requirements.txt file does not exist: {requirements_path}",
            "installed": [],
            "failed": []
        }
        if not quiet:
            print(f"✗ Dependency installation failed: {result['error']}")
        return result

    # 4. Parse requirements file
    all_packages = parse_requirements(requirements_path)
    if not all_packages:
        result = {
            "success": True,
            "message": "No packages to install in requirements.txt",
            "installed": [],
            "failed": []
        }
        if not quiet:
            print(f"✓ Dependency installation completed: {result['message']}")
        return result

    # 5. Separate already installed packages from those to install
    installed_packages, packages_to_install = _filter_packages_by_install_status(
        all_packages,
        quiet=quiet
    )

    # 6. If all packages are already installed, return success immediately
    if not packages_to_install:
        result = {
            "success": True,
            "message": "All dependency packages are already installed",
            "installed": installed_packages,
            "failed": []
        }
        if not quiet:
            print(f"✓ Dependency installation completed: {result['message']}")
        return result

    # 7. Install packages to install one by one
    success_packages = []  # Packages successfully installed this time
    failed_packages = []  # Packages that failed installation this time

    for package in packages_to_install:
        ok, error = _install_single_package(
            package,
            use_conda=use_conda,
            conda_env_name=conda_env_name,
            upgrade=upgrade,
            quiet=quiet
        )
        if ok:
            success_packages.append(package)
        else:
            failed_packages.append({
                "package": package,
                "error": error
            })

    # 8. Compile and return results
    all_installed = installed_packages + success_packages

    if failed_packages:
        # Some packages failed to install
        result = {
            "success": False,
            "message": f"Installation completed, but {len(failed_packages)} packages failed to install",
            "installed": all_installed,
            "failed": failed_packages,
            "total": len(all_packages),
            "success_count": len(success_packages),
            "failure_count": len(failed_packages)
        }
    else:
        # All installations successful
        result = {
            "success": True,
            "message": f"Successfully installed {len(success_packages)} packages",
            "installed": all_installed,
            "failed": [],
            "total": len(all_packages),
            "success_count": len(success_packages),
            "failure_count": 0
        }

    # 9. Output final result
    if not quiet:
        if result["success"]:
            print(f"✓ Dependency installation completed: {result['message']}")
        else:
            print(f"✗ Dependency installation failed: {result['message']}")

    return result
