
from django.shortcuts import render
from django.apps import apps
import importlib


def index(request):
    """
    Menu page that displays all available web sources
    """
    # Get all installed apps
    all_apps = [app.name for app in apps.get_app_configs()]

    # Filter for source apps (adapt this to your naming convention for source apps)
    source_apps = [app for app in all_apps if app.startswith('source_')]

    # Collect source metadata
    sources = []
    for app_name in source_apps:
        try:
            # Try to import source_info from each source app
            module = importlib.import_module(f"{app_name}.source_info")
            source_data = module.get_source_metadata()
            sources.append(source_data)
        except (ImportError, AttributeError):
            # Skip apps that don't implement the expected interface
            continue

    # For testing, if no sources are found, add some dummy sources
    if not sources:
        sources = [
            {
                'name': 'Google',
                'icon': 'menu/icons/google.png',  # Placeholder path
                'url_name': 'menu:index',  # Placeholder URL
                'description': 'Google search results'
            },
            {
                'name': 'Twitter',
                'icon': 'menu/icons/twitter.png',  # Placeholder path
                'url_name': 'menu:index',  # Placeholder URL
                'description': 'Twitter posts and profiles'
            },
            {
                'name': 'Amazon',
                'icon': None,  # Will use default icon (first letter)
                'url_name': 'menu:index',  # Placeholder URL
                'description': 'Amazon product listings'
            }
        ]

    context = {
        'sources': sources,
    }
    return render(request, 'menu/menu.html', context)