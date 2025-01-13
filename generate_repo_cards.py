import os
import requests
from github import Github
from datetime import datetime
import json
from typing import Dict, List, Optional
from operator import itemgetter
from collections import defaultdict

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
        
        # Load configuration
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load configuration from config file"""
        try:
            with open('repo_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config file if it doesn't exist
            default_config = {
                "categories": {
                    "Frontend": {
                        "description": "Frontend development projects",
                        "color": "#41b883",
                        "icon": "🎨",
                        "priority": 1
                    },
                    "Backend": {
                        "description": "Backend and API projects",
                        "color": "#3572A5",
                        "icon": "⚙️",
                        "priority": 2
                    },
                    "Tools": {
                        "description": "Development tools and utilities",
                        "color": "#f1e05a",
                        "icon": "🔧",
                        "priority": 3
                    }
                },
                "repositories": {
                    "awesome-frontend": {
                        "category": "Frontend",
                        "description_override": None,
                        "priority": 1,
                        "tags": ["featured", "production"],
                        "showcase": True,
                        "custom_color": None
                    },
                    "api-service": {
                        "category": "Backend",
                        "description_override": None,
                        "priority": 1,
                        "tags": ["api", "stable"],
                        "showcase": True,
                        "custom_color": None
                    }
                },
                "settings": {
                    "sort_by": "popularity",
                    "sort_direction": "desc",
                    "max_cards_per_category": 5,
                    "show_tags": True,
                    "show_category_descriptions": True,
                    "layout": "grid"  # or "list"
                }
            }
            with open('repo_config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config

    def get_repo_info(self, repo, metadata: Dict) -> Dict:
        """Extract and combine repository information with metadata"""
        category = metadata.get("category", "Uncategorized")
        category_data = self.config["categories"].get(category, {})
        
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
            "showcase": metadata.get("showcase", True),
            "category": category,
            "category_color": category_data.get("color", "#888888"),
            "category_icon": category_data.get("icon", "📁")
        }
        
        # Calculate popularity score
        base_info["popularity_score"] = (
            base_info["stars"] * 2 + 
            base_info["forks"] * 3 + 
            (1000 if base_info["showcase"] else 0) +
            (500 * (10 - metadata.get("priority", 5)))  # Higher priority gives better score
        )
        
        return base_info

    def create_svg(self, repo_info: Dict) -> str:
        """Generate SVG card for a repository with category styling"""
        tags_display = " • ".join(repo_info["tags"]) if repo_info["tags"] else ""
        
        svg_template = f'''
        <svg width="400" height="140" viewBox="0 0 400 140" xmlns="http://www.w3.org/2000/svg">
            <a href="{repo_info['url']}" target="_blank">
                <!-- Card Background -->
                <rect x="0" y="0" rx="10" ry="10" width="400" height="140" 
                    fill="#ffffff" stroke="{repo_info['category_color']}" stroke-width="2"/>
                
                <!-- Category Badge -->
                <rect x="20" y="15" rx="5" ry="5" width="auto" height="20" 
                    fill="{repo_info['category_color']}" fill-opacity="0.1"/>
                <text x="30" y="30" font-family="Arial, sans-serif" font-size="12" fill="{repo_info['category_color']}">
                    {repo_info['category_icon']} {repo_info['category']}
                </text>
                
                <!-- Repository Name -->
                <text x="20" y="60" font-family="Arial, sans-serif" font-size="16" font-weight="600" fill="#0366d6">
                    {repo_info['name']}
                </text>
                
                <!-- Repository Description -->
                <text x="20" y="85" font-family="Arial, sans-serif" font-size="14" fill="#586069">
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
                {f'<text x="150" y="125" font-family="Arial, sans-serif" font-size="10" fill="#6a737d">{tags_display}</text>' if repo_info["tags"] else ""}
            </a>
        </svg>
        '''
        return svg_template.strip()

    def generate_cards(self, username: str):
        """Generate SVG cards for repositories organized by categories"""
        user = self.github.get_user(username)
        output_dir = "repo-cards"
        settings = self.config["settings"]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Collect repositories by category
        categorized_repos = defaultdict(list)
        for repo in user.get_repos():
            if repo.name in self.config["repositories"]:
                repo_metadata = self.config["repositories"][repo.name]
                repo_info = self.get_repo_info(repo, repo_metadata)
                category = repo_metadata.get("category", "Uncategorized")
                categorized_repos[category].append(repo_info)
        
        # Sort categories by priority
        sorted_categories = sorted(
            self.config["categories"].items(),
            key=lambda x: x[1].get("priority", 999)
        )
        
        # Generate README content
        readme_content = "# Repository Showcase\n\n"
        
        # Process each category
        for category_name, category_data in sorted_categories:
            if category_name in categorized_repos:
                repos_in_category = categorized_repos[category_name]
                
                # Sort repositories within category
                sort_key = {
                    "stars": "stars",
                    "priority": "priority",
                    "name": "name",
                    "popularity": "popularity_score"
                }.get(settings["sort_by"], "popularity_score")
                
                repos_in_category.sort(
                    key=itemgetter(sort_key),
                    reverse=(settings["sort_direction"] == "desc")
                )
                
                # Limit cards per category
                if settings["max_cards_per_category"]:
                    repos_in_category = repos_in_category[:settings["max_cards_per_category"]]
                
                # Add category section to README
                readme_content += f'\n## {category_data["icon"]} {category_name}\n'
                if settings["show_category_descriptions"]:
                    readme_content += f'\n{category_data["description"]}\n'
                
                readme_content += '\n<div align="center">\n\n'
                
                # Generate cards for this category
                for repo_info in repos_in_category:
                    svg_content = self.create_svg(repo_info)
                    filename = f"{output_dir}/{repo_info['name']}-card.svg"
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(svg_content)
                    
                    # Add to README with category-specific styling
                    readme_content += f'<img src="{filename}" alt="{repo_info["name"]}" style="margin: 10px">\n\n'
                
                readme_content += "</div>\n\n"
        
        # Save README section
        with open("REPO_CARDS.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        # Generate metadata file with category information
        metadata = {
            "last_updated": datetime.now().isoformat(),
            "categories": {
                category: {
                    "total_repositories": len(repos),
                    "total_stars": sum(repo["stars"] for repo in repos),
                    "total_forks": sum(repo["forks"] for repo in repos),
                    "repositories": repos
                }
                for category, repos in categorized_repos.items()
            }
        }
        
        with open(f"{output_dir}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("Please set the GITHUB_TOKEN environment variable")
    
    username = os.getenv("GITHUB_USERNAME")
    if not username:
        raise ValueError("Please set the GITHUB_USERNAME environment variable")
    
    generator = RepoCardGenerator(github_token)
    generator.generate_cards(username)
