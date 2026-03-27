from dataclasses import dataclass

import httpx


class ExternalServiceTimeoutError(Exception):
    pass


class ExternalServiceUnavailableError(Exception):
    pass


class ImageNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ImageProviderClient:
    base_url_pattern: str
    timeout_seconds: float = 10.0

    async def get_image(self, image_id: int, client: httpx.AsyncClient) -> bytes:
        url = self.base_url_pattern.format(img_id=image_id)
        try:
            response = await client.get(url, timeout=self.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ExternalServiceTimeoutError(f"Timeout while fetching image {image_id}") from exc
        except httpx.HTTPError as exc:
            raise ExternalServiceUnavailableError(f"External service request failed for image {image_id}") from exc

        if response.status_code == 404:
            raise ImageNotFoundError(f"Image {image_id} not found")

        if response.status_code != 200:
            raise ExternalServiceUnavailableError(f"External service returned status {response.status_code} for image {image_id}")

        return response.content
