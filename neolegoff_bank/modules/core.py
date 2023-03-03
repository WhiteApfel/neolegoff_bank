from typing import Optional

from httpx import AsyncClient, Cookies

from neolegoff_bank.models.auth import AuthTokens
from neolegoff_bank.models.auth.device_authorize import DeviceAuthorizeResponsePayload
from neolegoff_bank.models.neolegoff_app_data import (
    NeolegoffAppData,
    NeolegoffAppDataManagerAbstract,
    NeolegoffAppDataManagerFileSystem,
    NeolegoffDeviceInfo,
)


class AioNeolegoffCore:
    def __init__(
        self,
        app_name: str = "main:whiteapfel",
        app_data_manager: NeolegoffAppDataManagerAbstract | None = None,
    ):
        self._http_session: AsyncClient = None

        if app_data_manager is not None:
            self.app_data_manager = app_data_manager
        else:
            self.app_data_manager: NeolegoffAppDataManagerFileSystem = (
                NeolegoffAppDataManagerFileSystem(
                    app_data=NeolegoffAppData(app_name=app_name)
                ).load_data()
            )

    @property
    def session(self) -> AsyncClient:
        if self._http_session is None:
            self._http_session = AsyncClient(headers={"user-agent": "okhttp/4.10.0"})
        if self.tokens is not None:
            self._http_session.headers.update(
                {"Authorization": f"Bearer {self.tokens.access_token}"}
            )
        self._http_session.cookies.update(self.cookies)
        return self._http_session

    @property
    def app_data(self) -> NeolegoffAppData:
        if (
            self.app_data_manager.file_last_modified_datetime
            > self.app_data_manager.last_load_datetime
        ):
            self.app_data_manager.load_data()
        return self.app_data_manager.data

    @property
    def cookies(self) -> dict[str, str]:
        return self.app_data_manager.data.cookies

    @cookies.setter
    def cookies(self, cookies: Cookies):
        self._http_session.cookies.update(cookies)
        self.app_data_manager.update_cookies(dict(cookies))

    @property
    def device_info(self) -> NeolegoffDeviceInfo:
        return self.app_data_manager.data.device_info

    @property
    def session_info(self) -> DeviceAuthorizeResponsePayload:
        return self.app_data_manager.data.session_info

    @session_info.setter
    def session_info(self, session_info):
        self.app_data_manager.update_session_info(session_info)

    @property
    def tokens(self) -> Optional[AuthTokens]:
        return self.app_data_manager.data.tokens

    @tokens.setter
    def tokens(self, tokens):
        self.app_data_manager.update_tokens(tokens)

    @property
    def app_data_payload(self):
        return {
            "appVersion": self.device_info.app_version,
            "appName": "mobile",
            "origin": "mobile,ib5,loyalty,platform",
            "platform": "android",
            "connectionType": "WiFi",
            "deviceId": self.device_info.device_uid,
            "oldDeviceId": self.device_info.device_uid,
            "sessionid": self.session_info.session_id,
        }
