from beanie import Document


class PingDocument(Document):
    name: str
    ok: bool = True

    class Settings:
        name = "diagnostic_pings"
