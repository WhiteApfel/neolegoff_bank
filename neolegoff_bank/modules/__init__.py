# isort: off

from neolegoff_bank.modules.core import AioNeolegoffCore
from neolegoff_bank.modules.auth import AioNeolegoffAuth
from neolegoff_bank.modules.products import AioNeolegoffProducts
from neolegoff_bank.modules.operations import AioNeolegoffOperations
from neolegoff_bank.modules.user import AioNeolegoffUser
from neolegoff_bank.modules.payment import AioNeolegoffPayments

# isort: on


class AioNeolegoff:
    def __init__(self, app_name: str = "main:whiteapfel"):
        self.core = AioNeolegoffCore(app_name)

        self.auth: AioNeolegoffAuth = AioNeolegoffAuth(self)
        self.products: AioNeolegoffProducts = AioNeolegoffProducts(self)
        self.user: AioNeolegoffUser = AioNeolegoffUser(self)
        self.operations: AioNeolegoffOperations = AioNeolegoffOperations(self)
        self.payments: AioNeolegoffPayments = AioNeolegoffPayments(self)

    @property
    def is_login_required(self) -> bool:
        return self.core.tokens is None

    @property
    def is_refresh_tokens_required(self):
        return not self.core.tokens.is_access_token_alive
