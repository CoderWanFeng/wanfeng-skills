"""三条产线：声音 / 形象 / 口播。"""

from .persona_line import PersonaResult, generate_persona_images
from .talking_line import TalkingResult, generate_talking_videos
from .voice_line import VoiceResult, synthesize_script

__all__ = [
    "PersonaResult",
    "TalkingResult",
    "VoiceResult",
    "generate_persona_images",
    "generate_talking_videos",
    "synthesize_script",
]
