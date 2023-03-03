import base64
import hashlib
import hmac
import json

from httpx import Request

from neolegoff_bank.models.payments.pay_request import (
    PaymentParameters,
    PaymentProviderFields,
)
from neolegoff_bank.modules._module_parent import AioNeolegoffModuleParent


class AioNeolegoffPayments(AioNeolegoffModuleParent):
    def _generate_signature(self, request: Request) -> str:
        session_id = request.url.params.get("sessionid")
        params = request.url.query.decode()
        body = request.content.decode()
        method = str(request.method)
        endpoint = request.url.path

        to_sign = f"{method}\n{endpoint}"
        if params is not None:
            to_sign += f"\n{params}"
        if body is not None:
            to_sign += f"\n{body}"

        signature = hmac.new(session_id.encode(), to_sign.encode(), hashlib.sha256)
        signature_64 = base64.b64encode(signature.digest()).decode()

        return signature_64

    async def payment_commission(self, pay_parameters: PaymentParameters | dict):
        if isinstance(pay_parameters, PaymentParameters):
            pay_parameters = pay_parameters.export_commissions_json()
        else:
            pay_parameters = json.dumps(pay_parameters)

        request_data = {
            "payParameters": pay_parameters,
        }

        response = await self.core.session.post(
            url="https://api.tinkoff.ru/v1/payment_commission",
            params=self.core.app_data_payload,
            data=request_data,
        )

        return response.json()

    async def pay(self, pay_parameters: PaymentParameters | dict):
        if isinstance(pay_parameters, PaymentParameters):
            pay_parameters = pay_parameters.export_pay_tinkoff_json()
        else:
            pay_parameters = json.dumps(pay_parameters)
        request_data = {
            "payParameters": pay_parameters,
            "notificationUrl": "https://api.tinkoff.ru/v1/3ds",
            "timezone": 180,
            "language": "ru",
            "device_screen_height": self.core.device_info.screen_height,
            "device_screen_width": self.core.device_info.screen_width,
            "javaEnabled": "false",
            "javaScriptEnabled": "true",
            "color_depth": 24,
            "root": "false",
            "emulator": 0,
            "debug": 0,
        }

        request = self.core.session.build_request(
            method="POST",
            url="https://api.tinkoff.ru/v1/pay",
            params=self.core.app_data_payload,
            data=request_data,
        )
        signature = self._generate_signature(request)

        request.headers.update({"x-api-signature": signature})

        response = await self.core.session.send(request)

        return response.json()

    async def find_mobile_provider(self, phone: str):
        params = self.core.app_data_payload | {
            "fullInfo": True,
            "phone": phone,
        }

        response = await self.core.session.get(
            url="https://api.tinkoff.ru/providers/compatible/find",
            params=params,
        )

        return response.json()
