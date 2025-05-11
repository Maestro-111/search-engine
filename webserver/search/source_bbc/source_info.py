def get_source_metadata():

    """
    Return metadata about this source for the menu app
    """

    return {
        'name': 'BBC',  # Display name
        'icon': 'source_bbc/icons/bbc.png',  # Path to icon in static folder
        'url_name': "search_bbc",  # URL name pattern for this source's main view
        'description': 'Search data crawled from BBC',  # Short description
    }