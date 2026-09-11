import uuid as uuid_lib

import httpx

from app.core.config import settings

REPO_INMOBILOT = "https://github.com/melvalanderson1-maker/inmobilot"  # ajusta a tu repo real de Inmobilot


class CoolifyService:
    def __init__(self):
        self.base_url = settings.COOLIFY_API_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.COOLIFY_API_TOKEN}",
            "Content-Type": "application/json",
        }
        self.server_uuid = settings.COOLIFY_SERVER_UUID
        self.project_uuid_erp = settings.COOLIFY_PROJECT_ERP_UUID  # proyecto Coolify donde viven las instancias de clientes

    async def _post(self, path: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{self.base_url}{path}", headers=self.headers, json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _get(self, path: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def crear_base_datos(self, nombre_tenant_slug: str) -> dict:
        payload = {
            "project_uuid": self.project_uuid_erp,
            "server_uuid": self.server_uuid,
            "environment_name": "production",
            "name": f"db-{nombre_tenant_slug}",
            "postgres_user": "postgres",
            "postgres_db": nombre_tenant_slug.replace("-", "_"),
            "instant_deploy": True,
        }
        return await self._post("/databases/postgresql", payload)

    async def crear_backend(self, nombre_tenant_slug: str, dominio_api: str, database_url: str) -> dict:
        payload = {
            "project_uuid": self.project_uuid_erp,
            "server_uuid": self.server_uuid,
            "environment_name": "production",
            "name": f"backend-{nombre_tenant_slug}",
            "git_repository": REPO_INMOBILOT,
            "git_branch": "main",
            "build_pack": "dockerfile",
            "base_directory": "/backend",
            "ports_exposes": "8000",
            "domains": dominio_api,
            "instant_deploy": False,
        }
        return await self._post("/applications/public", payload)

    async def crear_frontend(self, nombre_tenant_slug: str, dominio_publico: str) -> dict:
        payload = {
            "project_uuid": self.project_uuid_erp,
            "server_uuid": self.server_uuid,
            "environment_name": "production",
            "name": f"frontend-{nombre_tenant_slug}",
            "git_repository": REPO_INMOBILOT,
            "git_branch": "main",
            "build_pack": "dockerfile",
            "base_directory": "/frontend",
            "ports_exposes": "80",
            "domains": dominio_publico,
            "instant_deploy": False,
        }
        return await self._post("/applications/public", payload)

    async def set_env_var(self, app_uuid: str, clave: str, valor: str) -> None:
        payload = {"key": clave, "value": valor, "is_preview": False}
        await self._post(f"/applications/{app_uuid}/envs", payload)

    async def obtener_aplicacion(self, app_uuid: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{self.base_url}/applications/{app_uuid}", headers=self.headers)
            resp.raise_for_status()
            return resp.json()

    async def deploy(self, app_uuid: str) -> None:
        async with httpx.AsyncClient(timeout=60) as client:
            await client.post(
                f"{self.base_url}/deploy",
                headers=self.headers,
                params={"uuid": app_uuid},
            )

    async def pausar(self, app_uuid: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{self.base_url}/applications/{app_uuid}/stop", headers=self.headers)

    async def reanudar(self, app_uuid: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(f"{self.base_url}/applications/{app_uuid}/start", headers=self.headers)

    async def redeploy(self, app_uuid: str) -> None:
        await self.deploy(app_uuid)