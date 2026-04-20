import os
import re
import sys
from enum import Enum
from fastapi import FastAPI, HTTPException, Query, status, File, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv
import vertexai
from PIL import Image

load_dotenv("envDosyasi.env")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

app = FastAPI(title="Pixel Asset Generator Compiler v1.3")

class AssetCategory(str, Enum):
    ground = "ground"
    crops = "crops"
    objects = "objects"
    tools = "tools"
    water = "water"
    magic = "magic"

class BatchAssetItem(BaseModel):
    name: str
    category: AssetCategory
    hard_surface: bool = False

class BatchRequest(BaseModel):
    assets: list[BatchAssetItem]
    seed: int = None

try:
    from services.gemini import prompt_engine
    from services.imagen import image_engine
    from services.pipeline import pixel_pipeline
except ImportError as e:
    print(f"CRITICAL: Service Import Failure: {e}")
    sys.exit(1)

def get_next_asset_id():
    os.makedirs("outputs/raw", exist_ok=True)
    os.makedirs("outputs/pixel", exist_ok=True)
    max_id = 0
    try:
        for filename in os.listdir("outputs/raw"):
            match = re.search(r"AGT-(\d+)", filename)
            if match: max_id = max(max_id, int(match.group(1)))
    except FileNotFoundError: pass
    return f"AGT-{max_id + 1:04d}"

def save_asset_result(gen_image, asset_id, safe_name, category, used_seed):
    raw_path = f"outputs/raw/{asset_id}_{safe_name}_raw.png"
    pixel_path = f"outputs/pixel/{asset_id}_{safe_name}_32x32.png"

    result = pixel_pipeline.process(gen_image, pixel_path, category)

    if result.is_success:
        gen_image.save(raw_path)
        return {
            "asset_id": asset_id,
            "status": "Success",
            "metadata": {
                "category": category,
                "unique_colors": result.metadata.get("unique_colors"),
                "seed": used_seed
            },
            "output_path": pixel_path,
            "errors": []
        }
    else:
        gen_image.save(raw_path)
        return {
            "asset_id": asset_id,
            "status": "Failed",
            "metadata": {
                "category": category,
                "seed": used_seed
            },
            "output_path": None,
            "errors": result.errors
        }

@app.post("/generate-asset", status_code=status.HTTP_201_CREATED)
async def generate_asset(
    asset_name: str,
    category: AssetCategory = Query(AssetCategory.ground),
    hard_surface: bool = Query(False),
    seed: int = Query(None, description="Seed for reproducibility")
):
    try:
        asset_id = get_next_asset_id()
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', asset_name).strip('_')[:20].lower()

        print(f"\n--- [İŞLEM: {asset_id} | {category.value.upper()} | SEED: {seed}] ---")

        ai_prompt = prompt_engine.generate_prompt(asset_name, category.value, hard_surface)
        generated, used_seed = image_engine.generate_asset(ai_prompt, seed=seed)

        if not generated:
            raise HTTPException(status_code=502, detail="Imagen API failed to return image.")

        gen_image = generated._pil_image

        raw_path = f"outputs/raw/{asset_id}_{safe_name}_raw.png"
        pixel_path = f"outputs/pixel/{asset_id}_{safe_name}_32x32.png"

        result = pixel_pipeline.process(gen_image, pixel_path, category.value)

        if not result.is_success:
            gen_image.save(raw_path)
            raise HTTPException(
                status_code=422,
                detail={"message": "PixelArt Validation Failed", "errors": result.errors}
            )

        gen_image.save(raw_path)

        return {
            "status": "Success",
            "asset_id": asset_id,
            "metadata": {
                "category": category.value,
                "hard_surface": hard_surface,
                "unique_colors": result.metadata.get("unique_colors"),
                "seed": used_seed
            },
            "output_path": pixel_path
        }

    except HTTPException as e: raise e
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-batch", status_code=status.HTTP_201_CREATED)
async def generate_batch(request: BatchRequest):
    try:
        print(f"\n--- [BATCH İŞLEM | {len(request.assets)} ASSET | SEED: {request.seed}] ---")

        assets_by_category = {}
        for asset in request.assets:
            cat = asset.category.value
            if cat not in assets_by_category:
                assets_by_category[cat] = []
            assets_by_category[cat].append(asset)

        results = []
        current_id = int(get_next_asset_id().split("-")[1])

        for category, assets in assets_by_category.items():
            prompt = prompt_engine.generate_prompt(
                ", ".join([a.name for a in assets]),
                category,
                assets[0].hard_surface if assets else False
            )

            gen_images, used_seed = image_engine.generate_batch(prompt, seed=request.seed)

            for i, generated in enumerate(gen_images):
                if i < len(assets):
                    asset = assets[i]
                    asset_id = f"AGT-{current_id:04d}"
                    current_id += 1
                    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', asset.name).strip('_')[:20].lower()

                    print(f"  Processing: {asset_id} - {asset.name}")

                    gen_image = generated._pil_image
                    result = save_asset_result(gen_image, asset_id, safe_name, category, used_seed)
                    results.append(result)

        success_count = sum(1 for r in results if r["status"] == "Success")
        print(f"--- [BATCH COMPLETE | {success_count}/{len(results)} SUCCESS] ---")

        return {
            "status": "Batch Complete",
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "results": results
        }

    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "Online"}

@app.post("/img2img", status_code=status.HTTP_201_CREATED)
async def img2img(
    reference_image: UploadFile = File(...),
    asset_name: str = Query(...),
    category: AssetCategory = Query(AssetCategory.ground),
    hard_surface: bool = Query(False),
    seed: int = Query(None, description="Seed for reproducibility")
):
    try:
        asset_id = get_next_asset_id()
        safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', asset_name).strip('_')[:20].lower()

        print(f"\n--- [IMG2IMG: {asset_id} | {category.value.upper()} | SEED: {seed}] ---")

        image_bytes = await reference_image.read()

        ai_prompt = prompt_engine.generate_prompt(asset_name, category.value, hard_surface)

        generated, used_seed = image_engine.edit_asset(image_bytes, ai_prompt, seed=seed)

        if not generated:
            raise HTTPException(status_code=502, detail="Imagen API failed to return image.")

        gen_image = generated._pil_image

        raw_path = f"outputs/raw/{asset_id}_{safe_name}_img2img_raw.png"
        pixel_path = f"outputs/pixel/{asset_id}_{safe_name}_img2img_32x32.png"

        result = pixel_pipeline.process(gen_image, pixel_path, category.value)

        if not result.is_success:
            gen_image.save(raw_path)
            raise HTTPException(
                status_code=422,
                detail={"message": "PixelArt Validation Failed", "errors": result.errors}
            )

        gen_image.save(raw_path)

        return {
            "status": "Success",
            "asset_id": asset_id,
            "metadata": {
                "category": category.value,
                "hard_surface": hard_surface,
                "unique_colors": result.metadata.get("unique_colors"),
                "seed": used_seed,
                "process_type": "img2img"
            },
            "output_path": pixel_path
        }

    except HTTPException as e: raise e
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))