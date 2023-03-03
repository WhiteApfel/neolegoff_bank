import json
from datetime import datetime, timedelta

from neolegoff_bank.models.operations import Operations
from neolegoff_bank.modules._helpers import prepare_response
from neolegoff_bank.modules._module_parent import AioNeolegoffModuleParent


class AioNeolegoffOperations(AioNeolegoffModuleParent):
    async def statements(self, account: str):
        request_data = {
            "requestsData": json.dumps(
                [
                    {
                        "key": account,
                        "operation": "statements",
                        "params": {
                            "last": "1",
                            "account": account,
                        },
                    }
                ]
            )
        }

        response = await self.core.session.post(
            url=f"https://api.tinkoff.ru/v1/grouped_requests?",
            params=self.core.app_data_payload,
            data=request_data,
        )

        data = response.json()

        return data

    @prepare_response()
    async def operations(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        period: timedelta | None = timedelta(days=30),
        account_id: str = None,
    ) -> Operations:
        if start is None:
            if end is None:
                end = datetime.now().astimezone()
            start = end - period
        elif end is None:
            end = start + period

        response = await self.core.session.get(
            url=f"https://api.tinkoff.ru/v1/operations?",
            params=self.core.app_data_payload
            | {
                "start": int(start.timestamp() * 1000),
                "end": int(end.timestamp() * 1000),
            }
            | ({"account": account_id} if account_id is not None else {}),
        )

        return response
