import json
from enum import Enum

short_version_fields = ['id', 'title', 'icon_url', 'developer_id', 'downloads', 'country', 'updated_date']
extended_version_fields = short_version_fields + ['description', 'app_store_url', 'developer_url', 'permissions', 'available', 'first_time_seen']


class Application:
    id = None
    title = None
    icon_url = None
    developer_id = None
    updated_date = None
    downloads = None
    country = None
    description = None
    app_store_url = None
    permissions = None
    developer_url = None
    available = True
    first_time_seen = None

    def get_dynamodb_item(self):
        return {key: value for key, value in self.get_dict().items() if (value or key == 'available')}

    def get_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'icon_url': self.icon_url,
            'developer_id': self.developer_id,
            'updated_date': self.updated_date,
            'downloads': self.downloads,
            'country': self.country,
            'description': self.description,
            'app_store_url': self.app_store_url,
            'permissions': self.permissions,
            'developer_url': self.developer_url,
            'available': self.available,
            'first_time_seen': self.first_time_seen
        }

    def get_short_version_dict(self):
        return {
            key: value for key, value in self.get_dict().items() if key in short_version_fields
        }

    def get_short_version_json(self):
        return json.dumps(self.get_short_version_dict(), indent=2)

    def get_extended_version_json(self):
        extended_version_dict = {
            key: value for key, value in self.get_dict().items() if key in extended_version_fields
        }

        return json.dumps(extended_version_dict, indent=2)

    def enrich_from_dictionary(self, dictionary):
        self.id = dictionary.get('id', '')
        self.title = dictionary.get('title', '')
        self.icon_url = dictionary.get('icon_url', '')
        self.developer_id = dictionary.get('developer_id', '')
        self.updated_date = dictionary.get('updated_date', '')
        self.downloads = dictionary.get('downloads', '')
        self.country = dictionary.get('country', '')
        self.description = dictionary.get('description', '')
        self.app_store_url = dictionary.get('app_store_url', '')
        self.permissions = dictionary.get('permissions', [])
        self.developer_url = dictionary.get('developer_url', '')
        self.available = dictionary.get('available', True)
        self.first_time_seen = dictionary.get('first_time_seen', '')

    def __init__(self, app_id=None):
        self.id = app_id

    def __eq__(self, other):
        if not isinstance(other, Application):
            # don't attempt to compare against unrelated types
            return False

        if self.id != other.id:
            return False
        if self.title != other.title:
            return False
        if self.icon_url != other.icon_url:
            return False
        if self.developer_id != other.developer_id:
            return False
        if self.updated_date != other.updated_date:
            return False
        if self.downloads != other.downloads:
            return False
        if self.description != other.description:
            return False
        if set(self.permissions) != set(other.permissions):
            return False
        if self.developer_url != other.developer_url:
            return False
        if self.country != other.country:
            return False
        if self.first_time_seen != other.first_time_seen:
            return False

        return True


class TwitterNotificationType(Enum):
    NEW = 1
    UPDATE = 2
    UNAVAILABLE = 3


class TwitterNotification:
    id = None
    title = None
    updated_date = None
    country = None
    notification_type = None
