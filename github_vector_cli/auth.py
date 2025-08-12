import json
import os
import hashlib
from getpass import getpass
from pathlib import Path
from typing import Optional, Dict

class AuthManager:
    def __init__(self, data_dir: str = ".github_vector_cli"):
        self.data_dir = Path(data_dir)
        self.users_file = self.data_dir / "users.json"
        self.sessions_file = self.data_dir / "sessions.json"
        self._ensure_data_dir()
        self.current_user: Optional[str] = None

    def _ensure_data_dir(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        if not self.users_file.exists():
            self.users_file.write_text("{}")
        if not self.sessions_file.exists():
            self.sessions_file.write_text("{}")

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str) -> bool:
        users = self._load_users()
        if username in users:
            return False
        
        users[username] = {
            "password_hash": self._hash_password(password),
            "github_token": None
        }
        self._save_users(users)
        return True

    def login(self, username: str, password: str) -> bool:
        users = self._load_users()
        if username not in users:
            return False
        
        if users[username]["password_hash"] != self._hash_password(password):
            return False
        
        self.current_user = username
        self._create_session(username)
        return True

    def logout(self) -> None:
        self.current_user = None
        self._clear_session()

    def set_github_token(self, username: str, token: str) -> None:
        users = self._load_users()
        if username in users:
            users[username]["github_token"] = token
            self._save_users(users)

    def get_github_token(self, username: str) -> Optional[str]:
        users = self._load_users()
        return users.get(username, {}).get("github_token")

    def _load_users(self) -> Dict:
        return json.loads(self.users_file.read_text())

    def _save_users(self, users: Dict) -> None:
        self.users_file.write_text(json.dumps(users, indent=2))

    def _create_session(self, username: str) -> None:
        sessions = {username: True}
        self.sessions_file.write_text(json.dumps(sessions, indent=2))

    def _clear_session(self) -> None:
        self.sessions_file.write_text("{}")

    def get_current_user(self) -> Optional[str]:
        if self.sessions_file.exists():
            sessions = json.loads(self.sessions_file.read_text())
            return next(iter(sessions.keys()), None)
        return None