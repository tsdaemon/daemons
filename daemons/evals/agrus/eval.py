from pprint import pprint
from jira import JIRA
import numpy as np
import yaml
from pathlib import Path

from daemons.agents.argus.smol import Argus
from daemons.tools.jira import JiraTicketCommentTool, JiraTicketCreateTool, JiraTicketReopenTool, JiraTicketSearchTool
from unittest.mock import Mock

from smolagents import (
    WebSearchTool,
)

def get_argus_and_tools(model_id: str, verbose: bool) -> Argus:
    jira_client = Mock(spec=JIRA)
    jira_client.search_issues = Mock(return_value=[])
    jira_tools = [
        JiraTicketSearchTool(jira_client=jira_client),
        JiraTicketCreateTool(jira_client=jira_client),
        JiraTicketReopenTool(jira_client=jira_client),
        JiraTicketCommentTool(jira_client=jira_client),
    ]
    web_search_tool = WebSearchTool()

    steps = []
    def callback(step, agent):
        steps.append((agent.name, step))

    argus = Argus(
        model_id=model_id,
        verbose=verbose,
        jira_tools=jira_tools,
        web_search_tool=web_search_tool,
        callbacks=[callback],
    )

    return argus, jira_client, web_search_tool, steps


def eval_argus(model_id: str, verbose: bool) -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        eval_config = yaml.safe_load(f)
    expected_steps_percent = []
    wrong_steps_percent = []

    for case in eval_config["cases"]:
        argus, jira_client, web_search_tool, steps = get_argus_and_tools(model_id, verbose)
        result = argus.run(case["inputs"]["logs"])
        evaluation = evaluate_case(
            case,
            result,
            jira_client,
            web_search_tool,
            steps,
        )
        expected_steps_percent.append(evaluation["expected_steps_percent"])
        wrong_steps_percent.append(evaluation["wrong_steps_percent"])
        if verbose:
            log_yaml_dict = {
                "case": case["name"],
                "expected_steps_percent": evaluation["expected_steps_percent"],
                "wrong_steps_percent": evaluation["wrong_steps_percent"],
                "steps": [{agent: step.observations} for agent, step in steps],
                "result": result,
            }
            with open(f"evaluation_log.yaml", "a") as f:
                yaml.dump(log_yaml_dict, f)
                f.write("---\n")

    report = {
        "expected_steps_percent": np.mean(expected_steps_percent),
        "wrong_steps_percent": np.mean(wrong_steps_percent),
    }

    return report

def evaluate_case(case, result, jira_client, web_search_tool, steps):
    expected_steps_num = 0.0
    for expected_step in case["expected_steps"]:
        step = next(
            (
                step for step in steps 
                if step[0] == expected_step["agent"] and expected_step["observations"] in step[1].observations
            ),
            None,
        )
        if step is None:
            continue
        expected_steps_num += 1
    
    wrong_steps_num = len(steps) - expected_steps_num
    expected_steps_percent = expected_steps_num / len(case["expected_steps"])
    wrong_steps_percent = wrong_steps_num / len(case["expected_steps"])
    return {
        "expected_steps_percent": expected_steps_percent,
        "wrong_steps_percent": wrong_steps_percent,
    }


