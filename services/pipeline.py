import os
import numpy as np
from PIL import Image
import dataclasses
from typing import List, Tuple, Set

from utils.palette import get_palette_for_category


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
        self.palette_rgb = get_palette_for_category(category)
        self.palette = np.array(self.palette_rgb, dtype=np.uint8)
        self.palette_set = set(tuple(c) for c in self.palette_rgb)

    def _quantize(self, img_arr: np.ndarray) -> np.ndarray:
        pixels = img_arr.reshape(-1, 3).astype(np.int32)
        pal = self.palette.astype(np.int32)
        dist_sq = (
            np.sum(pixels**2, axis=1)[:, np.newaxis]
            + np.sum(pal**2, axis=1)
            - 2 * np.dot(pixels, pal.T)
        )
        indices = np.argmin(dist_sq, axis=1)
        return self.palette[indices].reshape(self.target_res[1], self.target_res[0], 3)

    def _reduce_colors(self, img_arr: np.ndarray, max_colors: int = 6) -> np.ndarray:
        pixels = img_arr.reshape(-1, 3)
        unique_colors = np.unique(pixels, axis=0)
        if len(unique_colors) <= max_colors:
            return img_arr.reshape(self.target_res[1], self.target_res[0], 3)
        centroids = unique_colors[:max_colors].astype(np.float32)
        for _ in range(10):
            dist = np.sum((pixels[:, np.newaxis] - centroids[np.newaxis, :])**2, axis=2)
            labels = np.argmin(dist, axis=1)
            for i in range(len(centroids)):
                mask = labels == i
                if np.sum(mask) > 0:
                    centroids[i] = pixels[mask].mean(axis=0)
        result = centroids[labels].astype(np.uint8).reshape(self.target_res[1], self.target_res[0], 3)
        return result

    def _apply_border_flood_fill(self, img_arr: np.ndarray) -> np.ndarray:
        h, w, _ = img_arr.shape
        border_pixels = np.concatenate([
            img_arr[0, :], img_arr[-1, :], img_arr[:, 0], img_arr[:, -1]
        ])
        unique, counts = np.unique(border_pixels, axis=0, return_counts=True)
        sorted_indices = np.argsort(counts)[::-1]
        bg_seed_color = unique[sorted_indices[0]]
        match_mask = np.all(img_arr == bg_seed_color, axis=-1)
        bg_pixel_count = np.sum(match_mask)
        total_pixels = h * w
        if bg_pixel_count > total_pixels * 0.85:
            if len(sorted_indices) > 1:
                bg_seed_color = unique[sorted_indices[1]]
                match_mask = np.all(img_arr == bg_seed_color, axis=-1)
        visited = np.zeros((h, w), dtype=bool)
        mask = np.zeros((h, w), dtype=bool)
        stack = []
        for y in [0, h-1]:
            for x in range(w):
                if match_mask[y, x]:
                    stack.append((y, x))
        for x in [0, w-1]:
            for y in range(1, h-1):
                if match_mask[y, x]:
                    stack.append((y, x))
        while stack:
            y, x = stack.pop()
            if not visited[y, x]:
                visited[y, x] = True
                mask[y, x] = True
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and match_mask[ny, nx] and not visited[ny, nx]:
                        stack.append((ny, nx))
        rgba = np.empty((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3], rgba[:, :, 3] = img_arr, np.where(mask, 0, 255)
        return rgba

    def validate(self, rgba_arr: np.ndarray, category: str) -> List[str]:
        errors = []
        rgb_data = rgba_arr[:, :, :3].reshape(-1, 3)
        unique_colors = np.unique(rgb_data, axis=0)
        for color in unique_colors:
            if tuple(color) not in self.palette_set:
                errors.append(f"ERR_PALETTE_BREACH: {tuple(color)}")
                break
        color_count = len(unique_colors)
        if color_count < 4:
            errors.append(f"ERR_COLOR_COUNT_TOO_LOW: {color_count} (min: 4)")
        elif color_count > 6:
            errors.append(f"ERR_COLOR_COUNT_TOO_HIGH: {color_count} (max: 6)")
        alpha = rgba_arr[:, :, 3]
        trans_ratio = np.sum(alpha == 0) / alpha.size
        if category == "ground" and trans_ratio > 0.50:
            errors.append(f"ERR_GROUND_TRANSPARENCY_LIMIT: {trans_ratio:.2%}")
        elif category in ["objects", "crops"] and trans_ratio < 0.05:
            errors.append(f"ERR_OBJECT_ISOLATION_FAILURE: {trans_ratio:.2%}")
        return errors

    def compile_asset(self, raw_image: Image.Image, category: str) -> PipelineResult:
        def _process(img):
            arr = np.array(img.convert("RGB").resize(self.target_res, Image.NEAREST))
            arr = self._reduce_colors(arr, max_colors=6)
            arr = self._quantize(arr)
            return self._apply_border_flood_fill(arr)
        current_rgba = _process(raw_image)
        errors = self.validate(current_rgba, category)
        if errors:
            print(f"  [DEBUG] First pass failed: {errors}")
            repair_img = Image.fromarray(current_rgba[:, :, :3], "RGB")
            current_rgba = _process(repair_img)
            errors = self.validate(current_rgba, category)
            if errors:
                print(f"  [DEBUG] Second pass failed: {errors}")
        return PipelineResult(
            image=Image.fromarray(current_rgba, "RGBA"),
            is_success=len(errors) == 0,
            errors=errors,
            metadata={
                "category": category,
                "unique_colors": len(np.unique(current_rgba[:, :, :3].reshape(-1, 3), axis=0)),
                "palette_used": self.category,
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