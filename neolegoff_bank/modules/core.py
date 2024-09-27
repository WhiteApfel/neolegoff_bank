import inspect
import traceback
import uuid
from pathlib import Path
from typing import Optional, Callable, Awaitable

import asyncio

import loguru
from httpx import AsyncClient, Cookies, Request, Response
from pullkin import Pullkin
from pullkin.models import AppCredentials as PullkinCredentials, Message
from pullkin.proto.mcs_proto import DataMessageStanza

from neolegoff_bank._service.context_logger import Context, get_context_logger
from neolegoff_bank.models.auth import AuthTokens
from neolegoff_bank.models.auth.device_authorize import DeviceAuthorizeResponsePayload
from neolegoff_bank.models.neolegoff_app_data import (
    NeolegoffAppData,
    NeolegoffAppDataManagerAbstract,
    NeolegoffAppDataManagerFileSystem,
    NeolegoffDeviceInfo,
)

logger = get_context_logger(__name__)


class AioNeolegoffCore:
    def __init__(
        self,
        app_name: str = "main:whiteapfel",
        app_data_manager: NeolegoffAppDataManagerAbstract | None = None,
        gcm_app_id="1:166510564052:android:ddf91abb35ca9795",
        fcm_sender_id="166510564052",
    ):
        self._http_session: AsyncClient = None
        self.pullkin = Pullkin()
        self.fcm_sender_id = fcm_sender_id
        self.gcm_app_id = gcm_app_id
        self.__receiving_push: asyncio.Task | None = None

        if app_data_manager is not None:
            self.app_data_manager = app_data_manager
        else:
            self.app_data_manager: NeolegoffAppDataManagerFileSystem = (
                NeolegoffAppDataManagerFileSystem(
                    app_data=NeolegoffAppData(app_name=app_name), app_name=app_name
                ).load_data()
            )

        self._user_handlers: list = []

    def on_notification(self, handler_filter=lambda *a, **k: True):
        def decorator(callback: Callable[[dict | None], Awaitable | None]):
            logger.debug(
                "(on_notification) Register"
                f" {callback.__module__}.{callback.__name__} as callback on"
                f" {inspect.getsource(callback) if not inspect.isfunction(callback) else callback.__name__}"
            )
            self._user_handlers.append({"callback": callback, "filter": handler_filter})
            return callback

        return decorator

    async def __run_on_notification_callbacks(
        self,
        message: dict,
    ):
        logger.info(
            f"(__run_on_notification_callbacks) Start parsing handler filters",
            extra={"mfms_message": message},
        )
        x = 0
        for handler in self._user_handlers:
            if handler["filter"](message):
                if inspect.iscoroutinefunction(handler["callback"]):
                    await handler["callback"](message)
                else:
                    handler["callback"](message)
                x += 1
        if not x:
            logger.debug("No one callback was called")

    async def start_push_server(self):
        logger.info(
            f"(start_push_server) Start push server",
            extra={
                "pullkin_credentials": (
                    self.pullkin_credentials.dict()
                    if self.pullkin_credentials is not None
                    else None
                )
            },
        )
        self.pullkin.credentials = self.pullkin_credentials
        self.__receiving_push = asyncio.get_event_loop().create_task(
            self._push_server()
        )

    async def stop_push_server(self):
        logger.info("(stop_push_server) Stop push server")
        await self.pullkin.close()

    async def _push_server(self):
        logger.info(f"(push_server) Init push server")
        filedir = f"{self.app_data_manager.data_dir_path}"
        persistent_path = f"{filedir}/persistent_ids.txt"
        Path(filedir).mkdir(parents=True, exist_ok=True)

        with open(persistent_path, "a+") as f:
            received_persistent_ids = [x.strip() for x in f]

        @self.pullkin.on_notification(lambda m, d: m is not None)
        async def on_push_message(message: Message, data_message: DataMessageStanza):
            logger.debug(
                "(on_push_message) Receive push with message",
                extra={"push": {"notification": dict(message)}},
            )

            server_message_id = message.fcmMessageId + "\n"
            with open(persistent_path, "r") as f:
                if server_message_id in f:
                    return
            with open(persistent_path, "a") as f:
                f.write(server_message_id)

        @self.pullkin.on_notification(
            lambda m, d: m is None
            and len([a for a in d.app_data if a.key == "alert"]) == 0
        )
        async def on_data_message_without_alert(
            message: None, data_message: DataMessageStanza
        ):
            logger.debug(
                "(on_data_message_without_alert) Receive push without alert",
                extra={
                    "push": {
                        "app_data": {a.key: a.value for a in data_message.app_data}
                    }
                },
            )

        @self.pullkin.on_notification(
            lambda m, d: m is None and len([a for a in d.app_data if a.key == "alert"])
        )
        async def on_data_message_with_alert(
            message: None, data_message: DataMessageStanza
        ):
            try:
                logger.info(
                    "(on_data_message_with_alert) Receive push with alert",
                    extra={
                        "push": {
                            "app_data": {a.key: a.value for a in data_message.app_data}
                        }
                    },
                )

                server_message_id = data_message.persistent_id + "\n"
                with open(persistent_path, "r") as f:
                    if server_message_id in f:
                        return
                with open(persistent_path, "a") as f:
                    f.write(server_message_id)

                session_key = self.pullkin._app_data_by_key(data_message, "sessionKey")
                message_id = self.pullkin._app_data_by_key(
                    data_message, "serverMessageId"
                )

                await self.push_received(message_id)

                messages_response = await self.mfms_sync(session_key)

                messages = messages_response.get("pushMessage")
                if messages:
                    for message in messages:
                        await self.__run_on_notification_callbacks(message)
            except:
                logger.exception(
                    "(on_data_message_with_alert) Error during processing push"
                )

        self.pullkin.persistent_ids = received_persistent_ids
        # push_listener = await self.pullkin.listen_coroutine()
        # try:
        #     while True:
        #         await push_listener.asend(None)
        # except (asyncio.CancelledError, ConnectionResetError, RuntimeError, OSError):
        #     return
        # except Exception as e:
        #     logger.exception("(_push_server) Push listener error:")
        #     raise

    async def push_received(
        self,
        server_message_id: str,
    ):
        logger.debug(
            f"(push_received) Mark mfms message {server_message_id=} as received via"
            " push"
        )
        response = await self.session.post(
            url="https://pushserver.mfms.ru/tcsbank/service/messages/pushReceived",
            json={
                "deviceAddress": {
                    "deviceAddress": self.app_data.device_address,
                },
                "serverMessageId": server_message_id,
            },
            headers={"Accept": "application/json, text/plain, */*"},
        )

        return response.json()

    async def mfms_sync(self, session_key):
        logger.debug(f"(mfms_sync) Sync push messages with mfms by {session_key=}")
        response = await self.session.post(
            url="https://pushserver.mfms.ru/tcsbank/service/messages/sync",
            json={
                "batchSize": 100,
                "deviceAddress": {
                    "deviceAddress": self.app_data.device_address,
                },
                "sessionKey": session_key,
                "syncToken": self.app_data.next_sync_token or "null",
            },
            headers={"Accept": "application/json, text/plain, */*"},
        )

        response_data = response.json()

        next_sync_token = response_data.get("nextSyncToken")
        logger.debug(f"(mfms_sync) Synced successfully {next_sync_token=}")

        self.app_data.next_sync_token = next_sync_token
        self.app_data_manager.save_data()

        messages = response_data.get("pushMessage")

        if messages is not None:
            logger.debug(
                f"(mfms_sync) Synced {len(messages)} messages",
                extra={"Push messages": messages},
            )
            await self.mfms_received([m.get("messageId") for m in messages])
        else:
            logger.debug("(mfms_sync) No push synced")

        return response_data

    async def mfms_received(self, received: list[str]):
        logger.debug(
            f"(mfms_received) Mark {len(received)} messages as received",
            extra={
                "Push received": received,
            },
        )
        response = await self.session.post(
            url="https://pushserver.mfms.ru/tcsbank/service/messages/received",
            json={
                "deviceAddress": {
                    "deviceAddress": self.app_data.device_address,
                },
                "receivedMessageId": received,
            },
            headers={"Accept": "application/json, text/plain, */*"},
        )

        return response.json()

    @property
    def session(self) -> AsyncClient:
        if self._http_session is None:
            self._http_session = AsyncClient(headers={"user-agent": "okhttp/4.10.0"}, timeout=11)

            def get_decorated_send(func):
                async def decorated_send(request: Request, *args, **kwargs):
                    req_id = str(uuid.uuid4())
                    logger.debug(
                        f"(http_session.send) Send request to {request.url} #{req_id}",
                        extra={
                            "request": {
                                "headers": dict(request.headers),
                                "content": request.content.decode(),
                            }
                        },
                    )
                    response: Response = await func(request, *args, **kwargs)
                    logger.debug(
                        (
                            "(http_session.send) Got response from"
                            f" {request.url} #{req_id}"
                        ),
                        extra={
                            "response": {
                                "headers": dict(response.headers),
                                "content": response.content.decode(),
                            }
                        },
                    )
                    return response

                return decorated_send

            self._http_session.send = get_decorated_send(self._http_session.send)
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
        Context.set(Context.get() | {"cookies": self.app_data.cookies})
        return self.app_data.cookies

    @cookies.setter
    def cookies(self, cookies: Cookies | None):
        if cookies is not None:
            self._http_session.cookies.update(cookies)
            self.app_data_manager.update_cookies(dict(cookies))
        else:
            self._http_session.cookies.clear()
            self.app_data_manager.update_cookies({})
        Context.set(Context.get() | {"cookies": self.app_data.cookies})

    @property
    def device_info(self) -> NeolegoffDeviceInfo:
        return self.app_data.device_info

    @property
    def session_info(self) -> DeviceAuthorizeResponsePayload:
        Context.set(Context.get() | {"session_info": self.app_data.session_info.dict()})
        return self.app_data.session_info

    @session_info.setter
    def session_info(self, session_info):
        if session_info is not None:
            Context.set(Context.get() | {"session_info": session_info.dict()})
        else:
            Context.set(Context.get() | {"session_info": None})
        self.app_data_manager.update_session_info(session_info)

    @property
    def tokens(self) -> AuthTokens | None:
        if self.app_data.tokens is not None:
            self.app_data.tokens.expires_in = 120
            Context.set(Context.get() | {"tokens": self.app_data.tokens.dict()})
        else:
            Context.set(Context.get() | {"tokens": None})
        return self.app_data.tokens

    @tokens.setter
    def tokens(self, tokens):
        if tokens is not None:
            Context.set(Context.get() | {"tokens": tokens.dict()})
        else:
            Context.set(Context.get() | {"tokens": None})
        self.app_data_manager.update_tokens(tokens)

    @property
    def pullkin_credentials(self) -> PullkinCredentials | None:
        return self.app_data.pullkin_credentials

    @pullkin_credentials.setter
    def pullkin_credentials(self, pullkin_credentials):
        self.app_data_manager.update_pullkin_credentials(pullkin_credentials)

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
