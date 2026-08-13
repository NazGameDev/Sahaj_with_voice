# voice_typing.py
import os
import sys
import tempfile
import wave
import traceback
import pyaudio
import threading
from PyQt6.QtCore import QThread, pyqtSignal, QTimer

# --- Logging helper ---
def log_error(msg):
    """Append error message to a log file in the user's home."""
    log_path = os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log')
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    except:
        pass

# --- Set cache directory BEFORE importing the ASR module ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    cache_dir = os.path.join(base_path, 'indic_asr_cache')
    if os.path.exists(cache_dir):
        os.environ['INDIC_ASR_CACHE'] = cache_dir
        log_error(f"Using bundled ASR cache: {cache_dir}")
        try:
            contents = os.listdir(cache_dir)
            log_error(f"Cache contents: {contents}")
        except:
            pass
    else:
        log_error(f"Warning: Bundled ASR cache not found at {cache_dir}")
        
    # Also set FFmpeg path if bundled
    ffmpeg_dir = os.path.join(base_path, 'ffmpeg_bin')
    if os.path.exists(ffmpeg_dir):
        # Add to PATH so torchaudio can find FFmpeg DLLs
        os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        log_error(f"Added FFmpeg to PATH: {ffmpeg_dir}")
    else:
        log_error(f"Warning: FFmpeg not found at {ffmpeg_dir}")
else:
    log_error("Running in development mode, using default cache.")


# --- Now import the ASR module ---
HAS_ASR = False
ASR_IMPORT_ERROR = None

try:
    from indic_asr_onnx import IndicTranscriber
    HAS_ASR = True
    log_error("Voice typing: indic_asr_onnx imported successfully.")
except ImportError as e:
    ASR_IMPORT_ERROR = str(e)
    log_error(f"Voice typing: ImportError - {e}")
    traceback.print_exc(file=open(os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log'), 'a'))
except Exception as e:
    ASR_IMPORT_ERROR = str(e)
    log_error(f"Voice typing: Unexpected import error - {e}")
    traceback.print_exc(file=open(os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log'), 'a'))


class VoiceRecorder:
    """Handles recording audio from the microphone with start/stop control."""
    def __init__(self):
        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None

    def start_recording(self):
        """Starts recording audio in a background thread."""
        if self.is_recording:
            return False
        
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
            log_error(f"VoiceRecorder.start_recording error: {e}")
            traceback.print_exc(file=open(os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log'), 'a'))
            self.is_recording = False
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

        if not self.frames:
            return None

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_filename = temp_file.name
        try:
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)
                wf.writeframes(b''.join(self.frames))
            return temp_filename
        except Exception as e:
            log_error(f"VoiceRecorder.stop_recording error: {e}")
            traceback.print_exc(file=open(os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log'), 'a'))
            return None

    def is_recording_active(self):
        return self.is_recording


class VoiceTypingWorker(QThread):
    """Worker thread to transcribe audio."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, audio_filepath):
        super().__init__()
        self.audio_filepath = audio_filepath

    def run(self):
        try:
            if not HAS_ASR:
                self.error.emit(f"Voice typing is not available.\nImport error: {ASR_IMPORT_ERROR}")
                return

            if not self.audio_filepath or not os.path.exists(self.audio_filepath):
                self.error.emit("Audio file not found.")
                return

            # Disable progress bars and suppress stdout to prevent tqdm crash
            os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
            devnull = open(os.devnull, 'w')
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = devnull
            sys.stderr = devnull

            try:
                log_error("Initializing IndicTranscriber...")
                transcriber = IndicTranscriber()
                log_error("IndicTranscriber initialized.")
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                devnull.close()

            log_error(f"Transcribing file: {self.audio_filepath}")
            transcribed_text = transcriber.transcribe_rnnt(self.audio_filepath, "as")
            log_error(f"Transcription result: {transcribed_text}")

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
            error_msg = f"VoiceTypingWorker.run error: {str(e)}\n{traceback.format_exc()}"
            log_error(error_msg)
            self.error.emit(f"An error occurred during voice typing.\n\nError: {str(e)}\n\nPlease check the log file:\n{os.path.join(os.path.expanduser('~'), 'sahaj_voice_error.log')}")
