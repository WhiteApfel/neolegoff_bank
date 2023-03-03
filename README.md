# Neolegoff - Tinkoff Banking API client

## Предисловие

Использовать на свой страх и риск. В коде нет никаких бэкдоров для вытягивания ваших данных,
можете посмотреть сами. Но есть нюансик: если что-то пойдёт не так, то я не виноват, вы сами дураки.

## Как установить

### Из PyPI:

```shell
python -m pip install neolegoff_bank
```

### Из исходников:

```shell
git clone https://github.com/whiteapfel/neolegoff-bank.git
cd neolegoff-bank
python setup.py install
```

## Как использовать

### Пайплайн авторизации и получение информации о счетах и картах:

```python
import asyncio

from neolegoff_bank import AioNeolegoff


async def login(client):
    phone = "79998887766"
    password = "vs2p33ox!6x_vma_!y9xjw6gz"
    card = "5321304044087960"

    async def get_sms_code():
        return input("SMS code >>> ")

    login_pipeline = client.auth.login_pipeline(phone, password, card)
    async for _ in login_pipeline:
        # Можно использовать любой вариант получения кода:
        # ввести из консоли, дождаться создания файла или бота в телеграме.
        # Как угодно. Потребуется только в первый раз, потом будет
        # автоматически пропускаться, так как login_pipeline будет пустым
        await login_pipeline.asend(await get_sms_code())


async def main():
    # `app_name` используется для сохранения информации о токенах,
    # сессии и сгенерированном конфиге устройства.
    # Часть после двоеточия является паролем для шифрования,
    # но это не обязательно, можно абсолютно любую строку
    client = AioNeolegoff(app_name="main:whiteapfel")
    await login(client)

    products = await client.products.get_products()
    print(products)


asyncio.run(main())
```
**Далее в примерах будет опущен login, предполагая, что авторизация пройдена**

### Пополнение баланса мобильника

```python
import asyncio

from decimal import Decimal

from neolegoff_bank import AioNeolegoff
from neolegoff_bank.models.payments.pay_request import PaymentParametersMobileProvider

async def main():
    client = AioNeolegoff(app_name="main:whiteapfel")
    payment = PaymentParametersMobileProvider(
        provider='mts',
        account="5160007810",
        amount=Decimal("42.72"),
        phone="9867657635",
    )
    print(await client.payments.payment_commission(payment))
    print(await client.payments.pay(payment))

asyncio.run(main())
```

### Пайплайн перевода по СБП физику

```python

```

### Пайплайн оплаты по СБП юрику/ип через куар или ссылку

```python

```

### Пайплайн перевода по номеру карты

```python

```
