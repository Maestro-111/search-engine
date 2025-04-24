def get_source_metadata():

    """
    Return metadata about this source for the menu app
    """

    return {
        'name': 'Wikipedia',  # Display name
        'icon': 'source_wikipedia/icons/wikipedia.png',  # Path to icon in static folder
        'url_name': "search_wikipedia",  # URL name pattern for this source's main view
        'description': 'Search data crawled from Google',  # Short description
        'doc_count': 1000000,  # Optional: Any additional metadata to display
    }