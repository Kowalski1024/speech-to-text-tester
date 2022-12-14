import argparse

from loguru import logger
import whisper
from whisper.normalizers import EnglishTextNormalizer

from tests.test_base import TestBase
from lib.video import Video
from lib.differs import differ
import db


MODEL_TYPES = [
    'tiny',
    'base',
    'small',
    'medium',
    'large',
    'tiny.en',
    'base.en',
    'small.en',
    'medium.en'
]


class TranscriptDiffTest(TestBase):
    def __init__(self,
                 model_type: str,
                 **kwargs
                 ):
        super().__init__(**kwargs)

        self.model_name = model_type.replace('.', '-')
        self.model = whisper.load_model(model_type)

        self.normalizer = EnglishTextNormalizer()
        self.transcriber = self.model.transcribe

    def test_video(self, video_details: dict) -> dict:
        video = Video.from_dict(video_details)
        audio = video.download_mp3(self.audio_path)

        logger.info(f"Staring transcribing...")
        results = self.transcribe(audio, verbose=False, remove_audio=True)

        # self.save_transcript(results, f'{audio.stem}_{self.model_name}')

        detected_language = results['language']

        yt_transcript = video.youtube_transcript(detected_language)
        model_transcript = results['text']

        yt_transcript = self.normalize(yt_transcript)
        model_transcript = self.normalize(model_transcript)

        differ_results = differ(model_transcript, yt_transcript)

        differ_results['detectedLanguage'] = detected_language

        return differ_results

    def postprocess(self, results: dict):
        results['model'] = {
            'name': self.model_name
        }

        db.insert_transcript_diff_results(results)

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser()):
        parser.add_argument(
            type=str, dest='model_type', choices=MODEL_TYPES
        )


if __name__ == '__main__':
    TranscriptDiffTest.from_command_line().run()
