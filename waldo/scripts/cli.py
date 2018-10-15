#!/usr/bin/env python2
import logging
import os
from time import sleep

import click

from waldo.helpers.autostart import run_daemon
from waldo.player import Player
from waldo.recorder import record_setup, record_channel, set_servo, check_project
from waldo.utils import show_legal, print_projects, display_projects, copy_channel, empty_project_trash


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
@click.argument('project_name', default=False)
def play(start_from, project_name):
    """
    Playback of every servo channel in PROJECT_NAME and, if existent, audio file (alphabetical first
    in folder), optional from start point [start_from] in seconds.
    """
    if project_name:
        click.echo('Playing {} from {}'.format(project_name, start_from))
        player = Player(project_name)
        player.play()
        while True:
            sleep(1)
    else:
        click.echo('These projects are available:')
        display_projects()
        project_name = click.prompt('Name of project to play', type=str)
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
@click.argument('project_name', default=False)
@click.option('--bt_only/--no-bt_only', default=False, help='Display projects which are button controlled')
def ls(project_name, bt_only):
    """
    Examine projects in waldo_projects
    """
    if project_name or bt_only:
        print_projects(project_name, bt_only)

    else:
        action = click.prompt('What do you want to do?\n'
                              '  A - Display all project names\n'
                              '  B - Display projects which are button controlled\n'
                              '  C - Display all projects and details\n'
                              'Answer',
                              type=str)

        if action.lower() == 'a':
            display_projects()
            project_name = click.prompt('Name of project to display', type=str)
            print_projects(project_name, bt_only)
        elif action.lower() == 'b':
            print_projects(False, True)
        elif action.lower() == 'c':
            print_projects(False)


@cli.command()
@click.argument('project_name_from')
@click.argument('channel_name_old')
@click.argument('project_name_to')
@click.argument('channel_name_new', default=False)
@click.option('--pin_mode', default='pin_inc', help='\'pin_inc\', \'pin_copy\' or int')
def copy(project_name_from, channel_name_old, project_name_to, channel_name_new, pin_mode):
    """
    Copy channel file
    """
    if not channel_name_new:
        channel_name_new = project_name_to
        project_name_to = project_name_from
    copy_channel(project_name_from, channel_name_old, project_name_to, channel_name_new, pin_mode)


@cli.command()
@click.argument('project_name')
def empty_trash(project_name):
    """
    Delete all files in 'project_name/trash'
    """
    empty_project_trash(project_name)


@cli.command()
def legal():
    """
    Show legal info
    """
    show_legal()


if __name__ == '__main__':
    cli()
