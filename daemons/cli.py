#!/usr/bin/env python3
"""
CLI interface for the daemons
"""

import click
from dotenv import load_dotenv
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from phoenix.otel import register

load_dotenv()
register(project_name="daemons")
SmolagentsInstrumentor().instrument()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output", envvar="DAEMONS_VERBOSE")
@click.option("--model", "-m", default=None, help="LLM model to use", envvar="DAEMONS_MODEL")
@click.pass_context
def cli(ctx, verbose, model):
    """CLI interface for the daemons"""
    ctx.obj = {"verbose": verbose, "model": model}


@cli.group()
def argus():
    """Argus agent"""


@argus.command(name="run")
@click.pass_context
def argus_run(ctx):
    """Analyze logs for potential issues with Argus"""
    from daemons.agents.argus.smol import get_argus

    logs_content = None
    while not logs_content:
        click.echo("Provide logs to analyze:")
        logs_content = input()

    hostname = None
    while not hostname:
        click.echo("Provide hostname:")
        hostname = input()

    service_name = None
    while not service_name:
        click.echo("Provide service name:")
        service_name = input()

    click.echo("Provide unit (optional):")
    unit = input()
        
    model = ctx.obj["model"]
    verbose = ctx.obj["verbose"]

    click.echo(
        f"Analyzing logs with {click.style('Argus', fg='green')} [model: {click.style(model, fg='yellow', bold=True)}, verbose: {click.style('on' if verbose else 'off', fg='yellow', bold=True)}]"
    )
    workflow = get_argus(model_id=model, verbose=verbose)
    result = workflow.run(logs_content, hostname, service_name, unit)
    click.echo(result)


@argus.command(name="eval")
@click.pass_context
def argus_eval(ctx):
    """Evaluate Argus agent test cases"""
    from daemons.evals.agrus.eval import eval_argus

    result = eval_argus(model_id=ctx.obj["model"], verbose=ctx.obj["verbose"])
    click.echo(result)


if __name__ == "__main__":
    cli()
