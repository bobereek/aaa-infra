import asyncio
from io import BytesIO
from typing import List

import httpx
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from image_provider_client import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
    ImageNotFoundError,
    ImageProviderClient,
)
from models.plate_reader import InvalidImage, PlateReader

app = FastAPI()
plate_reader = PlateReader.load_from_file("./src/model_weights/plate_reader_model.pth")
EXTERNAL_SERVICE_URL = "http://89.169.157.72:8080/images/{img_id}"
image_provider_client = ImageProviderClient(EXTERNAL_SERVICE_URL, timeout_seconds=10.0)


class ImageRequest(BaseModel):
    ids: List[int]


async def fetch_and_read(img_id: int, client: httpx.AsyncClient):
    try:
        image_bytes = await image_provider_client.get_image(img_id, client)
        result = await asyncio.to_thread(plate_reader.read_text, BytesIO(image_bytes))
        return {
            "id": img_id,
            "detected_text": result,
            "status": "done",
            "status_code": status.HTTP_200_OK,
        }
    except ImageNotFoundError as exc:
        return {
            "id": img_id,
            "error": str(exc),
            "status": "failed",
            "status_code": status.HTTP_404_NOT_FOUND,
        }
    except ExternalServiceTimeoutError as exc:
        return {
            "id": img_id,
            "error": str(exc),
            "status": "failed",
            "status_code": status.HTTP_504_GATEWAY_TIMEOUT,
        }
    except ExternalServiceUnavailableError as exc:
        return {
            "id": img_id,
            "error": str(exc),
            "status": "failed",
            "status_code": status.HTTP_502_BAD_GATEWAY,
        }
    except InvalidImage:
        return {
            "id": img_id,
            "error": "External service returned invalid image",
            "status": "failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        }
    except Exception as e:
        return {
            "id": img_id,
            "error": str(e),
            "status": "error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }


@app.get("/")
async def root():
    return {"message": "OK"}


@app.get("/process-image/{img_id}")
async def process_single(img_id: int):
    async with httpx.AsyncClient() as client:
        result = await fetch_and_read(img_id, client)
        if result.get("status") != "done":
            raise HTTPException(status_code=result["status_code"], detail=result["error"])
        return result


@app.post("/process-images")
async def process_multiple(request: ImageRequest):
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids must contain at least one image id",
        )

    async with httpx.AsyncClient() as client:
        tasks = [fetch_and_read(img_id, client) for img_id in request.ids]
        results = await asyncio.gather(*tasks)

    all_ok = all(item["status"] == "done" for item in results)
    return {
        "total": len(request.ids),
        "success": sum(item["status"] == "done" for item in results),
        "failed": sum(item["status"] != "done" for item in results),
        "all_ok": all_ok,
        "results": results,
    }
