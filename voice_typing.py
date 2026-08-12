import os
import sys
import tempfile
import wave
import pyaudio
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Try to import the ASR package
try:
    from indic_asr_onnx import IndicTranscriber

    HAS_ASR = True
except ImportError as e:
    HAS_ASR = False
    print(f"Voice typing unavailable: {e}")

# If running as bundled exe, point cache to internal folder
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    cache_dir = os.path.join(base_path, 'indic_asr_cache')
    if os.path.exists(cache_dir):
        # Set environment variable for the package to use our bundled cache
        os.environ['INDIC_ASR_CACHE'] = cache_dir
        print(f"Using bundled ASR cache: {cache_dir}")
    else:
        print(f"Warning: Bundled ASR cache not found at {cache_dir}")


class VoiceRecorder:
    """Handles recording audio from the microphone."""

    def __init__(self):
        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False

    def start_recording(self):
        """Starts recording audio."""
        try:
            self.audio = pyaudio.PyAudio()
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
            return True
        except Exception as e:
            print(f"Failed to start recording: {e}")
            traceback.print_exc()
            return False

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
            self.stream = None
        if self.audio:
            self.audio.terminate()
            self.audio = None

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_filename = temp_file.name
        try:
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit = 2 bytes
                wf.setframerate(16000)
                wf.writeframes(b''.join(self.frames))
            return temp_filename
        except Exception as e:
            print(f"Failed to save audio: {e}")
            traceback.print_exc()
            return None


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

        if not self.audio_filepath or not os.path.exists(self.audio_filepath):
            self.error.emit("Audio file not found.")
            return

        try:
            # Initialize the transcriber (this will use the bundled cache if available)
            transcriber = IndicTranscriber()
            # Transcribe the audio file (language 'as' = Assamese)
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
            error_msg = f"Transcription error: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            self.error.emit(error_msg + "\n\nCheck if the model is bundled correctly.")
