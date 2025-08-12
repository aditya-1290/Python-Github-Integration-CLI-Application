from rich.tree import Tree
from rich import print

def display_repo_tree(github_manager):
    """Display repository tree structure"""
    if not github_manager.current_repo:
        print("[red]No repository selected")
        return
    
    tree = github_manager.get_repo_tree()
    print(tree)