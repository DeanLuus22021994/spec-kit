#!/usr/bin/env python3
"""
Audio Utilities for Voice Agent
================================

Provides audio recording and playback capabilities using sounddevice and numpy.
Compatible with Semantic Kernel realtime APIs.

Based on: semantic-kernel/python/samples/concepts/audio/
"""

from __future__ import annotations

import base64
import logging
import threading
import wave
from typing import Any, ClassVar, Final

import numpy as np
import numpy.typing as npt

try:
    import sounddevice as sd  # type: ignore[import-untyped,import-not-found]
    from sounddevice import InputStream, OutputStream  # type: ignore[import-untyped,import-not-found]

    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    sd = None  # type: ignore[assignment]
    InputStream = None  # type: ignore[assignment,misc]
    OutputStream = None  # type: ignore[assignment,misc]

try:
    import pyaudio  # type: ignore[import-untyped,import-not-found]

    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    pyaudio = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Audio constants
SAMPLE_RATE: Final[int] = 24000
RECORDER_CHANNELS: Final[int] = 1
PLAYER_CHANNELS: Final[int] = 1
FRAME_DURATION: Final[int] = 100
DTYPE: Final[npt.DTypeLike] = np.int16


def check_audio_devices() -> dict[str, Any]:
    """Check available audio devices and return info."""
    if not HAS_SOUNDDEVICE:
        return {"error": "sounddevice not installed", "devices": []}

    devices = sd.query_devices()  # type: ignore[union-attr]
    default_input = sd.query_devices(kind="input")  # type: ignore[union-attr]
    default_output = sd.query_devices(kind="output")  # type: ignore[union-attr]

    return {
        "devices": devices,
        "default_input": default_input,
        "default_output": default_output,
        "sample_rate": SAMPLE_RATE,
    }


class AudioRecorder:
    """Record audio from microphone using sounddevice.

    Usage:
        recorder = AudioRecorder()
        async with recorder:
            # Recording happens automatically
            await asyncio.sleep(5)  # Record for 5 seconds
        audio_data = recorder.get_audio_data()
    """

    def __init__(
        self,
        device: str | int | None = None,
        sample_rate: int = SAMPLE_RATE,
        channels: int = RECORDER_CHANNELS,
        frame_duration: int = FRAME_DURATION,
        dtype: npt.DTypeLike = DTYPE,
    ) -> None:
        """Initialize audio recorder.

        Args:
            device: Audio input device (None for default)
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            frame_duration: Frame duration in ms
            dtype: Numpy dtype for audio data
        """
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_duration = frame_duration
        self.dtype = dtype
        self.frame_size = int(sample_rate * frame_duration / 1000)

        self._stream: Any = None
        self._queue: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._is_recording = False

    def _sounddevice_callback(
        self,
        indata: np.ndarray,
        _frames: int,
        _time: Any,
        status: Any,
    ) -> None:
        """Callback for sounddevice input stream."""
        if status:
            logger.warning("Audio input status: %s", status)
        with self._lock:
            self._queue.append(indata.copy())

    async def __aenter__(self) -> "AudioRecorder":
        """Start recording when entering context."""
        if not HAS_SOUNDDEVICE:
            raise RuntimeError("sounddevice not installed. Run: pip install sounddevice")

        self._is_recording = True
        self._queue = []
        self._stream = InputStream(  # type: ignore[misc]
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=self.dtype,
            blocksize=self.frame_size,
            callback=self._sounddevice_callback,
        )
        self._stream.start()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Stop recording when exiting context."""
        self._is_recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
        self._stream = None

    def get_audio_data(self) -> np.ndarray:
        """Get all recorded audio as a single numpy array."""
        with self._lock:
            if not self._queue:
                return np.array([], dtype=self.dtype)
            return np.concatenate(self._queue)

    def get_audio_bytes(self) -> bytes:
        """Get recorded audio as bytes."""
        return self.get_audio_data().tobytes()

    def get_audio_base64(self) -> str:
        """Get recorded audio as base64 string."""
        return base64.b64encode(self.get_audio_bytes()).decode("utf-8")

    def save_wav(self, filepath: str) -> None:
        """Save recorded audio to WAV file."""
        audio_data = self.get_audio_data()
        # pylint: disable=no-member  # wave.open("wb") returns Wave_write, not Wave_read
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())


class AudioPlayer:
    """Play audio using sounddevice.

    Usage:
        player = AudioPlayer()
        async with player:
            await player.play_audio(audio_data)
    """

    def __init__(
        self,
        device: int | None = None,
        sample_rate: int = SAMPLE_RATE,
        channels: int = PLAYER_CHANNELS,
        frame_duration: int = FRAME_DURATION,
        dtype: npt.DTypeLike = DTYPE,
    ) -> None:
        """Initialize audio player.

        Args:
            device: Audio output device (None for default)
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            frame_duration: Frame duration in ms
            dtype: Numpy dtype for audio data
        """
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_duration = frame_duration
        self.dtype = dtype

        self._stream: Any = None
        self._queue: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._frame_count = 0

    def _sounddevice_callback(
        self,
        outdata: np.ndarray,
        frames: int,
        _time: Any,
        status: Any,
    ) -> None:
        """Callback for sounddevice output stream."""
        with self._lock:
            if status:
                logger.debug("Audio output status: %s", status)
            data = np.empty(0, dtype=np.int16)

            while len(data) < frames and len(self._queue) > 0:
                item = self._queue.pop(0)
                frames_needed = frames - len(data)
                data = np.concatenate((data, item[:frames_needed]))
                if len(item) > frames_needed:
                    self._queue.insert(0, item[frames_needed:])

            self._frame_count += len(data)

            if len(data) < frames:
                data = np.concatenate((data, np.zeros(frames - len(data), dtype=np.int16)))

        outdata[:] = data.reshape(-1, 1)

    async def __aenter__(self) -> "AudioPlayer":
        """Start audio output stream when entering context."""
        if not HAS_SOUNDDEVICE:
            raise RuntimeError("sounddevice not installed. Run: pip install sounddevice")

        with self._lock:
            self._queue = []
        self._stream = OutputStream(  # type: ignore[misc]
            callback=self._sounddevice_callback,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=int(self.sample_rate * self.frame_duration / 1000),
            device=self.device,
        )
        self._stream.start()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        """Stop audio output stream when exiting context."""
        if self._stream:
            self._stream.stop()
            self._stream.close()
        self._stream = None
        with self._lock:
            self._queue = []

    async def play_audio(self, audio_data: np.ndarray | bytes | str) -> None:
        """Add audio to the playback queue.

        Args:
            audio_data: Audio as numpy array, bytes, or base64 string
        """
        with self._lock:
            if isinstance(audio_data, np.ndarray):
                self._queue.append(audio_data)
            elif isinstance(audio_data, bytes):
                self._queue.append(np.frombuffer(audio_data, dtype=self.dtype))
            elif isinstance(audio_data, str):
                # Assume base64 encoded
                decoded = base64.b64decode(audio_data)
                self._queue.append(np.frombuffer(decoded, dtype=self.dtype))

    async def play_wav(self, filepath: str) -> None:
        """Play a WAV file."""
        with wave.open(filepath, "rb") as wf:
            audio_data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            await self.play_audio(audio_data)


class SimpleAudioPlayer:
    """Simple audio player using pyaudio (synchronous)."""

    CHUNK: ClassVar[int] = 1024

    def __init__(self) -> None:
        if not HAS_PYAUDIO:
            raise RuntimeError("pyaudio not installed. Run: pip install pyaudio")

    def play_wav(self, filepath: str) -> None:
        """Play a WAV file synchronously."""
        with wave.open(filepath, "rb") as wf:
            audio = pyaudio.PyAudio()  # type: ignore[union-attr]
            stream = audio.open(
                format=audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            data = wf.readframes(self.CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(self.CHUNK)

            stream.stop_stream()
            stream.close()
            audio.terminate()

    def play_bytes(self, audio_bytes: bytes, sample_rate: int = 24000, channels: int = 1) -> None:
        """Play raw audio bytes."""
        audio = pyaudio.PyAudio()  # type: ignore[union-attr]
        stream = audio.open(
            format=pyaudio.paInt16,  # type: ignore[union-attr]
            channels=channels,
            rate=sample_rate,
            output=True,
        )
        stream.write(audio_bytes)
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    # Test audio devices
    print("Audio Device Check:")
    info = check_audio_devices()
    if "error" in info:
        print(f"  Error: {info['error']}")
    else:
        print(f"  Default Input: {info['default_input'].get('name', 'N/A')}")
        print(f"  Default Output: {info['default_output'].get('name', 'N/A')}")
        print(f"  Sample Rate: {info['sample_rate']}")
