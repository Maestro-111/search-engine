
from django.shortcuts import render
from django.apps import apps
import importlib


def index(request):

    """
    Menu page that displays all available web sources
    """

    all_apps = [app.name for app in apps.get_app_configs()]

    print(all_apps)

    source_apps = [app for app in all_apps if app.startswith('source_')]

    sources = []
    for app_name in source_apps:
        try:

            module = importlib.import_module(f"{app_name}.source_info")
            source_data = module.get_source_metadata()
            sources.append(source_data)
        except (ImportError, AttributeError):
            continue

    print(sources)

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