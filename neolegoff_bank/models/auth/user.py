from pydantic import BaseModel


class UserInfo(BaseModel):
    phone_number_verified: bool
    family_name: str
    birthdate: str
    middle_name: str | None
    sub: str
    given_name: str
    gender: str
    name: str
    phone_number: str
    cryptography: list | None
