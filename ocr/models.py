from pydantic import BaseModel, ValidationError, validator


class OtpEntry(BaseModel):
    secret: str
    name: str
    issuer: str
    algorithm: int
    digits: int
    type: int

    @validator("secret")
    def secret_must_be_right(cls, v):
        if len(v) != 24:
            raise ValidationError("secret length must be 24 chairs, got length: %d" % len(v))
        if v != v.upper():
            raise ValidationError("secret must be alpha(upper) numeric")
