from neolegoff_bank.models.auth.user import UserInfo
from neolegoff_bank.modules._helpers import prepare_response
from neolegoff_bank.modules._module_parent import AioNeolegoffModuleParent


class AioNeolegoffUser(AioNeolegoffModuleParent):
    @prepare_response()
    async def user_info(self) -> UserInfo:
        return await self.core.session.get(
            url=f"https://id.tinkoff.ru/userinfo/userinfo?client_id=tinkoff-mb-app",
        )

    async def ping(self):
        response = await self.core.session.post(
            url="https://api.tinkoff.ru/v1/ping",
            params={
                "sessionid": self.core.session_info.session_id,
            },
            data={
                "mobile_device_model": self._neolegoff.device_info.device_model,
                "mobile_device_os": "android",
                "appVersion": self._neolegoff.device_info.app_version,
                "appName": "mobile",
                "origin": "mobile,ib5,loyalty,platform",
                "deviceId": self._neolegoff.device_info.device_uid,
                "oldDeviceId": self._neolegoff.device_info.device_uid,
                "appsflyer_uid": self._neolegoff.device_info.appsflyer_uid,
                "screen_width": self._neolegoff.device_info.screen_width,
                "screen_height": self._neolegoff.device_info.screen_height,
                "screen_dpi": self._neolegoff.device_info.screen_dpi,
                "mobile_device_os_version": (
                    self._neolegoff.device_info.os_version_major
                ),
                "connectionType": "WiFi",
                "platform": "android",
            },
        )

        return response.json()
