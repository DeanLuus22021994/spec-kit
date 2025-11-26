#!/usr/bin/env python3
"""Voice Desktop Agent - AI with voice and desktop control."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .audio_utils import AudioPlayer, AudioRecorder, check_audio_devices
from .desktop_control import DesktopControlPlugin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from semantic_kernel.connectors.ai.open_ai import (  # type: ignore[import-not-found]
        AzureRealtimeExecutionSettings,
        AzureRealtimeWebsocket,
        OpenAIRealtimeExecutionSettings,
        OpenAIRealtimeWebsocket,
    )

    HAS_SK_REALTIME = True
except ImportError:
    HAS_SK_REALTIME = False
    logger.warning("Semantic Kernel realtime not installed.")


class VoiceDesktopAgent:
    """Voice-controlled AI agent with desktop automation."""

    def __init__(self, use_azure: bool = True, voice: str = "alloy") -> None:
        self.use_azure = use_azure
        self.voice = voice
        self.desktop = DesktopControlPlugin()
        self.audio_player: AudioPlayer | None = None
        self.audio_recorder: AudioRecorder | None = None
        self.realtime_client: Any = None
        self.is_running = False

    async def start(self) -> None:
        """Start the voice agent."""
        if not HAS_SK_REALTIME:
            logger.error("Semantic Kernel realtime not available")
            return

        audio_info = check_audio_devices()
        if "error" in audio_info:
            logger.error("Audio error: %s", audio_info["error"])
            return

        settings = self._create_settings()
        if self.use_azure:
            # pylint: disable=import-error,import-outside-toplevel
            from azure.identity import DefaultAzureCredential  # type: ignore[import-not-found,import-untyped]

            self.realtime_client = AzureRealtimeWebsocket(settings=settings, credential=DefaultAzureCredential())
        else:
            self.realtime_client = OpenAIRealtimeWebsocket(settings=settings)

        self.audio_player = AudioPlayer()
        self.audio_recorder = AudioRecorder()
        self.is_running = True

        print("VOICE DESKTOP AGENT - READY")
        try:
            async with self.audio_player, self.audio_recorder, self.realtime_client:
                await self._main_loop()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            self.is_running = False

    def _create_settings(self) -> Any:
        if self.use_azure:
            return AzureRealtimeExecutionSettings(voice=self.voice)
        return OpenAIRealtimeExecutionSettings(voice=self.voice)

    async def _main_loop(self) -> None:
        async for event in self.realtime_client.receive():
            if not self.is_running:
                break
            event_type = type(event).__name__
            if event_type == "RealtimeAudioEvent" and self.audio_player:
                if hasattr(event, "audio"):
                    await self.audio_player.play_audio(event.audio)
            elif event_type == "RealtimeTextEvent" and hasattr(event, "text"):
                text = str(getattr(event.text, "text", event.text))
                print(f"Aria: {text}", end="", flush=True)
                await self._process_desktop_command(text)

    async def _process_desktop_command(self, text: str) -> None:
        text_lower = text.lower()
        try:
            if "click" in text_lower:
                self.desktop.mouse_click()
            elif "open notepad" in text_lower:
                self.desktop.launch_application("notepad")
            elif "open explorer" in text_lower:
                self.desktop.launch_application("explorer")
        except (ValueError, AttributeError) as e:
            logger.error("Command failed: %s", e)

    async def execute_command(self, command: str) -> str:
        """Execute a desktop control command.

        Args:
            command: The command string to execute.

        Returns:
            The result of the command execution.
        """
        cmd = command.lower().strip()
        if cmd.startswith("click"):
            return self.desktop.mouse_click()
        if cmd.startswith("type "):
            return self.desktop.type_text(command[5:])
        if cmd.startswith("open "):
            return self.desktop.launch_application(command[5:])
        if cmd == "screenshot":
            return self.desktop.screenshot()
        return f"Unknown command: {command}"


def run_interactive() -> None:
    """Run interactive desktop control mode with command-line interface."""
    print("Interactive Desktop Control Mode")
    print("Commands: click, type <text>, open <app>, screenshot")
    agent = VoiceDesktopAgent()
    while True:
        try:
            command = input("Command> ").strip()
            if command.lower() in ("quit", "exit", "q"):
                break
            if command:
                result = asyncio.run(agent.execute_command(command))
                print(f"Result: {result}")
        except KeyboardInterrupt:
            break
    print("Goodbye!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--text":
        run_interactive()
    else:
        asyncio.run(VoiceDesktopAgent().start())
