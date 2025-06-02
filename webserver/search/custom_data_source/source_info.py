def get_source_metadata():
    """
    Return metadata about this source for the menu app
    """

    return {
        "name": "Upload Custom Data Source",  # Display name
        "icon": "custom_data_source/icons/custom.svg",  # Path to icon in static folder
        "url_name": "search_custom",  # URL name pattern for this source's main view
        "description": "Search data indexed from Custom Data Source",  # Short description
    }
