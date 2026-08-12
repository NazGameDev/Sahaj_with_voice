import os
import sys
import tempfile
import wave
import threading
import time
import pyaudio
from PyQt6.QtCore import QThread, pyqtSignal

# Try to import the ASR package
try:
    from indic_asr_onnx import IndicTranscriber
    HAS_ASR = True
except ImportError:
    HAS_ASR = False
    print("Voice typing unavailable: 'indic-asr-onnx' not installed.")

# Set cache directory to bundled folder if running from exe
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    cache_dir = os.path.join(base_path, 'indic_asr_cache')
    if os.path.exists(cache_dir):
        os.environ['INDIC_ASR_CACHE'] = cache_dir
        print(f"Using bundled ASR cache: {cache_dir}")


class VoiceRecorder:
    """Handles recording audio from the microphone."""
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False

    def start_recording(self):
        """Starts recording audio."""
        self.frames = []
        self.is_recording = True
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self._callback
        )
        self.stream.start_stream()

    def _callback(self, in_data, frame_count, time_info, status):
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """Stops recording and returns path to saved WAV file."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_filename = temp_file.name
        with wave.open(temp_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.frames))
        return temp_filename


class VoiceTypingWorker(QThread):
    """Worker thread to transcribe audio without freezing the UI."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_filepath):
        super().__init__()
        self.audio_filepath = audio_filepath

    def run(self):
        if not HAS_ASR:
            self.error.emit("Voice typing is not available. Please install 'indic-asr-onnx'.")
            return

        try:
            # Initialize the transcriber
            transcriber = IndicTranscriber()
            # Transcribe the audio file
            transcribed_text = transcriber.transcribe_rnnt(self.audio_filepath, "as")
            
            # Clean up temp file
            try:
                os.remove(self.audio_filepath)
            except:
                pass

            if transcribed_text and transcribed_text.strip():
                self.finished.emit(transcribed_text.strip())
            else:
                self.error.emit("Could not understand the audio. Please try again.")

        except Exception as e:
            import traceback
            error_msg = f"Transcription error: {str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            self.error.emit(error_msg)
