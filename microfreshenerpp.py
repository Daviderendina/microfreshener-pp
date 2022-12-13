import click


@click.command()
@click.option('--name', default="NO NAME", help='number of greetings')
# @click.argument('name')
def run(name):  # count, name):
    click.echo(f"Hi {name}")


if __name__ == "__main":
    run()
