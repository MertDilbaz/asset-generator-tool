import os
import random
from vertexai.preview.vision_models import ImageGenerationModel, Image as VertexImage

BATCH_SIZE = 4

class ImageEngine:
    def __init__(self):
        self.model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        self.neg_prompt = ""

    def generate_asset(self, prompt: str, seed: int = None):
        if seed is None:
            seed = random.randint(0, 2147483647)

        images = self.model.generate_images(
            prompt=prompt,
            negative_prompt=self.neg_prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_few",
            seed=seed,
            add_watermark=False
        )

        if not images:
            raise ValueError("Gorsel uretilemedi: Prompt guvenlik filtresine takilmis olabilir.")

        return images[0], seed

    def generate_batch(self, prompt: str, seed: int = None):
        if seed is None:
            seed = random.randint(0, 2147483647)

        images = self.model.generate_images(
            prompt=prompt,
            negative_prompt=self.neg_prompt,
            number_of_images=BATCH_SIZE,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_few",
            seed=seed,
            add_watermark=False
        )

        if not images:
            raise ValueError("Gorsel uretilemedi: Prompt guvenlik filtresine takilmis olabilir.")

        return images, seed

    def edit_asset(self, base_image_bytes: bytes, prompt: str, seed: int = None):
        if seed is None:
            seed = random.randint(0, 2147483647)

        base_image = VertexImage(image_bytes=base_image_bytes)

        images = self.model.edit_image(
            prompt=prompt,
            negative_prompt=self.neg_prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_few",
            seed=seed,
            add_watermark=False
        )

        if not images:
            raise ValueError("Gorsel duzenlenemedi: Guvenlik filtresine takilmis olabilir.")

        return images[0], seed

image_engine = ImageEngine()