"""Voice transcription provider using Groq Whisper."""

import asyncio
import io
import os
from pathlib import Path

import httpx
from loguru import logger

# Formats natively supported by Groq Whisper (no conversion needed)
_GROQ_SUPPORTED = {".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm"}


def _to_wav_bytes_sync(path: Path) -> bytes | None:
    """
    Convert any audio file to WAV (PCM 16-bit mono 16 kHz) in memory using PyAV.

    Runs synchronously — call via run_in_executor to avoid blocking the event loop.
    PyAV bundles FFmpeg libraries so no system ffmpeg binary is required.

    Returns raw WAV bytes, or None on failure.
    """
    try:
        import av  # bundled FFmpeg via `pip install av`
    except ImportError:
        logger.error(
            "PyAV is not installed. Run: pip install av\n"
            "PyAV bundles FFmpeg and enables audio format conversion (AMR, etc.)."
        )
        return None

    try:
        buf = io.BytesIO()
        with av.open(str(path)) as src:
            audio_stream = next(
                (s for s in src.streams if s.type == "audio"), None
            )
            if audio_stream is None:
                logger.error(f"No audio stream found in {path.name}")
                return None

            with av.open(buf, mode="w", format="wav") as dst:
                out_stream = dst.add_stream("pcm_s16le", rate=16000, layout="mono")
                for packet in src.demux(audio_stream):
                    for frame in packet.decode():
                        frame.pts = None
                        for out_packet in out_stream.encode(frame):
                            dst.mux(out_packet)
                # Flush encoder
                for out_packet in out_stream.encode(None):
                    dst.mux(out_packet)

        buf.seek(0)
        data = buf.read()
        logger.debug(f"Converted {path.name} → WAV in memory ({len(data)} bytes)")
        return data

    except Exception as e:
        logger.error(f"PyAV conversion failed for {path.name}: {e}")
        return None


class GroqTranscriptionProvider:
    """
    Voice transcription provider using Groq's Whisper API.

    Groq offers extremely fast transcription with a generous free tier.

    Unsupported formats (e.g. AMR from DingTalk mobile) are automatically
    converted to WAV in memory via PyAV (bundled FFmpeg — no system binary needed).
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.api_url = "https://api.groq.com/openai/v1/audio/transcriptions"

    async def transcribe(self, file_path: str | Path) -> str:
        """
        Transcribe an audio file using Groq Whisper.

        Automatically converts unsupported formats (AMR, etc.) to WAV in memory
        via PyAV — no external tools or temp files required.

        Args:
            file_path: Path to the local audio file.

        Returns:
            Transcribed text, or empty string on failure.
        """
        if not self.api_key:
            logger.warning("Groq API key not configured for transcription")
            return ""

        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return ""

        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Formats Groq accepts directly — upload the file as-is
        if path.suffix.lower() in _GROQ_SUPPORTED:
            try:
                async with httpx.AsyncClient() as client:
                    with open(path, "rb") as f:
                        files = {
                            "file": (path.name, f),
                            "model": (None, "whisper-large-v3"),
                        }
                        resp = await client.post(
                            self.api_url, headers=headers, files=files, timeout=60.0
                        )
                        resp.raise_for_status()
                        return resp.json().get("text", "")
            except Exception as e:
                logger.error(f"Groq transcription error: {e}")
                return ""

        # Unsupported format (e.g. .amr) — convert to WAV in memory via PyAV
        logger.info(
            f"Audio format {path.suffix!r} not natively supported — "
            "converting to WAV via PyAV (bundled FFmpeg)"
        )
        loop = asyncio.get_event_loop()
        wav_bytes = await loop.run_in_executor(None, _to_wav_bytes_sync, path)

        if not wav_bytes:
            logger.error("Audio conversion failed — cannot transcribe")
            return ""

        try:
            async with httpx.AsyncClient() as client:
                files = {
                    "file": ("audio.wav", wav_bytes, "audio/wav"),
                    "model": (None, "whisper-large-v3"),
                }
                resp = await client.post(
                    self.api_url, headers=headers, files=files, timeout=60.0
                )
                resp.raise_for_status()
                return resp.json().get("text", "")
        except Exception as e:
            logger.error(f"Groq transcription error (after conversion): {e}")
            return ""
