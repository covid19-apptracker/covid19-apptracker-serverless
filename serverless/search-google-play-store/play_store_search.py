import requests
from bs4 import BeautifulSoup
import re


def get_apps_ids(play_store_url):
    """Scrape play store to gather App IDs.
    Returns a list of App IDs

    Keyword arguments:
    play_store_url -- URL from a Play Store Search
    :rtype: list
    """
    page = requests.get(play_store_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    link_elements = soup.find_all('a', class_='')

    # Save unique App IDs on set (to avoid having to deduplicate)
    app_ids = set()
    app_id_regex_pattern = re.compile(r'/store/apps/details\?id=(.+)')
    for link_element in link_elements:
        if 'href' in link_element.attrs:
            result = app_id_regex_pattern.search(link_element.attrs['href'])
            if result is not None:
                app_ids.add(result.group(1))

    return list(app_ids)
