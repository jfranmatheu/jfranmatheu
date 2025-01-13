import os
import requests
from github import Github
from datetime import datetime
import json
from typing import Dict, List
from operator import itemgetter

class RepoCardGenerator:
    def __init__(self, github_token):
        self.github = Github(github_token)
        self.language_colors = {
            "Python": "#3572A5",
            "JavaScript": "#f1e05a",
            "TypeScript": "#2b7489",
            "Java": "#b07219",
            "C++": "#f34b7d",
            "Go": "#00ADD8",
            "Rust": "#dea584",
            "PHP": "#4F5D95",
            "Ruby": "#701516",
            "Vue": "#41b883",
            "React": "#61dafb",
            "Swift": "#ffac45"
        }
        
        # Load whitelist and metadata from config file
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load configuration from config file"""
        try:
            with open('repo_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config file if it doesn't exist
            default_config = {
                "repositories": {
                    "awesome-project": {
                        "description_override": None,
                        "priority": 1,
                        "tags": ["featured", "production"],
                        "showcase": True,
                        "custom_color": None
                    },
                    "cool-library": {
                        "description_override": None,
                        "priority": 2,
                        "tags": ["library"],
                        "showcase": True,
                        "custom_color": None
                    }
                },
                "settings": {
                    "sort_by": "stars",  # stars, priority, name
                    "sort_direction": "desc",
                    "max_cards": 10,
                    "show_tags": True
                }
            }
            with open('repo_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def get_repo_info(self, repo, metadata: Dict) -> Dict:
        """Extract and combine repository information with metadata"""
        base_info = {
            "name": repo.name,
            "description": metadata.get("description_override") or repo.description or "No description available",
            "url": repo.html_url,
            "language": repo.language or "None",
            "language_color": metadata.get("custom_color") or self.language_colors.get(repo.language, "#888888"),
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "priority": metadata.get("priority", 999),
            "tags": metadata.get("tags", []),
            "updated_at": repo.updated_at.isoformat(),
            "size": repo.size,
            "showcase": metadata.get("showcase", True)
        }
        
        # Calculate popularity score
        base_info["popularity_score"] = (
            base_info["stars"] * 2 + 
            base_info["forks"] * 3 + 
            (1000 if base_info["showcase"] else 0)
        )
        
        return base_info

    def create_svg(self, repo_info: Dict) -> str:
        """Generate SVG card for a repository"""
        # Format tags for display
        tags_display = " • ".join(repo_info["tags"]) if repo_info["tags"] else ""
        
        svg_template = f'''
        <svg width="400" height="140" viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
            <a href="{repo_info['url']}" target="_blank">
                <rect x="0" y="0" rx="10" ry="10" width="400" height="140" 
                    fill="#ffffff" stroke="#e1e4e8" stroke-width="1"/>
                
                <!-- Repository Icon -->
                <svg x="20" y="20" width="30" height="30" viewBox="0 0 16 16">
                    <path fill="#586069" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
                </svg>
                
                <!-- Repository Name -->
                <text x="60" y="45" font-family="Arial, sans-serif" font-size="16" font-weight="600" fill="#0366d6">
                    {repo_info['name']}
                </text>
                
                <!-- Repository Description -->
                <text x="20" y="80" font-family="Arial, sans-serif" font-size="14" fill="#586069">
                    <tspan>{repo_info['description'][:50]}</tspan>
                    <tspan x="20" dy="18">{repo_info['description'][50:100] if len(repo_info['description']) > 50 else ""}</tspan>
                </text>
                
                <!-- Language Info -->
                <circle cx="20" cy="120" r="6" fill="{repo_info['language_color']}"/>
                <text x="35" y="125" font-family="Arial, sans-serif" font-size="12" fill="#586069">
                    {repo_info['language']}
                </text>
                
                <!-- Stats -->
                <text x="320" y="125" font-family="Arial, sans-serif" font-size="12" fill="#586069">
                    ★ {repo_info['stars']} 🔀 {repo_info['forks']}
                </text>
                
                <!-- Tags -->
                <text x="20" y="25" font-family="Arial, sans-serif" font-size="10" fill="#6a737d">
                    {tags_display}
                </text>
            </a>
        </svg>
        '''
        return svg_template.strip()

    def generate_cards(self, username: str):
        """Generate SVG cards for repositories based on configuration"""
        user = self.github.get_user(username)
        output_dir = "repo-cards"
        settings = self.config["settings"]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect and sort repositories
        repos_data = []
        for repo in user.get_repos():
            if repo.name in self.config["repositories"]:
                repo_metadata = self.config["repositories"][repo.name]
                repo_info = self.get_repo_info(repo, repo_metadata)
                repos_data.append(repo_info)
        
        # Sort repositories based on settings
        sort_key = {
            "stars": "stars",
            "priority": "priority",
            "name": "name",
            "popularity": "popularity_score"
        }.get(settings["sort_by"], "stars")
        
        repos_data.sort(
            key=itemgetter(sort_key),
            reverse=(settings["sort_direction"] == "desc")
        )
        
        # Limit number of cards if specified
        if settings["max_cards"]:
            repos_data = repos_data[:settings["max_cards"]]
        
        # Generate README content
        readme_content = "# Featured Repositories\n\n<div align=\"center\">\n\n"
        
        # Generate cards
        for repo_info in repos_data:
            svg_content = self.create_svg(repo_info)
            
            # Save SVG file
            filename = f"{output_dir}/{repo_info['name']}-card.svg"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(svg_content)
            
            # Add to README
            readme_content += f'<img src="{filename}" alt="{repo_info["name"]}" style="margin: 10px">\n\n'
        
        readme_content += "</div>"
        
        # Save README section
        with open("REPO_CARDS.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        # Generate metadata file
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "total_repositories": len(repos_data),
            "total_stars": sum(repo["stars"] for repo in repos_data),
            "total_forks": sum(repo["forks"] for repo in repos_data),
            "repositories": repos_data
        }
        
        with open(f"{output_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    # Get GitHub token from environment variable
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("Please set the GITHUB_TOKEN environment variable")
    
    # Get username from environment variable or use as parameter
    username = os.getenv("GITHUB_USERNAME")
    if not username:
        raise ValueError("Please set the GITHUB_USERNAME environment variable")
    
    generator = RepoCardGenerator(github_token)
    generator.generate_cards(username)
