import json
import re
from enum import Enum
from fuzzywuzzy import fuzz

short_version_fields = ['id', 'title', 'icon_url', 'developer_id', 'downloads', 'country', 'updated_date',
                        'dangerous_permissions_count']
extended_version_fields = short_version_fields + ['description', 'app_store_url', 'developer_url', 'permissions',
                                                  'available', 'first_time_seen', 'privacy_policy']
dangerous_permissions_terms = [
    "precise location (gps and network-based)",
    "approximate location (network-based)",
    "read the contents of your usb storage",
    "modify or delete the contents of your usb storage",
    "take pictures and videos",
    "read phone status and identity",
    "directly call phone numbers",
    "record audio",
    "find accounts on the device",
    "add or modify calendar events and send email to guests without owners' knowledge",
    "read calendar events plus confidential information",
    "body sensors (like heart rate monitors)",
    "modify your contacts",
    "use accounts on the device",
    "send sms messages",
    "read your contacts"
]


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
    dangerous_permissions_count = 0
    developer_url = None
    available = True
    first_time_seen = None
    privacy_policy = None

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
            'dangerous_permissions_count': int(self.dangerous_permissions_count),
            'permissions': {
                category: [permission.get_dict() for permission in self.permissions[category]]
                for index, category
                in enumerate(self.permissions)
            },
            'developer_url': self.developer_url,
            'available': self.available,
            'first_time_seen': self.first_time_seen,
            'privacy_policy': self.privacy_policy
        }

    def get_short_version_dict(self):
        return {
            key: value for key, value in self.get_dict().items() if key in short_version_fields
        }

    def get_extended_version_json(self):
        extended_version_dict = {
            key: value for key, value in self.get_dict().items()
            if key in extended_version_fields
        }

        extended_version_dict['permissions'] = {
            category: [permission.get_dict() for permission in self.permissions[category]]
            for index, category
            in enumerate(self.permissions)
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
        self.permissions = {
            category: [Permission(permission['permissionName'], permission['isDangerous'] == 1) for permission in permissions]
            for category, permissions
            in dictionary.get('permissions', {}).items()
        }
        self.developer_url = dictionary.get('developer_url', '')
        self.available = dictionary.get('available', True)
        self.first_time_seen = dictionary.get('first_time_seen', '')
        self.privacy_policy = dictionary.get('privacy_policy', '')
        self.dangerous_permissions_count = dictionary.get('dangerous_permissions_count', 0)

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
        if self.privacy_policy != other.privacy_policy:
            return False
        if self.dangerous_permissions_count != other.dangerous_permissions_count:
            return False

        return True


class Permission:
    name = ""
    dangerous = False

    def __init__(self, name, dangerous=None):
        self.name = name
        if dangerous:
            self.dangerous = dangerous
        else:
            self.dangerous = self.__get_dangerous_flag()

    def get_dict(self):
        return {
            'permissionName': self.name,
            'isDangerous': 1 if self.dangerous else 0
        }

    def __get_dangerous_flag(self):
        """
        Based on Google permission categorization https://developer.android.com/reference/android/Manifest.permission
        :return: boolean, dangerous permission flag
        """

        for dangerous_permissions_term in dangerous_permissions_terms:
            if fuzz.partial_ratio(dangerous_permissions_term.lower(), self.name.lower()) >= 80:
                return True

        return False

    def __eq__(self, other):
        if not isinstance(other, Permission):
            # don't attempt to compare against unrelated types
            return False

        if self.name != other.name:
            return False
        if self.dangerous != other.dangerous:
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
