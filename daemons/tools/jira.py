import os

from jira import JIRA
from smolagents import Tool


def get_jira_tools(service_name: str, hostname: str, unit: str = None):
    client = JIRA(
        server="https://tsdaemon.atlassian.net",
        basic_auth=(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_KEY"]),
    )
    return [
        JiraTicketSearchTool(jira_client=client, service_name=service_name, hostname=hostname, unit=unit),
        JiraTicketCreateTool(jira_client=client, service_name=service_name, hostname=hostname, unit=unit),
        JiraTicketReopenTool(jira_client=client, service_name=service_name, hostname=hostname, unit=unit),
        JiraTicketCommentTool(jira_client=client, service_name=service_name, hostname=hostname, unit=unit),
    ]


class JiraTool(Tool):
    def __init__(self, jira_client: JIRA, service_name: str, hostname: str, unit: str = None):
        super().__init__()
        self.jira = jira_client
        self.service_name = service_name
        self.hostname = hostname
        self.unit = unit

class JiraTicketSearchTool(JiraTool):
    name = "jira_ticket_search"
    description = """
    This tool allows you to search for tickets in Jira. Use as keywords ONLY specific words that are related to the issue you are looking for.
    """
    inputs = {
        "keywords": {
            "type": "string",
            "description": "the keywords to search for",
        }
    }
    output_type = "string"

    def forward(self, keywords: str):
        issues = self.jira.search_issues(f'project=THES AND text ~ "{keywords} {self.service_name} {self.hostname} {self.unit}"')
        return [
            {
                "id": issue.key,
                "title": issue.fields.summary,
                "status": str(issue.fields.status.name),
            }
            for issue in issues
        ]


class JiraTicketCreateTool(JiraTool):
    name = "jira_ticket_create"
    description = """
    This tool allows you to create a new ticket in Jira.
    """
    inputs = {
        "title": {
            "type": "string",
            "description": "the title of the ticket to create",
        },
        "description": {
            "type": "string",
            "description": "the description of the ticket to create",
        },
    }
    output_type = "string"

    def forward(self, title: str, description: str):
        issue = self.jira.create_issue(
            project="THES",
            summary=f"[{self.service_name} {self.hostname}{f' / {self.unit}' if self.unit else ''}] {title}",
            description=description,
            issuetype={"name": "Bug"},
        )
        return issue.key


class JiraTicketReopenTool(JiraTool):
    name = "jira_ticket_reopen"
    description = """
    This tool allows you to reopen a ticket in Jira.
    """
    inputs = {
        "ticket_id": {
            "type": "string",
            "description": "the id of the ticket to reopen",
        }
    }
    output_type = "string"

    def forward(self, ticket_id: str):
        self.jira.transition_issue(ticket_id, "11")
        return ticket_id


class JiraTicketCommentTool(JiraTool):
    name = "jira_ticket_comment"
    description = """
    This tool allows you to comment on a ticket in Jira.
    """
    inputs = {
        "ticket_id": {
            "type": "string",
            "description": "the id of the ticket to comment on",
        },
        "comment": {
            "type": "string",
            "description": "the comment to add to the ticket",
        },
    }
    output_type = "string"

    def forward(self, ticket_id: str, comment: str):
        self.jira.add_comment(ticket_id, comment)
        return ticket_id
