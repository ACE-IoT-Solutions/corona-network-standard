"""
Utility functions for the Corona Network Standard tool.
"""
import importlib.resources
import sys
import click
from pathlib import Path

def get_resource_path(package: str, resource_name: str) -> Path:
    """
    Safely retrieves the path to a packaged resource using importlib.resources.

    Handles potential deprecation warnings and provides a fallback for older Python versions.

    Args:
        package: The name of the package containing the resource (e.g., 'corona_network_standard.data.shapes').
        resource_name: The name of the resource file (e.g., 'network-shapes.ttl').

    Returns:
        A Path object pointing to the resource file.

    Raises:
        FileNotFoundError: If the resource cannot be found within the package.
    """
    try:
        # Use files() API available in Python 3.9+
        if sys.version_info >= (3, 9):
            return importlib.resources.files(package).joinpath(resource_name)
        else:
            # Fallback for Python < 3.9 (may show DeprecationWarning)
            with importlib.resources.path(package, resource_name) as path:
                return path
    except (ModuleNotFoundError, FileNotFoundError, TypeError) as e: # Added TypeError for context manager issue
        # Attempt fallback for potential zipapp/context manager issues
        try:
            with importlib.resources.path(package, resource_name) as path:
                 print(f"Using fallback importlib.resources.path due to error: {e}", file=sys.stderr)
                 return path
        except Exception as final_e:
             raise FileNotFoundError(
                 f"Resource '{resource_name}' not found in package '{package}'. Original error: {e}, Fallback error: {final_e}"
             ) from final_e
