def get_source_metadata():
    """
    Return metadata about this source for the menu app
    """

    return {
        "name": "Dota Buff",  # Display name
        "icon": "source_dota_buff/icons/dota_buff.png",  # Path to icon in static folder
        "url_name": "dota_buff_search",  # URL name pattern for this source's main view
        "description": "Search data crawled from dota_buff",  # Short description
    }
