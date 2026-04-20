import os

def compile_prompt(*components) -> str:
    valid_parts = [text.strip() for text in components if text is not None and text.strip()]
    return "\n\n".join(valid_parts)

class PromptEngine:
    def __init__(self, styles_dir: str = "styles"):
        self.styles_dir = styles_dir

    def _read_style_file(self, *path_parts: str) -> str:
        filepath = os.path.join(self.styles_dir, *path_parts)
        if not os.path.exists(filepath):
            return ""
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read().strip()
            return content if content else ""

    def generate_prompt(self, asset_name: str, category: str, use_hard_surface: bool = False) -> str:
        contract = self._read_style_file("core", "contract.txt")
        anti = self._read_style_file("core", "anti_style.txt")
        base = self._read_style_file("core", "base.txt")
        lighting = self._read_style_file("core", "lighting.txt")
        palette = self._read_style_file("core", "palette.txt")

        category_style = self._read_style_file("categories", f"{category}.txt")

        overrides = []
        if use_hard_surface:
            overrides.append(self._read_style_file("overrides", "hard_surface.txt"))

        isolated_subject = f"Subject: {asset_name}"
        if category == "ground":
            isolated_subject = f"Subject: A completely FLAT 2D top-down pixel art seamless texture pattern of {asset_name}. Filling the entire frame edge-to-edge seamlessly."
        elif category in ["objects", "tools", "crops"]:
            isolated_subject = f"Subject: Single isolated 2D pixel object of {asset_name} on a blank solid background."

        components = [
            isolated_subject,
            contract,
            base,
            lighting,
            palette,
            category_style,
            *overrides
        ]
        return compile_prompt(*components)

prompt_engine = PromptEngine()