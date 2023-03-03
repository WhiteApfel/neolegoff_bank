import hashlib
import json
import string
from abc import ABC
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from hashlib import md5
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from random import choice, randint, randrange
from typing import Optional

from appdirs import AppDirs
from Cryptodome.Cipher import AES
from pydantic import BaseModel, Field
from randmac import RandMac

from neolegoff_bank.models.auth import AuthTokens
from neolegoff_bank.models.auth.device_authorize import DeviceAuthorizeResponsePayload


class NeolegoffDeviceInfo(BaseModel):
    # May need an increase
    app_version = "6.12.1"
    push_version = "2.0.6"
    version = "3.1.2"

    # Package info
    app_package = "com.idamob.tinkoff.android"

    # Unique device IDs
    appsflyer_uid = "1665453203890-5636190662334170797"
    device_address = "gcmorix6v50f8y832o7noupcolouhkqjqb"
    device_serial_number = "36abb434"
    device_uid = "8b102654eb77ddcc"
    installation_uid = "34snDzQ2mYDRnfrenBai"
    old_device_id = "8b102654eb77ddcc"
    pns_push_address = (
        "c-34snDzQ2mYDRnfrenBai:APA91bExVQZHfen2Ap3f0PBJxi_gNy-"
        "QNA90ChdHbPhJOFqnI4N3alXFOJHhyNsC6dnmkiuvAfpbfdjJLNmOC"
        "2UQUvCesNzRrBZSpp8fQt1HJApQ3MV5ptPIc0EzJcApYj61gp4U68k9"
    )
    provider_uid = "PH5AckgzOkJrMVhoRGRrPkBCbDdeKUFuRVooRElkZCtCay5Qfj4K"

    # Device info
    device_model = "WhiteApfel Neolegoff"
    device_name = "wafelka"
    os_name = "Android sm6150"

    locale = "ru"
    time_zone_utc_offset_second = "10800"

    memory_size = 1024

    screen_dpi = 404
    screen_height = 2297
    screen_width = 1080

    # Android info
    api_level = 31
    can_show_push_notification = True
    os_version_major = 12
    os_version_minor = -1
    os_version_patch = -1
    platform = 1  # 1 = Android

    # Network info
    ip_address = "fe80::3464:87ff:fece:1e20%dummy0"
    mac_address = "36:64:87:CE:1E:20"
    router_ip_address = "192.168.0.100"
    router_mac_address = "02:00:00:00:00:00"

    # Calculated
    user_agent = f"{device_model}/android: {os_version_major}/TCSMB/{app_version}"
    device_fingerprint = (
        f"{user_agent}###{screen_width}x{screen_height}x32###180###false###false###"
    )

    @classmethod
    def generate_new_config(cls):
        network = IPv4Network("192.168.0.0/16")
        random_ip = IPv4Address(
            randrange(
                int(network.network_address) + 1,
                int(network.broadcast_address) - 1,
            )
        )
        return cls(
            appsflyer_uid=(
                f"{''.join(str(randint(0, 9)) for _ in range(13))}-{''.join(str(randint(0, 9)) for _ in range(19))}"
            ),
            device_address="".join(
                [choice(string.ascii_letters[:26] + string.digits) for _ in range(34)]
            ),
            device_serial_number="".join(
                [choice(string.hexdigits[:-6]) for _ in range(8)]
            ),
            device_uid=(
                device_uid := "".join(
                    [choice(string.hexdigits[:-6]) for _ in range(16)]
                )
            ),
            old_device_id=device_uid,
            installation_uid="".join(
                [choice(string.ascii_letters + string.digits) for _ in range(20)]
            ),
            mac_address=str(RandMac()),
            router_ip_address=str(random_ip),
            pns_push_address=(
                "".join(
                    [
                        choice(string.ascii_letters + string.digits + "-_")
                        for _ in range(22)
                    ]
                )
                + ":"
                + "".join(
                    [
                        choice(string.ascii_letters + string.digits + "-_")
                        for _ in range(140)
                    ]
                )
            ),
        )

    def fingerprint(self):
        return json.dumps(
            {
                "appVersion": self.app_version,
                "autologinOn": False,
                "autologinUsed": False,
                "backCameraAvailable": True,
                "biometricsSupport": 1,
                "clientLanguage": "en",
                "clientTimezone": -180,
                "connectionType": "WiFi",
                "debug": 0,
                "emulator": 0,
                "frontCameraAvailable": True,
                "root_flag": False,
                "lockedDevice": 1,
                "mobileDeviceId": self.device_uid,
                "mobileDeviceModel": self.device_model,
                "mobileDeviceOs": "Android",
                "mobileDeviceOsVersion": "12",
                "screenDpi": self.screen_dpi,
                "screenHeight": self.screen_height,
                "screenWidth": self.screen_width,
                "tinkoffDeviceId": self.device_uid,
                "userAgent": self.user_agent,
            }
        )


class NeolegoffAppData(BaseModel):
    app_name: str = Field("main:whiteapfel", exclude=True)
    cookies: dict = Field(default_factory=dict)
    cypher_key: Optional[str]
    device_info: Optional[NeolegoffDeviceInfo]
    session_info: Optional[DeviceAuthorizeResponsePayload]
    tokens: Optional[AuthTokens]


class NeolegoffAppDataManagerAbstract(ABC):
    def __init__(self, **kwargs):
        ...

    def update_tokens(self, tokens: AuthTokens):
        ...

    def update_device_info(self, device_info: NeolegoffDeviceInfo):
        ...

    def update_cookies(self, cookies: dict):
        ...

    def update_session_info(self, session: DeviceAuthorizeResponsePayload):
        ...

    def load_data(self, **kwargs):
        ...

    def save_data(self, **kwargs):
        ...


class NeolegoffAppDataManagerFileSystem(NeolegoffAppDataManagerAbstract):
    def __init__(self, app_data: NeolegoffAppData = None, **kwargs):
        super().__init__()
        self.data: NeolegoffAppData = app_data

        self.salt = md5(b"whiteapfel").hexdigest().encode()
        self.key = hashlib.scrypt(
            self.data.app_name.rsplit(":", 1)[-1].encode(),
            salt=self.salt,
            n=2,
            r=8,
            p=2,
            dklen=32,
        )

        self.last_load_datetime: datetime = None

    @property
    def data_dir_path(self) -> Path:
        neolegoff_dir = AppDirs("neolegoff", "whiteapfel")
        return Path(
            f"{neolegoff_dir.user_data_dir}/{self.data.app_name.rsplit(':', 1)[0]}"
        )

    @property
    def data_file_path(self) -> Path:
        return self.data_dir_path / "neolegoff_data.json"

    @property
    def file_last_modified_datetime(self) -> datetime:
        return datetime.fromtimestamp(
            self.data_file_path.stat().st_mtime, tz=timezone.utc
        )

    def get_cipher(self):
        return AES.new(self.key, AES.MODE_EAX, b64decode(b"GAYGAY0WHITEAPFELGAYEw=="))

    def load_data(self, **kwargs):
        self.data_dir_path.mkdir(parents=True, exist_ok=True)

        if not self.data_file_path.exists():
            self.data.device_info = NeolegoffDeviceInfo.generate_new_config()
            self.save_data()
        # TODO: Add failed config data case
        else:
            encoded_b64_string = self.data_file_path.read_text()
            encrypted_string = b64decode(encoded_b64_string)
            tag, ciphertext = encrypted_string[:16], encrypted_string[16:]
            json_string = self.get_cipher().decrypt_and_verify(ciphertext, tag)
            data = json.loads(json_string)
            self.data = NeolegoffAppData(**data)
            self.last_load_datetime = self.file_last_modified_datetime
        return self

    def save_data(self, **kwargs):
        json_string = self.data.json(by_alias=True)
        ciphertext, tag = self.get_cipher().encrypt_and_digest(json_string.encode())
        encrypted_string = tag + ciphertext
        encoded_b64_string = b64encode(encrypted_string).decode()
        self.data_file_path.write_text(encoded_b64_string)
        self.last_load_datetime = self.file_last_modified_datetime

    def update_tokens(self, tokens: AuthTokens):
        self.data.tokens = tokens
        self.save_data()

    def update_device_info(self, device_info: NeolegoffDeviceInfo):
        self.data.device_info = device_info
        self.save_data()

    def update_cookies(self, cookies: dict):
        self.data.cookies.update(cookies)
        self.save_data()

    def update_session_info(self, session_info: DeviceAuthorizeResponsePayload):
        self.data.session_info = session_info
        self.save_data()
