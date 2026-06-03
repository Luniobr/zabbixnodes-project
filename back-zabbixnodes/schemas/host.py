from pydantic import BaseModel


class HostInterface(BaseModel):
    type: int = 1  # 1=agent, 2=snmp, 3=ipmi, 4=jmx
    main: int = 1
    useip: int = 1
    ip: str = ""
    dns: str = ""
    port: str = "10050"


class HostGroup(BaseModel):
    groupid: str
    name: str | None = None


class HostTemplate(BaseModel):
    templateid: str
    name: str | None = None


class HostCreate(BaseModel):
    host: str
    name: str | None = None
    groups: list[dict]
    templates: list[dict] = []
    interfaces: list[HostInterface] = []
    description: str = ""
    monitored_by: int = 0  # 0=server, 1=proxy
    proxyid: str = "0"


class HostInterfaceUpdate(BaseModel):
    interfaceid: str
    type: int = 1
    main: int = 1
    useip: int = 1
    ip: str = ""
    dns: str = ""
    port: str = "10050"


class HostUpdate(BaseModel):
    host: str | None = None
    name: str | None = None
    groups: list[dict] | None = None
    templates: list[dict] | None = None
    interfaces: list[dict] | None = None
    description: str | None = None
    monitored_by: int | None = None
    proxyid: str | None = None


class HostOut(BaseModel):
    hostid: str
    host: str
    name: str
    status: str
    groups: list[dict] = []
    parentTemplates: list[dict] = []
    interfaces: list[dict] = []
    description: str = ""
