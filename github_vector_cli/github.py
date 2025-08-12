from github import Github, GithubException
from github.Repository import Repository
from github.ContentFile import ContentFile
from typing import List, Dict, Optional
from pathlib import Path
import os
import json
from rich.tree import Tree
from rich import print

class GitHubManager:
    def __init__(self, token: Optional[str] = None, data_dir: str = ".github_vector_cli"):
        self.gh = Github(token) if token else None
        self.data_dir = Path(data_dir)
        self.current_repo: Optional[Repository] = None
        self.repo_state_file = self.data_dir / "selected_repo.json"
        self._load_selected_repo()

    def _load_selected_repo(self) -> None:
        """Load the previously selected repository from file"""
        if self.repo_state_file.exists():
            try:
                state = json.loads(self.repo_state_file.read_text())
                repo_name = state.get("selected_repo")
                if repo_name and self.gh:
                    try:
                        self.current_repo = self.gh.get_user().get_repo(repo_name)
                    except GithubException:
                        # Repository no longer exists or access revoked
                        self.repo_state_file.unlink(missing_ok=True)
            except (json.JSONDecodeError, GithubException):
                # Invalid state file, remove it
                self.repo_state_file.unlink(missing_ok=True)

    def _save_selected_repo(self, repo_name: str) -> None:
        """Save the selected repository to file"""
        self.data_dir.mkdir(exist_ok=True)
        state = {"selected_repo": repo_name}
        self.repo_state_file.write_text(json.dumps(state, indent=2))

    def _clear_selected_repo(self) -> None:
        """Clear the selected repository state"""
        self.repo_state_file.unlink(missing_ok=True)

    def is_authenticated(self) -> bool:
        return self.gh is not None

    def get_repos(self) -> List[str]:
        if not self.gh:
            raise ValueError("GitHub not authenticated")
        return [repo.name for repo in self.gh.get_user().get_repos()]

    def set_current_repo(self, repo_name: str) -> None:
        if not self.gh:
            raise ValueError("GitHub not authenticated")
        self.current_repo = self.gh.get_user().get_repo(repo_name)
        self._save_selected_repo(repo_name)

    def get_repo_tree(self, path: str = "") -> Tree:
        if not self.current_repo:
            raise ValueError("No repository selected")
        
        tree = Tree(f"[bold green]{self.current_repo.name}")
        contents = self.current_repo.get_contents(path)
        
        for content in contents:
            if content.type == "dir":
                branch = tree.add(f"[blue]{content.name}")
                self._add_directory_contents(branch, content.path)
            else:
                tree.add(f"[yellow]{content.name}")
        
        return tree

    def _add_directory_contents(self, tree: Tree, path: str) -> None:
        contents = self.current_repo.get_contents(path)
        for content in contents:
            if content.type == "dir":
                branch = tree.add(f"[blue]{content.name}")
                self._add_directory_contents(branch, content.path)
            else:
                tree.add(f"[yellow]{content.name}")

    def get_file_content(self, file_path: str) -> str:
        if not self.current_repo:
            raise ValueError("No repository selected")
        
        try:
            content = self.current_repo.get_contents(file_path)
            if isinstance(content, list):
                raise ValueError("Path is a directory, not a file")
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            raise ValueError(f"Error fetching file: {e}")

    def search_repo(self, query: str) -> Dict[str, str]:
        if not self.current_repo:
            raise ValueError("No repository selected")
        
        results = {}
        contents = self._get_all_contents(self.current_repo)
        
        for item in contents:
            if query.lower() in item.path.lower():
                results[item.path] = item.download_url
        
        return results

    def _get_all_contents(self, repo: Repository, path: str = "") -> List[ContentFile]:
        contents = []
        try:
            items = repo.get_contents(path)
            for item in items:
                if item.type == "dir":
                    contents.extend(self._get_all_contents(repo, item.path))
                else:
                    contents.append(item)
            return contents
        except GithubException:
            return []
        