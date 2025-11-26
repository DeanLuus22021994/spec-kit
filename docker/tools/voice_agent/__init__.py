# Voice Agent Package - AI with voice and desktop control
"""
Voice-enabled AI agent with Windows desktop control capabilities.

Components:
- audio_utils: Audio recording and playback utilities
- desktop_control: Windows automation plugin (mouse, keyboard, windows)
- voice_agent: Main orchestrator combining voice + desktop control

Requirements (install in container/venv):
    pip install sounddevice pyaudio pyautogui pywin32
"""

from __future__ import annotations

from .audio_utils import AudioPlayer, AudioRecorder
from .desktop_control import DesktopControlPlugin
from .voice_agent import VoiceDesktopAgent

__all__ = [
    "AudioPlayer",
    "AudioRecorder",
    "DesktopControlPlugin",
    "VoiceDesktopAgent",
]
