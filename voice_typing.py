import os
import sys
import tempfile
import wave
import threading
import pyaudio
from PyQt6.QtCore import QThread, pyqtSignal

# Try to import the ASR package
try:
    from indic_asr_onnx import IndicTranscriber
    HAS_ASR = True
except ImportError:
    HAS_ASR = False
    print("Voice typing unavailable: 'indic-asr-onnx' not installed.")


class VoiceRecorder:
    """Handles recording audio from the microphone."""
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False

    def start_recording(self):
        """Starts recording audio in a background thread."""
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
        """Callback function for PyAudio stream."""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        """Stops recording and saves audio to a temporary WAV file."""
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

        # Save recorded audio to a temporary file
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
            # Initialize the transcriber (downloads model on first use)
            transcriber = IndicTranscriber()
            # Transcribe the audio file
            # The language code for Assamese is 'as'
            transcribed_text = transcriber.transcribe_rnnt(self.audio_filepath, "as")
            
            # Clean up the temporary file
            try:
                os.remove(self.audio_filepath)
            except:
                pass

            if transcribed_text and transcribed_text.strip():
                self.finished.emit(transcribed_text.strip())
            else:
                self.error.emit("Could not understand the audio. Please try again.")

        except Exception as e:
            self.error.emit(f"An error occurred during transcription: {str(e)}")