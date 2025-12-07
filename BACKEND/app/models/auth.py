from pydantic import BaseModel, constr


class LoginWithPhoneRequest(BaseModel):
    phone_number: constr(pattern=r"^\+[1-9]\d{1,14}$")
    guest_id: str
