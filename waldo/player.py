from __future__ import print_function

import logging
import os
from time import sleep

import servo
from waldo.audio import AudioPlayer
from waldo.utils import read_project_config, get_first_file, read_main_config

logger = logging.getLogger(__name__)


class Player(object):
    def __init__(self, project_name, play_from=0, repeat=False, mute_pins=None):
        """
        :type mute_channels: list
        """
        self._servo_channels = []
        self._mute_pins = mute_pins if mute_pins else []
        self._audio_player = None
        self.running = False
        self.project_name = project_name
        self.play_from = play_from
        self.repeat = repeat

        preferences = read_main_config()
        project_path = preferences['project_path']
        # FIXME: find a better name to distinguish between this projects path and the path of all projects
        self.song_path = os.path.join(project_path, self.project_name)

        self._read_config()
        self._create_servo_channels()
        self._create_audio_player()

    def play(self):
        # Wait if still running
        while self.running:
            sleep(0.01)

        while not all([s.ready for s in self._servo_channels]):
            sleep(0.1)
        self._play_audio()
        self._play_servos()
        logger.info('Playing {}'.format(self.project_name))
        self.running = True

    def stop(self):
        logger.info('Stopping {}'.format(self.project_name))
        self._stop_audio()
        self._stop_servos()
        self.running = False

    def _read_config(self):
        self._config = read_project_config(self.project_name)

    def _create_servo_channels(self):
        if self._config:
            for channel_name, channel_config in self._config['channels'].items():
                if channel_config['servo_pin'] in self._mute_pins:
                    logger.debug('Muting pin {}'.format(channel_config['servo_pin']))
                    continue

                channel_path = os.path.join(self.song_path, channel_name)
                if os.path.isfile(channel_path):
                    s = servo.ServoChannel(channel_path,
                                           channel_config['servo_pin'],
                                           channel_config['map_min'],
                                           channel_config['map_max'],
                                           channel_config['start_pos']
                                           )
                    self._servo_channels.append(s)
                else:
                    logger.debug('No such channel file: {}'.format(channel_path))

    def _create_audio_player(self):
        audio_file = get_first_file(os.path.join(self.song_path, 'audio'), ('.wav', '.mp3', '.aiff'))
        try:
            self._audio_player = AudioPlayer(os.path.join(self.song_path, 'audio', audio_file), self.play_from)
        except AttributeError:
            logger.debug('No audio clip found for {}'.format(self.project_name))
            pass

    def _play_servos(self):
        for s in self._servo_channels:
            s.play(play_from=self.play_from)

    def _play_audio(self):
        if self._audio_player:
            self._audio_player.play()

    def _stop_audio(self):
        try:
            self._audio_player.stop()
        except AttributeError:
            pass

    def _stop_servos(self):
        for s in self._servo_channels:
            s.stop()

    # FIXME: @fabian remove when done with testing
    def create_test(self, channel):
        # create file with timestamps and servo positions from map_min to map_max
        file_path = os.path.join(self.song_path, "{}_test".format(channel))
        logger.debug(file_path)
        with open(file_path, 'w') as f:
            test_data = ''
            values = {self._config['channels'][channel]['map_min'], self._config['channels'][channel]['map_max']}
            map_min = min(values)
            map_max = max(values)
            for i in range(map_max - map_min + 1):
                test_data += "{}: {}\n".format(float(i) / 10, map_min + i)
            logger.debug(test_data)
            f.write(test_data)
            # f.write("{} ==> {}".format(self.map_min, self.map_max))


def preload_players():
    logger.info('Pre-loading players')

    # Read preferences and set project folder path
    preferences = read_main_config()
    # do not expand user due to autostart user is 'root' not 'pi'
    project_path = preferences['project_path'] if not os.path.isdir('projects') else 'projects'

    players = {}
    song_names = sorted(
        [item for item in os.listdir(project_path) if not item.startswith('.') and not item == '_archive']
    )

    for name in song_names:
        players[name] = Player(project_name=name)

    return players


if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)  # DEBUG / INFO / WARNING

    p = Player('sine_half_test')
    # p.create_test('1')
    p.play()
    while True:
        sleep(1)
