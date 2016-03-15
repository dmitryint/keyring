import platform

from ..backend import KeyringBackend
from ..errors import PasswordSetError
from ..errors import PasswordDeleteError
from ..util import properties

try:
    from . import _OS_X_API as api
except Exception:
    pass


class Keyring(KeyringBackend):
    """Mac OS X Keychain"""

    keychain = 'login.keychain'
    "Pathname to keychain filename, overriding default keychain."

    @properties.ClassProperty
    @classmethod
    def priority(cls):
        """
        Preferred for all OS X environments.
        """
        if platform.system() != 'Darwin':
            raise RuntimeError("OS X required")
        return 5

    def set_password(self, service, username, password):
        if username is None:
            username = ''

        try:
            api.set_generic_password(self.keychain, service, username, password)
        except api.Error:
            raise PasswordSetError("Can't store password on keychain")

    def get_password(self, service, username):
        if username is None:
            username = ''

        try:
            return api.find_generic_password(self.keychain, service, username)
        except api.NotFound:
            pass

    def delete_password(self, service, username):
        if username is None:
            username = ''

        username = username.encode('utf-8')
        service = service.encode('utf-8')
        with api.open(self.keychain) as keychain:
            length = api.c_uint32()
            data = api.c_void_p()
            item = api.sec_keychain_item_ref()
            status = api.SecKeychainFindGenericPassword(
                keychain,
                len(service),
                service,
                len(username),
                username,
                length,
                data,
                item,
            )
            if status != 0:
                raise PasswordDeleteError("Can't delete password in keychain")

            api.SecKeychainItemDelete(item)
            api._core.CFRelease(item)
