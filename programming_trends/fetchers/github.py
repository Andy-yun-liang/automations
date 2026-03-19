import datetime
from github import Github, Auth
from config import GITHUB_TOKEN, GITHUB_QUERIES


def fetch_github(max_per_query: int = 5) -> list:
    if not GITHUB_TOKEN:
        print("  [skip] GITHUB_TOKEN not set")
        return []

    gh    = Github(auth=Auth.Token(GITHUB_TOKEN))
    since = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    items = []

    for query in GITHUB_QUERIES:
        try:
            results = gh.search_repositories(f"{query} created:>{since}", sort="stars", order="desc")
            for repo in results[:max_per_query]:
                items.append({
                    "title":       repo.full_name,
                    "url":         repo.html_url,
                    "description": (repo.description or "") + f" | ⭐ {repo.stargazers_count}",
                    "source":      "GitHub",
                })
        except Exception as e:
            print(f"  [github] error on '{query}': {e}")

    return items
