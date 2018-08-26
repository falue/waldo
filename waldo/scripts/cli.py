#!/usr/bin/env python2
import click

from waldo.helpers.autostart import run_daemon


@click.group()
def cli():
    """Puppeteering tool for animatronics"""
    pass


@cli.command()
def daemon():
    """Run in background and wait for keyboard commands. This is usually being run from rc.local"""
    click.echo('Waiting for input..')
    run_daemon()


@cli.command()
@click.option('--start_from', default=0, help='Start point in seconds')
@click.argument('project_name')
def play(start_from, project_name):
    """
    Playback of every servo channel in PROJECT_NAME and, if existent, audiofile (alphabetical first
    in folder), optional from start point [start_from] in seconds.
    """
    click.echo('Playing {} from {}'.format(project_name, start_from))


@cli.command()
@click.argument('project_name')
@click.argument('channel_file')
@click.option('--audio_file', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def record(project_name, channel_file, audio_file):
    """
    Record CHANNEL_FILE in PROJECT_NAME. Optional specific audio playback with --audio_file
    (if none is entered, alphabetical first in folder will play if existent).
    """
    click.echo('Recording {}.'.format(project_name))


if __name__ == '__main__':
    cli()
