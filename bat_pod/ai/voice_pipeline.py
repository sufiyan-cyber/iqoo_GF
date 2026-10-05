"""Voice Pipeline handling STT, TTS, and language management with offline fallback."""

import logging
import os
from typing import Optional
import requests
from bat_pod.config import settings

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Manages Speech-to-Text and Text-to-Speech interactions."""

    def __init__(self) -> None:
        self.sarvam_key = settings.SARVAM_API_KEY
        self.default_language = settings.VOICE_LANGUAGE

    def speech_to_text(self, audio_data: Optional[bytes] = None, language: Optional[str] = None) -> Optional[str]:
        """Convert captured speech audio into text."""
        lang = language or self.default_language

        # If Sarvam API key is present and audio provided, call Sarvam ASR
        if self.sarvam_key and audio_data:
            try:
                headers = {"api-subscription-key": self.sarvam_key}
                files = {"file": ("audio.wav", audio_data, "audio/wav")}
                data = {"language_code": lang}
                resp = requests.post(
                    "https://api.sarvam.ai/speech-to-text",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    res_json = resp.json()
                    transcript = res_json.get("transcript")
                    if transcript:
                        return transcript
            except Exception as ex:
                logger.warning(f"Sarvam STT failed: {ex}. Falling back.")

        return None

    def text_to_speech(self, text: str, language: Optional[str] = None) -> bool:
        """Synthesize spoken audio from text."""
        lang = language or self.default_language

        # If Sarvam key is provided, request Sarvam TTS audio
        if self.sarvam_key:
            try:
                headers = {
                    "api-subscription-key": self.sarvam_key,
                    "Content-Type": "application/json",
                }
                payload = {
                    "inputs": [text],
                    "target_language_code": lang,
                    "speaker": "meera",
                    "pitch": 0,
                    "pace": 1.0,
                    "loudness": 1.5,
                    "speech_sample_rate": 16000,
                    "enable_preprocessing": True,
                    "model": "bulbul:v1",
                }
                resp = requests.post(
                    "https://api.sarvam.ai/text-to-speech",
                    headers=headers,
                    json=payload,
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    logger.info(f"[Sarvam TTS Audio Synthesized]: \"{text}\"")
                    return True
            except Exception as ex:
                logger.warning(f"Sarvam TTS failed: {ex}. Falling back to local console output.")

        # Local fallback: Log speech output
        logger.info(f"[VOICE OUTPUT ({lang})]: \"{text}\"")
        return True


voice_pipeline = VoicePipeline()
