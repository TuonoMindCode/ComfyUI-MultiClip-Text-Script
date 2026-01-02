__version__ = "1.1.0"

from .sequence_prompt_nodes import (
    MultiClipTextScriptMain,
    MultiClipTextScriptClipSelector,
)

NODE_CLASS_MAPPINGS = {
    "MultiClipTextScriptMain": MultiClipTextScriptMain,
    "MultiClipTextScriptClipSelector": MultiClipTextScriptClipSelector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultiClipTextScriptMain": "Multi-Clip Text Script: Main",
    "MultiClipTextScriptClipSelector": "Multi-Clip Text Script: Clip Selector",
}
