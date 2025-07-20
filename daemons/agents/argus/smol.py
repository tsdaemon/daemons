from typing import Callable
from smolagents import (
    CodeAgent,
    LiteLLMModel,
    LogLevel,
    ToolCallingAgent,
)
from opentelemetry import trace

from daemons.tools.jira import get_jira_tools

tracer = trace.get_tracer("daemons.agents.argus")

LOG_ANALYZER_INSTRUCTIONS = """
You are a cloud engineer who is responsible for a stability of a complex system with multiple services and home automations.
You are receiving logs from various sources, and your responsibility is to spot log records which needs to be addressed.

Please analyze the logs and provide a list of records which needs to be addressed.
If there are no issues, please return an empty list.
If there are issues, provide a list of log records.
For each record, provide a title and a record.
In title, provide a short summary of the record.
Do not add the same record multiple times.
DO NOT use variable named log!

Return your response in the following format:

```json
{
    "records": [
        {
            "title": "Title of the record",
            "record": "Record"
        }
    ]
}
```
"""

LOG_ANALYZER_DESCRIPTION = """
This agent is responsible for analyzing logs and providing a list of records which needs to be addressed.
Do not allow duplicates from him.   
"""

TICKET_FORMATTER_INSTRUCTIONS = """
You are a ticket formatter.
You are responsible for formatting log records as tickets.

You are receiving a list of log records which are identified as issues in the system.
De-duplicate the records if necessary.
Your goal is to format them as tickets.
Provide in title a short summary of the issue.
Provide a description with a summary of the issue. Description MUST have original log records formatted as markdown.


Return your response in the following format:

```json
{
    "tickets": [
        {
            "title": "Title of the ticket",
            "description": "Description of the ticket (formatted as markdown)",
        }
    ]
}
```
"""

TICKET_FORMATTER_DESCRIPTION = """
This agent is responsible for formatting log records as tickets.
"""

BACKLOG_GROOMER_INSTRUCTIONS = """
You are a backlog groomer.
You goal is to verify a proposed ticket against the current backlog.
Use available tools to search if there is an existing ticket for this issue.

If you find a ticket, and its open, return the ticket id.
If you find a ticket, and its closed, re-open it, and add a comment that the issue is still present with a log example.
If you find a ticket, and its rejected, do nothing and return the ticket id.
If you don't find a ticket, create a new one, and return the ticket id.

Return your response in the following format:
```json
{
    "ticket_id": "ticket_id"
}
"""

BACKLOG_GROOMER_DESCRIPTION = """
This agent with access to the backlog which can search and update tickets.
"""

MANAGER_INSTRUCTIONS = """
You are a manager of a team of agents.
You are responsible for managing the team and ensuring that the team is working together to achieve the goal.

You receive as an input a list of log records. The log records are formatted as ["unix_timestamp", "log_record"].
Use log_analyzer agent to analyze the logs and spot issues.
Use ticket_formatter agent to format the issues as tickets.
Use backlog_grommer agent to add tickets to the current backlog (one by one).

Make sure to count parentheses when you generate the code.

When finished, return the following JSON with a summary of the processed issues and tickets:
```json
{
    "issues": ["title of the issue", "title of the issue"],
    "tickets": ["ticket_id", "ticket_id"]
}
```
"""


class Argus:
    def __init__(
        self,
        model_id: str,
        callbacks: list[Callable] = [],
        verbose: bool = False,
    ):
        self.model_id = model_id
        self.verbose = verbose
        self.callbacks = callbacks
        
    def run(self, logs: str, hostname: str, service_name: str, unit: str | None = None):
        model = LiteLLMModel(model_id=self.model_id)
        jira_tools = get_jira_tools(service_name, hostname, unit)

        logs_analyzer_agent = ToolCallingAgent(
            tools=[],
            model=model,
            max_steps=10,
            name="log_analyzer",
            instructions=LOG_ANALYZER_INSTRUCTIONS,
            description=LOG_ANALYZER_DESCRIPTION,
            verbosity_level=LogLevel.DEBUG if self.verbose else LogLevel.OFF,
            step_callbacks=self.callbacks,
        )

        ticket_formatter_agent = ToolCallingAgent(
            tools=[],
            model=model,
            max_steps=10,
            name="ticket_formatter",
            instructions=TICKET_FORMATTER_INSTRUCTIONS,
            description=TICKET_FORMATTER_DESCRIPTION,
            verbosity_level=LogLevel.DEBUG if self.verbose else LogLevel.OFF,
            step_callbacks=self.callbacks,
        )

        backlog_groomer_agent = CodeAgent(
            tools=jira_tools,
            model=model,
            max_steps=10,
            name="backlog_groomer",
            step_callbacks=self.callbacks,
            instructions=BACKLOG_GROOMER_INSTRUCTIONS,
            description=BACKLOG_GROOMER_DESCRIPTION,
            verbosity_level=LogLevel.DEBUG if self.verbose else LogLevel.OFF,
        )

        manager_agent = ToolCallingAgent(
            tools=[],
            model=model,
            name="manager",
            max_steps=30,
            managed_agents=[
                logs_analyzer_agent,
                ticket_formatter_agent,
                backlog_groomer_agent,
            ],
            step_callbacks=self.callbacks,
            instructions=MANAGER_INSTRUCTIONS,
            verbosity_level=LogLevel.DEBUG if self.verbose else LogLevel.OFF,
        )
        
        task = f"Analyze the following logs: {logs} for host {hostname}, service {service_name}"
        if unit:
            task += f", unit {unit}"

        return manager_agent.run(
            task=task,
        )


def get_argus(model_id: str, verbose: bool):
    return Argus(
        model_id=model_id,
        verbose=verbose,
    )