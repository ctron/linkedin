from typing import Any, Tuple, List
import os

from mautrix.bridge.config import BaseBridgeConfig
from mautrix.types import UserID
from mautrix.util.config import ConfigUpdateHelper, ForbiddenDefault, ForbiddenKey


class Config(BaseBridgeConfig):
    def __getitem__(self, key: str) -> Any:
        try:
            return os.environ[f"MAUTRIX_FACEBOOK_{key.replace('.', '_').upper()}"]
        except KeyError:
            return super().__getitem__(key)

    @property
    def forbidden_defaults(self) -> List[ForbiddenDefault]:
        return [
            *super().forbidden_defaults,
            ForbiddenDefault(
                "appservice.database", "postgres://username:password@hostname/db"
            ),
            ForbiddenDefault(
                "appservice.public.external",
                "https://example.com/public",
                condition="appservice.public.enabled",
            ),
            ForbiddenDefault("bridge.permissions", ForbiddenKey("example.com")),
        ]

    def do_update(self, helper: ConfigUpdateHelper) -> None:
        super().do_update(helper)
        copy, copy_dict, base = helper

        copy("homeserver.asmux")

        # appservice
        copy("appservice.bot_avatar")
        copy("appservice.public.allow_matrix_login")
        copy("appservice.public.enabled")
        copy("appservice.public.external")
        copy("appservice.public.prefix")

        if self["appservice.public.shared_secret"] == "generate":
            base["appservice.public.shared_secret"] = self._new_token()
        else:
            copy("appservice.public.shared_secret")

        # bridge
        copy("bridge.double_puppet_allow_discovery")
        copy("bridge.double_puppet_server_map")
        copy("bridge.invite_own_puppet_to_pm")
        copy("bridge.resend_bridge_info")
        copy("bridge.sync_with_custom_puppets")
        copy("bridge.temporary_disconnect_notices")
        copy("bridge.username_template")

        if "bridge.login_shared_secret" in self:
            base["bridge.login_shared_secret_map"] = {
                base["homeserver.domain"]: self["bridge.login_shared_secret"]
            }
        else:
            copy("bridge.login_shared_secret_map")

        copy_dict("bridge.permissions")

    def _get_permissions(self, key: str) -> Tuple[bool, bool, str]:
        level = self["bridge.permissions"].get(key, "")
        admin = level == "admin"
        user = level == "user" or admin
        return user, admin, level

    def get_permissions(self, mxid: UserID) -> Tuple[bool, bool, str]:
        permissions = self["bridge.permissions"] or {}
        if mxid in permissions:
            return self._get_permissions(mxid)

        homeserver = mxid[mxid.index(":") + 1 :]
        if homeserver in permissions:
            return self._get_permissions(homeserver)

        return self._get_permissions("*")