import pycountry


def enrich_app_country(app_id, app_description, app_developer_url):
    country = None

    if app_id is not None:
        country = search_in_app_id(app_id)

    if country is not None:
        return country

    if app_developer_url is not None:
        country = search_in_developer_url(app_developer_url)

    if country is not None:
        return country

    if app_description is not None:
        country = search_in_description(app_description)

    return country if country is not None else ''


def search_in_app_id(app_id):
    split_id = app_id.split('.')
    return search_country(split_id)


def search_in_developer_url(app_developer_url):
    split_developer_url = app_developer_url.split('.')
    return search_country(split_developer_url)


def search_in_description(app_description):
    description = app_description.lower()
    for country_item in list(pycountry.countries):
        if description.find(country_item.name.lower()) != -1:
            return country_item.alpha_2
    return


def search_country(identifiers):
    for identifier in identifiers:
        result = pycountry.countries.get(alpha_2=identifier.upper())
        if result is not None:
            return result.alpha_2

        result = pycountry.countries.get(name=identifier.capitalize())
        if result is not None:
            return result.alpha_2

    return None

