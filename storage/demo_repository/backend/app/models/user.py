"""User entities and domain records."""

class BaseEntity:
    def __init__(self, id: str):
        self.id = id

class User(BaseEntity):
    def __init__(self, id: str, username: str, email: str, password_hash: str):
        super().__init__(id)
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_active = True
