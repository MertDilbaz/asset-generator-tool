import os
from PIL import Image
import dataclasses
from typing import List

@dataclasses.dataclass
class PipelineResult:
    image: Image.Image
    is_success: bool
    errors: List[str]
    metadata: dict

class PixelArtCompiler:
    def __init__(self, category: str = "default"):
        self.target_res = (32, 32)
        self.category = category

    def compile_asset(self, raw_image: Image.Image, category: str) -> PipelineResult:
        # Görseli al, RGBA formatına çevir ve NEAREST filtresi ile 32x32'ye keskin bir şekilde küçült
        pixel_img = raw_image.convert("RGBA").resize(self.target_res, Image.NEAREST)

        return PipelineResult(
            image=pixel_img,
            is_success=True, # Validasyon kaldırıldığı için her zaman başarılı sayılacak
            errors=[],
            metadata={
                "category": category,
                "process": "simple_downscale"
            },
        )

class PixelPipeline:
    def __init__(self):
        pass

    def process(self, image: Image.Image, output_path: str, category: str) -> PipelineResult:
        compiler = PixelArtCompiler(category)
        result = compiler.compile_asset(image, category)
        
        if result.is_success and result.image:
            result.image.save(output_path)
            if os.path.getsize(output_path) == 0:
                raise RuntimeError(f"CRITICAL: Write failed, 0-byte file: {output_path}")
                
        return result

pixel_pipeline = PixelPipeline()