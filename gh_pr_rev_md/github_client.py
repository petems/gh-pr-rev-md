"""GitHub API client for fetching PR review comments."""

import requests
from typing import List, Dict, Any, Optional


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""

    pass


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.graphql_url = "https://api.github.com/graphql"
        self.session = requests.Session()
        headers: Dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gh-pr-rev-md",
        }
        if token:
            headers["Authorization"] = f"bearer {token}"
        self.session.headers.update(headers)

    def get_pr_review_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        include_outdated: bool = False,
        include_resolved: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch review comments for a PR using the GraphQL API."""
        comments = []
        threads_cursor = None

        while True:
            query, variables = self._build_graphql_query(
                owner, repo, pr_number, threads_cursor
            )
            response = self.session.post(
                self.graphql_url, json={"query": query, "variables": variables}, timeout=30
            )

            if response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )

            data = response.json()
            if "errors" in data:
                raise GitHubAPIError(f"GitHub GraphQL API error: {data['errors']}")

            pr_data = data.get("data", {}).get("repository", {}).get("pullRequest")
            if not pr_data:
                raise GitHubAPIError(f"PR #{pr_number} not found in {owner}/{repo}")

            review_threads = pr_data.get("reviewThreads", {})
            for thread in review_threads.get("nodes", []):
                if not include_resolved and thread.get("isResolved"):
                    continue

                # Handle pagination within each thread's comments
                thread_comments = self._get_all_thread_comments(
                    thread, owner, repo, pr_number, include_outdated
                )
                comments.extend(thread_comments)

            if review_threads.get("pageInfo", {}).get("hasNextPage"):
                threads_cursor = review_threads["pageInfo"]["endCursor"]
            else:
                break

        return sorted(comments, key=lambda c: c.get("createdAt", ""))

    def _get_all_thread_comments(
        self,
        thread: Dict[str, Any],
        owner: str,
        repo: str,
        pr_number: int,
        include_outdated: bool,
    ) -> List[Dict[str, Any]]:
        """Get all comments from a thread, handling pagination within the thread."""
        comments = []
        
        # Get comments from the initial thread data
        thread_comments_data = thread.get("comments", {})
        for comment in thread_comments_data.get("nodes", []):
            if not include_outdated and self._is_outdated(comment):
                continue
            comments.append(self._format_graphql_comment(comment))
        
        # If there are more comments in this thread, paginate through them
        comments_page_info = thread_comments_data.get("pageInfo", {})
        if comments_page_info.get("hasNextPage"):
            thread_id = thread.get("id")
            if thread_id:
                additional_comments = self._get_additional_thread_comments(
                    thread_id, comments_page_info.get("endCursor"), include_outdated
                )
                comments.extend(additional_comments)
        
        return comments

    def _get_additional_thread_comments(
        self, thread_id: str, comments_cursor: str, include_outdated: bool
    ) -> List[Dict[str, Any]]:
        """Fetch additional comments for a specific thread using pagination."""
        comments = []
        
        while comments_cursor:
            query = """
            query($threadId: ID!, $commentsCursor: String) {
              node(id: $threadId) {
                ... on PullRequestReviewThread {
                  comments(first: 100, after: $commentsCursor) {
                    pageInfo {
                      endCursor
                      hasNextPage
                    }
                    nodes {
                      id
                      author {
                        login
                      }
                      body
                      createdAt
                      updatedAt
                      path
                      diffHunk
                      position
                      url
                      line
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "threadId": thread_id,
                "commentsCursor": comments_cursor,
            }
            
            response = self.session.post(
                self.graphql_url, json={"query": query, "variables": variables}, timeout=30
            )
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            if "errors" in data:
                raise GitHubAPIError(f"GitHub GraphQL API error: {data['errors']}")
            
            thread_data = data.get("data", {}).get("node", {})
            thread_comments_data = thread_data.get("comments", {})
            
            for comment in thread_comments_data.get("nodes", []):
                if not include_outdated and self._is_outdated(comment):
                    continue
                comments.append(self._format_graphql_comment(comment))
            
            # Check if there are more pages
            comments_page_info = thread_comments_data.get("pageInfo", {})
            if comments_page_info.get("hasNextPage"):
                comments_cursor = comments_page_info.get("endCursor")
            else:
                break
        
        return comments

    def _is_outdated(self, comment: Dict[str, Any]) -> bool:
        """Determines if a comment is outdated."""
        # In the GraphQL response, outdated comments have a null position.
        return comment.get("position") is None

    def _format_graphql_comment(self, comment: Dict[str, Any]) -> Dict[str, Any]:
        """Formats a GraphQL comment object to match the structure of the REST API response."""
        return {
            "id": comment.get("id"),
            "user": {"login": comment.get("author", {}).get("login")},
            "body": comment.get("body"),
            "created_at": comment.get("createdAt"),
            "updated_at": comment.get("updatedAt"),
            "path": comment.get("path"),
            "diff_hunk": comment.get("diffHunk"),
            "line": comment.get("line"),
            "position": comment.get("position"),
            "html_url": comment.get("url"),
            # The 'side' isn't directly available in the same way,
            # but we can use the outdated status to infer it.
            "side": "LEFT" if self._is_outdated(comment) else "RIGHT",
        }

    def _build_graphql_query(
        self, owner: str, repo: str, pr_number: int, threads_cursor: Optional[str]
    ):
        """Builds the GraphQL query and variables for fetching review threads."""
        query = """
        query($owner: String!, $repo: String!, $prNumber: Int!, $threadsCursor: String) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $prNumber) {
              reviewThreads(first: 100, after: $threadsCursor) {
                pageInfo {
                  endCursor
                  hasNextPage
                }
                nodes {
                  id
                  isResolved
                  comments(first: 100) {
                    pageInfo {
                      endCursor
                      hasNextPage
                    }
                    nodes {
                      id
                      author {
                        login
                      }
                      body
                      createdAt
                      updatedAt
                      path
                      diffHunk
                      position
                      url
                      line
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "owner": owner,
            "repo": repo,
            "prNumber": pr_number,
            "threadsCursor": threads_cursor,
        }
        return query, variables

    def get_authenticated_user(self) -> str:
        """Get the login of the authenticated user.

        Returns:
            The login of the authenticated user.

        Raises:
            GitHubAPIError: If the API call fails or the response is invalid.
        """
        query = "{ viewer { login } }"
        try:
            response = self.session.post(
                self.graphql_url, json={"query": query}, timeout=30
            )
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )
            data = response.json()
            if "errors" in data:
                raise GitHubAPIError(f"GitHub GraphQL API error: {data['errors']}")
            return data["data"]["viewer"]["login"]
        except (requests.RequestException, KeyError, TypeError) as exc:
            raise GitHubAPIError(
                f"Failed to get authenticated user: {exc}"
            ) from exc

    def find_pr_by_branch(self, owner: str, repo: str, branch_name: str) -> Optional[int]:
        """Find the PR number for a given branch name."""
        query = """
        query($owner: String!, $repo: String!, $branchName: String!) {
          repository(owner: $owner, name: $repo) {
            pullRequests(first: 10, states: [OPEN], headRefName: $branchName) {
              nodes {
                number
                headRefName
                state
              }
            }
          }
        }
        """
        variables = {
            "owner": owner,
            "repo": repo,
            "branchName": branch_name,
        }

        response = self.session.post(
            self.graphql_url, json={"query": query, "variables": variables}, timeout=30
        )

        if response.status_code != 200:
            raise GitHubAPIError(
                f"GitHub API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        if "errors" in data:
            raise GitHubAPIError(f"GitHub GraphQL API error: {data['errors']}")

        prs = data.get("data", {}).get("repository", {}).get("pullRequests", {}).get("nodes", [])
        
        # Return the first open PR for this branch
        for pr in prs:
            if pr.get("state") == "OPEN" and pr.get("headRefName") == branch_name:
                return pr.get("number")
        
        return None