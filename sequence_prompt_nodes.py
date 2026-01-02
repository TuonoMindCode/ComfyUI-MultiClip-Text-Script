import re

# Separatorer för intern kodning i pair_data
CLIP_SEP = "\n<<<MULTICLIP_CLIP_SEP>>>\n"
META_SEP = "\n<<<MULTICLIP_META_SEP>>>\n"


class MultiClipTextScriptMain:
    """
    Multi-Clip Text Script: Main

    Tar text från t.ex. Ollama eller någon annan källa + konstant prefix/suffix:

    prefix_text:
      Beskrivning som alltid ska vara med (personen, scenen, stil, etc).

    multi_clip_script (exempel):
      (clip01)
      woman waves at the camera

      (clip02)
      woman gets angry

      (clip03)
      woman calls someone

    suffix_text:
      Text som läggs till efter varje klipp (t.ex. kamera-stil, kvalitet, osv).

    negative_text:
      Negativ prompt som är gemensam för alla klipp.

    Scriptet parsas i formatet:

      (clip01)
      <text>

      (clip02)
      <text>

      ...

    Och omvandlas till ett internt paket (MULTICLIP_PAIR_DATA) där vi sparar:
      - prefix
      - suffix
      - alla clip-texter i ordning

    Sedan kan "Multi-Clip Text Script: Clip Selector" plocka ut
    en clip-text i taget och bygga en färdig prompt.

    Output:
      pair_data (MULTICLIP_PAIR_DATA)        – intern sträng med all data
      num_clips (INT)                        – hur många klipp som hittades
      multi_clip_negative (MULTICLIP_NEGATIVE) – negativ prompt för alla klipp
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # 1. Prefix först
                "prefix_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
                # 2. Huvudfönstret för (clip01)(clip02)...-scriptet
                "multi_clip_script": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "(clip01)\nwoman walks forward and waves to the camera\n\n"
                                   "(clip02)\nwoman walks forward and gets angry\n\n"
                                   "(clip03)\nwoman throws the phone",
                    },
                ),
                # 3. Suffix sist
                "suffix_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
            },
            "optional": {
                "negative_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MULTICLIP_PAIR_DATA", "INT", "MULTICLIP_NEGATIVE")
    RETURN_NAMES = ("pair_data", "num_clips", "multi_clip_negative")
    FUNCTION = "parse_script"
    CATEGORY = "Text / Multi-Clip"

    def parse_script(
        self,
        prefix_text: str,
        multi_clip_script: str,
        suffix_text: str,
        negative_text: str = "",
    ):
        # Hitta alla (clipXX) + text fram till nästa (clipYY) eller slutet
        pattern = r"\(clip(\d+)\)\s*(.*?)(?=\n\(clip\d+\)|\Z)"
        matches = re.findall(pattern, multi_clip_script, flags=re.DOTALL | re.IGNORECASE)

        clips = []
        for idx, text in matches:
            text = text.strip()
            if text:
                clips.append((int(idx), text))  # "01" -> 1 osv, för sortering

        # Sortera efter clip-nummer
        clips.sort(key=lambda x: x[0])

        prefix_clean = (prefix_text or "").strip()
        suffix_clean = (suffix_text or "").strip()
        negative_clean = (negative_text or "").strip()

        if not clips:
            # Inga klipp hittade – koda ändå prefix/suffix men utan clips
            payload = META_SEP.join([prefix_clean, suffix_clean, ""])
            return (payload, 0, negative_clean)

        # Själva klipp-texterna i ordning
        clip_texts = [t for _, t in clips]
        clips_blob = CLIP_SEP.join(clip_texts)

        # Kodning i pair_data:
        #   prefix <<META_SEP>> suffix <<META_SEP>> clip1 <<CLIP_SEP>> clip2 <<CLIP_SEP>> ...
        payload = META_SEP.join([prefix_clean, suffix_clean, clips_blob])
        num_clips = len(clip_texts)

        return (payload, num_clips, negative_clean)


class MultiClipTextScriptPositiveOnly:
    """
    Multi-Clip Text Script: Main Simple

    Förenklad version av Main utan prefix/suffix/negativ.

    Tar endast scriptet med (clip01)(clip02)... och konverterar det till pair_data.

    Användning:
      - Scriptet med (clip01), (clip02), osv
      - Utdata pair_data → Clip Selector (din befintliga nod)

    Output:
      pair_data (MULTICLIP_PAIR_DATA)  – intern sträng med alla clips
      num_clips (INT)                  – hur många klipp som hittades
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "multi_clip_script": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "(clip01)\nwoman walks forward and waves to the camera\n\n"
                                   "(clip02)\nwoman walks forward and gets angry\n\n"
                                   "(clip03)\nwoman throws the phone",
                    },
                ),
            },
        }

    RETURN_TYPES = ("MULTICLIP_PAIR_DATA", "INT")
    RETURN_NAMES = ("pair_data", "num_clips")
    FUNCTION = "parse_simple"
    CATEGORY = "Text / Multi-Clip"

    def parse_simple(self, multi_clip_script: str):
        # Hitta alla (clipXX) + text fram till nästa (clipYY) eller slutet
        pattern = r"\(clip(\d+)\)\s*(.*?)(?=\n\(clip\d+\)|\Z)"
        matches = re.findall(pattern, multi_clip_script, flags=re.DOTALL | re.IGNORECASE)

        clips = []
        for idx, text in matches:
            text = text.strip()
            if text:
                clips.append((int(idx), text))

        # Sortera efter clip-nummer
        clips.sort(key=lambda x: x[0])

        if not clips:
            # Inga klipp hittade
            payload = META_SEP.join(["", "", ""])
            return (payload, 0)

        # Själva klipp-texterna i ordning
        clip_texts = [t for _, t in clips]
        clips_blob = CLIP_SEP.join(clip_texts)

        # Kodning i pair_data (samma format som Main, men utan prefix/suffix):
        #   "" <<META_SEP>> "" <<META_SEP>> clip1 <<CLIP_SEP>> clip2 <<CLIP_SEP>> ...
        payload = META_SEP.join(["", "", clips_blob])
        num_clips = len(clip_texts)

        return (payload, num_clips)



class MultiClipTextScriptClipSelector:
    """
    Multi-Clip Text Script: Clip Selector

    Tar emot pair_data från MultiClipTextScriptMain (typ MULTICLIP_PAIR_DATA)
    och väljer EN specifik klipp-text baserat på clip_number (1-baserat).

    clip_number (1-baserat i UI):
      1 -> första klipp-texten (clip01)
      2 -> andra (clip02)
      3 -> tredje (clip03)
      osv.

    auto_format:
      - False:  prefix + tomrad + clip + tomrad + suffix
      - True:   "prefix, clip, suffix." (klassisk prompt-stil)
                + rensar bort extra kommatecken i slutet av varje del.

    negative:
      - Input av typen MULTICLIP_NEGATIVE (ingen egen text-ruta i denna nod).
        Typisk kedja:
          Multi-Clip Text Script: Main (multi_clip_negative)
            → Anything Everywhere
            → Multi-Clip Text Script: Clip Selector (negative)
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pair_data": ("MULTICLIP_PAIR_DATA", {}),
                "clip_number": (
                    "INT",
                    {
                        "default": 1,
                        "min": 1,
                        "max": 999,
                        "step": 1,
                    },
                ),
            },
            "optional": {
                "auto_format": (
                    "BOOLEAN",
                    {
                        "default": False,
                    },
                ),
                "log_to_console": (
                    "BOOLEAN",
                    {
                        "default": False,
                    },
                ),
                "negative": (
                    "MULTICLIP_NEGATIVE",
                    {},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("clip_text", "negative_text")
    FUNCTION = "select_pair"
    CATEGORY = "Text / Multi-Clip"

    def select_pair(
        self,
        pair_data: str,
        clip_number: int,
        auto_format: bool = False,
        log_to_console: bool = False,
        negative: str = "",
    ):
        if not pair_data:
            return ("", negative)

        # Förväntat format:
        #   prefix <<META_SEP>> suffix <<META_SEP>> clips_blob
        parts = pair_data.split(META_SEP)
        if len(parts) == 3:
            prefix, suffix, clips_blob = parts
        elif len(parts) == 2:
            prefix, clips_blob = parts
            suffix = ""
        else:
            prefix = ""
            suffix = ""
            clips_blob = parts[0] if parts else ""

        clips_blob = clips_blob or ""
        clips = clips_blob.split(CLIP_SEP) if clips_blob else []

        internal_index = clip_number - 1

        if not clips:
            combined = self._combine(prefix, "", suffix, auto_format)
            if log_to_console and combined:
                print("[Multi-Clip Selector] (no clips) →", combined)
            return (combined, negative)

        if internal_index < 0:
            internal_index = 0
        if internal_index >= len(clips):
            internal_index = len(clips) - 1

        clip_raw = clips[internal_index]

        combined = self._combine(prefix, clip_raw, suffix, auto_format)

        if log_to_console and combined:
            print(f"[Multi-Clip Selector] clip_number={clip_number} →", combined)

        return (combined, negative)

    @staticmethod
    def _clean_piece(piece: str) -> str:
        if not piece:
            return ""
        p = piece.strip()
        while p and p[-1] in [",", ";", " "]:
            p = p[:-1]
        return p.strip()

    @staticmethod
    def _combine(prefix: str, clip: str, suffix: str, auto_format: bool) -> str:
        prefix = prefix or ""
        clip = clip or ""
        suffix = suffix or ""

        if not auto_format:
            parts = []
            if prefix.strip():
                parts.append(prefix.strip())
            if clip.strip():
                parts.append(clip.strip())
            if suffix.strip():
                parts.append(suffix.strip())
            return "\n\n".join(parts)

        prefix_clean = MultiClipTextScriptClipSelector._clean_piece(prefix)
        clip_clean = MultiClipTextScriptClipSelector._clean_piece(clip)
        suffix_clean = MultiClipTextScriptClipSelector._clean_piece(suffix)

        parts = []
        if prefix_clean:
            parts.append(prefix_clean)
        if clip_clean:
            parts.append(clip_clean)
        if suffix_clean:
            parts.append(suffix_clean)

        if not parts:
            return ""

        text = ", ".join(parts)

        text = text.strip()
        if text and text[-1] not in [".", "!", "?"]:
            text += "."
        return text


# Registrering för ComfyUI
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
