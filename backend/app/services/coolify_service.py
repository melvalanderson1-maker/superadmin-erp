import httpx

from app.core.config import settings


class CoolifyService:
    def __init__(self):
        self.base_url = settings.COOLIFY_API_URL
        self.headers = {"Authorization": f"Bearer {settings.COOLIFY_API_TOKEN}"}

    async def crear_aplicacion(self, nombre: str, dominio: str) -> dict:
        """Placeholder — se implementa en la Fase 2 con los parámetros exactos de tu Coolify."""
        raise NotImplementedError("Pendiente: integración real con Coolify API")

    async def pausar_aplicacion(self, app_uuid: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/applications/{app_uuid}/stop", headers=self.headers)

    async def reanudar_aplicacion(self, app_uuid: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/applications/{app_uuid}/start", headers=self.headers)

    async def redeploy_aplicacion(self, app_uuid: str) -> None:
        async with httpx.AsyncClient() as client:
            await client.post(f"{self.base_url}/applications/{app_uuid}/restart", headers=self.headers)