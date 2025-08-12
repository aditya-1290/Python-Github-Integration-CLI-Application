from typing import Dict, Any
import typer
from rich import print
from rich.table import Table

from github_vector_cli.chroma import VectorDBManager

vector_db = VectorDBManager()

def register_plugin(app: typer.Typer) -> Dict[str, Any]:
    @app.command()
    def semantic_search(
        query: str = typer.Option(..., prompt="Enter semantic search query"),
        repo_name: str = typer.Option(None, help="Filter by repository name"),
        limit: int = typer.Option(5, help="Number of results to return")
    ):
        """Perform semantic search across indexed repositories"""
        results = vector_db.search_repository(query, repo_name, limit)
        
        if not results:
            print("[yellow]No results found")
            return
        
        table = Table(title="Semantic Search Results")
        table.add_column("Score", style="green")
        table.add_column("Repository", style="cyan")
        table.add_column("File Path", style="magenta")
        table.add_column("Preview", style="yellow")
        
        for result in results:
            score = f"{1 - result['distance']:.2%}"
            preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
            table.add_row(
                score,
                result['repo'],
                result['path'],
                preview
            )
        
        print(table)
    
    return {
        "name": "search",
        "commands": {
            "semantic-search": semantic_search
        }
    }