__version__ = "1.1.1"

from .sequence_prompt_nodes import (
    MultiClipTextScriptMain,
    MultiClipTextScriptClipSelector,
    MultiClipTextScriptPositiveOnly,
)

NODE_CLASS_MAPPINGS = {
    "MultiClipTextScriptMain": MultiClipTextScriptMain,
    "MultiClipTextScriptClipSelector": MultiClipTextScriptClipSelector,
    "MultiClipTextScriptPositiveOnly": MultiClipTextScriptPositiveOnly,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultiClipTextScriptMain": "Multi-Clip Text Script: Main",
    "MultiClipTextScriptClipSelector": "Multi-Clip Text Script: Clip Selector",
    "MultiClipTextScriptPositiveOnly": "Multi-Clip Text Script: Main Simple",
}