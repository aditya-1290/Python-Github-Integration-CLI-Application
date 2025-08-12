from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    username: str
    password_hash: str
    github_token: Optional[str] = None