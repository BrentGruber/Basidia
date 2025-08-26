import click
from importlib.metadata import version

@click.command
@click.version_option()
def basidia():
    print("Hello from Basidia")

