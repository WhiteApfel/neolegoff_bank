class AioNeolegoffModuleParent:
    def __init__(self, neolegoff: "AioNeolegoff"):
        from neolegoff_bank.modules import AioNeolegoff

        self._neolegoff: AioNeolegoff = neolegoff
        self.core = self._neolegoff.core
