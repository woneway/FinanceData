"""FinanceData CLI entry point."""
import click

from finance_data.cli.tools import describe_cmd, invoke_cmd, providers_cmd, tools_cmd
from finance_data.cli.ops import health_cmd, verify_cmd


@click.group()
@click.version_option(package_name="finance-data")
def main() -> None:
    """FinanceData CLI — developer/debug/ops companion."""


main.add_command(tools_cmd, "tools")
main.add_command(describe_cmd, "describe")
main.add_command(invoke_cmd, "invoke")
main.add_command(providers_cmd, "providers")
main.add_command(health_cmd, "health")
main.add_command(verify_cmd, "verify")
