#!/usr/bin/env python2
import logging
import os
from time import sleep

import click

from waldo.helpers.autostart import run_daemon
from waldo.player import Player
from waldo.recorder import record_setup, record_channel, set_servo, check_project
from waldo.utils import show_legal, print_projects, go_to_projects, copy_channel


@click.group()
@click.option('--debug/--no-debug', default=False)
def cli(debug):
    """Puppeteering tool for animatronics"""
    logging_format = '%(asctime)s - %(name)-12s - %(levelname)s - %(message)s'
    logging.basicConfig(format=logging_format, level=logging.DEBUG if debug else logging.INFO)


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
    Playback of every servo channel in PROJECT_NAME and, if existent, audio file (alphabetical first
    in folder), optional from start point [start_from] in seconds.
    """
    click.echo('Playing {} from {}'.format(project_name, start_from))
    player = Player(project_name)
    player.play()
    while True:
        sleep(1)


@cli.command()
@click.argument('project_name')
@click.argument('channel_name', default=False)
def setup(project_name, channel_name):
    """
    Setup or re-set servo parameters for recording
    """
    check_project(project_name)
    if channel_name:
        set_servo(project_name, channel_name)


@cli.command()
@click.argument('project_name')
@click.argument('channel_name')
def record(project_name, channel_name):
    """
    Record CHANNEL_FILE in PROJECT_NAME
    """
    check_project(project_name)
    record_setup(project_name, channel_name)
    record_channel(project_name, channel_name)


@cli.command()
@click.option('-p', default=None, help='Name of project')
# @click.option('--bt_only', default=False, help='Only projects which are set by buttons')
@click.option('--bt_only/--no-bt_only', default=False)
def ls(p, bt_only):
    """
    Examine projects in waldo_projects
    """
    print_projects(p, bt_only)



@cli.command()
def legal():
    """
    Show legal info
    """
    show_legal()


if __name__ == '__main__':
    cli()
