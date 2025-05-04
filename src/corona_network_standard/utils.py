import importlib.resources
import sys
import click

def get_resource_path(package: str, resource: str) -> str:
    """Gets the path to a resource within the package."""
    try:
        # Use files() for modern Python (returns Traversable)
        # The path needs to be resolved within the context manager
        with importlib.resources.files(package) as package_path:
            resource_path = package_path / resource
            if resource_path.is_file():
                # Ensure the path is resolved to a string before exiting the context
                resolved_path = str(resource_path.resolve())
                return resolved_path
            else:
                raise FileNotFoundError(f"Resource not found or not a file: {resource} in {package}")
    except (ImportError, AttributeError, FileNotFoundError, TypeError) as e:
        # Fallback for older Python or if files() fails
        click.echo(f"Using fallback importlib.resources.path due to error: {e}", err=True)
        try:
            with importlib.resources.path(package, resource) as p:
                 return str(p)
        except Exception as fallback_e:
            click.echo(f"Error finding resource {resource} in package {package} using fallback: {fallback_e}", err=True)
            sys.exit(1)
