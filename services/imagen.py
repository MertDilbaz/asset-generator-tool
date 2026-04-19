import os
import random
from vertexai.preview.vision_models import ImageGenerationModel

BATCH_SIZE = 4

class ImageEngine:
    def __init__(self):
        self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

    def generate_asset(self, prompt: str, seed: int = None):
        if seed is None:
            seed = random.randint(0, 2147483647)

        # İstemediğin tüm yapıları buraya yaz
        neg_prompt = ""

        images = self.model.generate_images(
            prompt=prompt,
            negative_prompt=neg_prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_few",
            seed=seed,
            add_watermark=False
        )

        return images[0], seed

    def generate_batch(self, prompt: str, seed: int = None):
        if seed is None:
            seed = random.randint(0, 2147483647)

        images = self.model.generate_images(
            prompt=prompt,
            number_of_images=BATCH_SIZE,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_few",
            seed=seed,
            add_watermark=False
        )

        return images, seed

image_engine = ImageEngine()