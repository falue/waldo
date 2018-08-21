import subprocess

from waldo.player import logger


class AudioPlayer(object):
    def __init__(self, audio_file, play_from=0):
        self.play_process = None

        self.audio_file = audio_file
        self.play_from = play_from

    def play(self):
        logger.info('Playing audio file {}'.format(self.audio_file))
        cmd = ['/usr/bin/play', '-q', self.audio_file]
        if self.play_from:
            cmd += ['trim', self.play_from]

        self.play_process = subprocess.Popen(cmd)

    def stop(self):
        self.play_process.kill()
