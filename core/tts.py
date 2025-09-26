"""Text-to-Speech service using ElevenLabs API."""

import io
import asyncio
from typing import Optional

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import Voice, VoiceSettings
except ImportError:
    ElevenLabs = None
    Voice = None
    VoiceSettings = None

from core.config import settings


class TTSService:
    """Text-to-Speech service using ElevenLabs."""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ElevenLabs client if API key is available."""
        if not settings.ELEVEN_LAB_API_KEY:
            print("⚠️ ElevenLabs API key not configured - TTS disabled")
            return
        
        if ElevenLabs is None:
            print("⚠️ ElevenLabs package not installed - TTS disabled")
            return
        
        try:
            self.client = ElevenLabs(api_key=settings.ELEVEN_LAB_API_KEY)
            print("✅ ElevenLabs TTS service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize ElevenLabs: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if TTS service is available."""
        return self.client is not None
    
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",  # Default voice
        model_id: str = "eleven_multilingual_v2",
        output_format: str = "mp3_44100_128"
    ) -> Optional[bytes]:
        """
        Convert text to speech and return audio bytes.
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            model_id: ElevenLabs model ID
            output_format: Audio output format
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.is_available():
            print("❌ TTS service not available")
            return None
        
        if not text or len(text.strip()) == 0:
            print("❌ Empty text provided for TTS")
            return None
        
        # Limit text length to avoid API issues
        if len(text) > 1000:
            text = text[:997] + "..."
            print(f"⚠️ Text truncated to 1000 characters for TTS")
        
        try:
            print(f"🎤 Converting text to speech: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            # Run the synchronous API call in a thread pool
            audio_generator = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.text_to_speech.convert(
                    text=text,
                    voice_id=voice_id,
                    model_id=model_id,
                    output_format=output_format,
                )
            )
            
            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)
            print(f"✅ TTS conversion successful - {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"❌ TTS conversion failed: {e}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available voices."""
        if not self.is_available():
            return []
        
        try:
            voices = self.client.voices.get_all()
            return [{"id": v.voice_id, "name": v.name} for v in voices.voices]
        except Exception as e:
            print(f"❌ Failed to get voices: {e}")
            return []


# Global TTS service instance
_tts_service = None

def get_tts_service() -> TTSService:
    """Get the global TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service