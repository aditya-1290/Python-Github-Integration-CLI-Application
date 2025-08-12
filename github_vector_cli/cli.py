import typer
from typing import Optional
from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress

from .auth import AuthManager
from .github import GitHubManager
from .chroma import VectorDBManager
from .utils.tree import display_repo_tree
from .plugins import load_plugins

app = typer.Typer(help="GitHub CLI with ChromaDB Integration")
auth_manager = AuthManager()
vector_db = VectorDBManager()

# Initialize github_manager as None - will be set when needed
github_manager: Optional[GitHubManager] = None

# Load plugins
plugin_commands = load_plugins(app)

def get_github_manager() -> GitHubManager:
    """Get or create GitHubManager instance with proper authentication"""
    global github_manager
    
    # If already exists, return it
    if github_manager is not None:
        return github_manager
    
    # Otherwise create new instance with proper auth
    username = auth_manager.get_current_user()
    if not username:
        raise typer.BadParameter("You must be logged in to perform this action")
    
    github_token = auth_manager.get_github_token(username)
    if not github_token:
        raise typer.BadParameter("GitHub token not set. Use 'set-github-token' first")
    
    github_manager = GitHubManager(github_token)
    return github_manager

@app.command()
def register(username: str = typer.Option(..., prompt=True),
             password: str = typer.Option(..., prompt=True, hide_input=True)):
    """Register a new user"""
    if auth_manager.register(username, password):
        print(f"[green]Successfully registered user {username}")
    else:
        print(f"[red]Username {username} already exists")

@app.command()
def login(username: str = typer.Option(..., prompt=True),
          password: str = typer.Option(..., prompt=True, hide_input=True)):
    """Login to the system"""
    if auth_manager.login(username, password):
        # Reset github_manager to ensure fresh state
        global github_manager
        github_manager = None
        
        print(f"[green]Successfully logged in as {username}")
        # Try to load GitHub token if exists
        token = auth_manager.get_github_token(username)
        if token:
            try:
                github_manager = GitHubManager(token)
                print("[green]GitHub token loaded automatically")
            except Exception as e:
                print(f"[yellow]Warning: Could not initialize GitHub client: {e}")
    else:
        print("[red]Invalid username or password")

@app.command()
def logout():
    """Logout from the system"""
    auth_manager.logout()
    global github_manager
    github_manager = None
    print("[green]Successfully logged out")

@app.command()
def set_github_token(token: str = typer.Option(..., prompt=True, hide_input=True)):
    """Set GitHub personal access token"""
    username = auth_manager.get_current_user()
    if not username:
        print("[red]You must be logged in to set a GitHub token")
        return
    
    auth_manager.set_github_token(username, token)
    global github_manager
    try:
        github_manager = GitHubManager(token)
        print("[green]GitHub token set successfully")
    except Exception as e:
        print(f"[red]Error initializing GitHub client: {e}")

@app.command()
def list_repos():
    """List all GitHub repositories"""
    try:
        manager = get_github_manager()
        repos = manager.get_repos()
        
        table = Table(title="Your GitHub Repositories")
        table.add_column("Repository Name", style="cyan")
        
        for repo in repos:
            table.add_row(repo)
        
        print(table)
    except Exception as e:
        print(f"[red]Error: {e}")

@app.command()
def select_repo(repo_name: str = typer.Option(..., prompt="Enter repository name")):
    """Select a repository to work with"""
    try:
        manager = get_github_manager()
        manager.set_current_repo(repo_name)
        print(f"[green]Selected repository: {repo_name}")
        display_repo_tree(manager)
    except Exception as e:
        print(f"[red]Error selecting repository: {e}")

@app.command()
def index_repo():
    """Index the selected repository into ChromaDB"""
    try:
        manager = get_github_manager()
        if not manager.current_repo:
            print("[red]No repository selected. Use 'select-repo' first")
            return
        
        repo_name = manager.current_repo.name
        print(f"[yellow]Indexing repository {repo_name}...")
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Indexing...", total=100)
            
            # Get all files from the repository
            contents = manager._get_all_contents(manager.current_repo)
            documents = {}
            
            for i, content in enumerate(contents):
                try:
                    file_content = content.decoded_content.decode("utf-8")
                    documents[content.path] = file_content
                    progress.update(task, advance=(100/len(contents)))
                except Exception as e:
                    print(f"[red]Error processing {content.path}: {e}")
                    continue
            
            # Store in ChromaDB
            vector_db.store_repository(repo_name, documents)
        
        print(f"[green]Successfully indexed repository {repo_name}")
    except Exception as e:
        print(f"[red]Error during indexing: {e}")

@app.command()
def search(query: str = typer.Option(..., prompt="Enter search query"),
           repo_name: Optional[str] = typer.Option(None)):
    """Search across indexed repositories"""
    try:
        results = vector_db.search_repository(query, repo_name)
        
        if not results:
            print("[yellow]No results found")
            return
        
        table = Table(title="Search Results")
        table.add_column("Repository", style="cyan")
        table.add_column("File Path", style="magenta")
        table.add_column("Similarity", style="green")
        table.add_column("Preview", style="yellow")
        
        for result in results:
            preview = result['content'][:50] + "..." if len(result['content']) > 50 else result['content']
            similarity = f"{1 - result['distance']:.2%}"
            table.add_row(
                result['repo'],
                result['path'],
                similarity,
                preview
            )
        
        print(table)
    except Exception as e:
        print(f"[red]Error during search: {e}")

def main():
    # Check for existing session
    username = auth_manager.get_current_user()
    if username:
        github_token = auth_manager.get_github_token(username)
        if github_token:
            try:
                global github_manager
                github_manager = GitHubManager(github_token)
                print(Panel.fit(f"Welcome back [bold green]{username}[/bold green]! You are already logged in."))
            except Exception as e:
                print(f"[yellow]Warning: Could not initialize GitHub client: {e}")
    
    app()

if __name__ == "__main__":
    main()