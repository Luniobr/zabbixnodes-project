from pydantic import BaseModel


class ProxyCreate(BaseModel):
    name: str
    operating_mode: int = 0  # 0=active, 1=passive
    description: str = ""


class ProxyOut(BaseModel):
    proxyid: str
    name: str
    operating_mode: str = "0"
    description: str = ""
    lastaccess: str = "0"
