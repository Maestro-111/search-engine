def get_source_metadata():
    """
    Return metadata about this source for the menu app
    """

    return {
        "name": "Wikipedia",  # Display name
        "icon": "source_wikipedia/icons/wikipedia.png",  # Path to icon in static folder
        "url_name": "wiki_search",  # URL name pattern for this source's main view
        "description": "Search data crawled from Wikipedia",  # Short description
    }
