from pydantic import BaseModel


class RawCodeFacts(BaseModel):
    pass


class GitHubRepositoryFact:
    repository_name: str
    repository_url: str
    # description: str
    # stars: int
    # forks: int
    # open_issues: int
    raw_content: RawCodeFacts
