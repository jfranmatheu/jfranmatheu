import os
import requests
from github import Github
from datetime import datetime
import json
from typing import Dict, List
from operator import itemgetter
import re

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
            with open('repo_cards.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config file if it doesn't exist
            default_config = {
                "categories": {
                    "Main Projects": {
                        "description": "Primary repositories",
                        "repositories": {
                            "awesome-project": {
                                "description_override": None,
                                "priority": 1,
                                "tags": ["featured", "production"],
                                "showcase": True,
                                "custom_color": None,
                                "dev_state": "RELEASE"
                            }
                        }
                    }
                },
                "settings": {
                    "sort_by": "popularity",
                    "sort_direction": "desc",
                    "max_cards": 10,
                    "show_tags": True
                }
            }
            with open('repo_cards.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def get_repo_info(self, repo, metadata: Dict) -> Dict:
        """Extract and combine repository information with metadata"""
        base_info = {
            "dev_state": metadata.get("dev_state", "RELEASE").upper(),
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
        # Define theme colors
        theme = {
            "dark": {
                "bg": "#0d1117",
                "stroke": "#30363d",
                "text": "#c9d1d9",
                "link": "#58a6ff",
                "secondary": "#8b949e"
            },
            "light": {
                "bg": "#ffffff",
                "stroke": "#e1e4e8",
                "text": "#24292e",
                "link": "#0366d6",
                "secondary": "#586069"
            }
        }


        svg_template = f'''
        <svg width="400" height="140" viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
            <style>
                .card {{ fill: var(--card-bg, {theme['light']['bg']}); }}
                .card-stroke {{ stroke: var(--card-stroke, {theme['light']['stroke']}); }}
                .text {{ fill: var(--card-text, {theme['light']['text']}); }}
                .text-secondary {{ fill: var(--card-secondary, {theme['light']['secondary']}); }}
                .text-link {{ fill: var(--card-link, {theme['light']['link']}); }}
                
                @media (prefers-color-scheme: dark) {{
                    .card {{ fill: {theme['dark']['bg']}; }}
                    .card-stroke {{ stroke: {theme['dark']['stroke']}; }}
                    .text {{ fill: {theme['dark']['text']}; }}
                    .text-secondary {{ fill: {theme['dark']['secondary']}; }}
                    .text-link {{ fill: {theme['dark']['link']}; }}
                }}
            </style>

            <a href="{repo_info['url']}" target="_blank">
                <rect x="0" y="0" rx="10" ry="10" width="400" height="140" 
                    class="card card-stroke" stroke-width="1"/>
                
                <!-- Repository Icon -->
                <svg x="20" y="20" width="30" height="30" viewBox="0 0 16 16">
                    <path class="text-secondary" d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z"/>
                </svg>
                
                <!-- Repository Name and Dev State -->
                <text x="60" y="45" font-family="Arial, sans-serif" font-size="16" font-weight="600" class="text-link">
                    {repo_info['name']}
                    <tspan x="350" text-anchor="end" font-size="12" class="text-secondary">
                        {repo_info['dev_state']}
                    </tspan>
                </text>
                
                <!-- Repository Description -->
                <text x="20" y="80" font-family="Arial, sans-serif" font-size="14" class="text">
                    <tspan>{repo_info['description'][:50]}</tspan>
                    <tspan x="20" dy="18">{repo_info['description'][50:100] if len(repo_info['description']) > 50 else ""}</tspan>
                </text>
                
                <!-- Language Info -->
                <circle cx="20" cy="120" r="6" fill="{repo_info['language_color']}"/>
                <text x="35" y="125" font-family="Arial, sans-serif" font-size="12" class="text-secondary">
                    {repo_info['language']}
                </text>
                
                <!-- Stats -->
                <text x="320" y="125" font-family="Arial, sans-serif" font-size="12" class="text-secondary">
                    ★ {repo_info['stars']} 🔀 {repo_info['forks']}
                </text>
            </a>
        </svg>
        '''
        return svg_template.strip()

    def update_readme(self, cards_content: str):
        # Read the README.md file
        with open('README.md', 'r', encoding='utf-8') as file:
            content = file.read()

        # Define the pattern to match only the repo-cards div block
        pattern = r'<div id="repo-cards"[^>]*>\s*(?:\n|.)*?\n</div>\s*\n*'
        
        # Check if pattern exists
        if re.search(pattern, content, flags=re.MULTILINE):
            # Replace the matched content
            new_content = re.sub(pattern, cards_content, content, flags=re.MULTILINE)
        else:
            # Append to the end of the file
            new_content = content.rstrip() + "\n\n" + cards_content + "\n"
        
        # Write the modified content back to the file
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(new_content)

    def generate_cards(self, username: str):
        """Generate SVG cards for repositories based on configuration"""
        user = self.github.get_user(username)
        output_dir = "repo-cards"
        settings = self.config["settings"]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Start the grid container that will wrap everything
        readme_content = '<div id="repo-cards" align="center" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; padding: 10px;">\n\n'
        
        # Process each category
        for category_name, category_data in self.config["categories"].items():
            # Add category header and description using markdown
            readme_content += f'### {category_name}\n\n'
            if category_data.get("description"):
                readme_content += f'{category_data["description"]}\n\n'
            
            # Collect and sort repositories for this category
            repos_data = []
            for repo_name, repo_metadata in category_data["repositories"].items():
                try:
                    repo = user.get_repo(repo_name)
                    repo_info = self.get_repo_info(repo, repo_metadata)
                    repos_data.append(repo_info)
                    print(f"{category_name} -> {repo_name}")
                except Exception as e:
                    print(f"Error processing {repo_name}: {e}")

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

            # Generate cards
            for repo_info in repos_data:
                svg_content = self.create_svg(repo_info)
                
                # Save SVG file
                filename = f"{output_dir}/{repo_info['name']}-card.svg"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(svg_content)
                
                # Add to README with link wrapper
                readme_content += f'<a href="{repo_info["url"]}" target="_blank"><img src="{filename}" alt="{repo_info["name"]}" style="width: 100%; max-width: 400px;"></a>\n\n'

            # Add spacing between categories
            readme_content += '---\n\n'
        
        # Close the main grid container
        readme_content += '</div>\n\n'
        
        # Update README
        self.update_readme(readme_content)
        
        # Generate metadata file
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "total_repositories": sum(len(cat["repositories"]) for cat in self.config["categories"].values()),
            "categories": {name: {
                "count": len(data["repositories"]),
                "total_stars": sum(repo["stars"] for repo in repos_data),
                "total_forks": sum(repo["forks"] for repo in repos_data)
            } for name, data in self.config["categories"].items()},
            "repositories": [repo for cat in self.config["categories"].values() 
                           for repo_name, _ in cat["repositories"].items()]
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
