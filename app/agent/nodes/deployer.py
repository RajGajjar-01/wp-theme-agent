import logging
from pathlib import Path

import httpx
from langgraph.config import get_stream_writer

from app.agent.models import DeployStatus
from app.agent.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


async def deployer_node(state: AgentState) -> dict:
    writer = get_stream_writer()
    errors: list[str] = list(state.get("errors", []))

    zip_path_str = state.get("zip_path", "")
    zip_path = Path(zip_path_str) if zip_path_str else None

    wp_site_url = settings.WP_SITE_URL
    wp_secret = settings.WP_SECRET_TOKEN

    if not wp_site_url or not wp_secret:
        writer({
            "node": "deployer",
            "status": "complete",
            "message": "Auto-deploy skipped — WP_SITE_URL or WP_SECRET_TOKEN not configured",
        })
        return {
            "deploy_status": DeployStatus(
                method="skipped",
                success=True,
                message="Deploy skipped — no WordPress site configured",
            ),
            "errors": errors,
        }

    if not zip_path or not zip_path.is_file():
        errors.append("Deploy failed — ZIP file not found")
        writer({
            "node": "deployer",
            "status": "failed",
            "message": "ZIP file not found at expected path",
        })
        return {
            "deploy_status": DeployStatus(
                method="rest_api",
                success=False,
                message="ZIP file not found",
            ),
            "errors": errors,
        }

    deploy_url = f"{wp_site_url.rstrip('/')}/wp-json/wp-theme-agent/v1/deploy"

    writer({
        "node": "deployer",
        "status": "running",
        "message": f"Deploying {zip_path.name} to {wp_site_url}...",
    })

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(zip_path, "rb") as f:
                resp = await client.post(
                    deploy_url,
                    headers={"X-WP-Theme-Agent-Token": wp_secret},
                    files={"theme_zip": (zip_path.name, f, "application/zip")},
                    data={"activate": "true"},
                )

            if resp.status_code == 200:
                data = resp.json()
                activated = data.get("activated", False)
                theme = data.get("theme", "unknown")
                msg = f"Theme \"{theme}\" deployed" + (" and activated" if activated else "")

                writer({"node": "deployer", "status": "complete", "message": msg})

                return {
                    "deploy_status": DeployStatus(
                        method="rest_api",
                        success=True,
                        message=msg,
                        url=wp_site_url,
                    ),
                    "errors": errors,
                }
            else:
                error_detail = resp.text[:500]
                errors.append(f"Deploy failed (HTTP {resp.status_code}): {error_detail}")
                writer({
                    "node": "deployer",
                    "status": "failed",
                    "message": f"Deploy failed — HTTP {resp.status_code}",
                })

                return {
                    "deploy_status": DeployStatus(
                        method="rest_api",
                        success=False,
                        message=f"HTTP {resp.status_code}: {error_detail}",
                    ),
                    "errors": errors,
                }

    except httpx.TimeoutException:
        errors.append("Deploy timed out after 60s")
        writer({"node": "deployer", "status": "failed", "message": "Deploy timed out"})
        return {
            "deploy_status": DeployStatus(method="rest_api", success=False, message="Timeout"),
            "errors": errors,
        }
    except Exception as e:
        errors.append(f"Deploy error: {e}")
        writer({"node": "deployer", "status": "failed", "message": f"Deploy error: {e}"})
        return {
            "deploy_status": DeployStatus(method="rest_api", success=False, message=str(e)),
            "errors": errors,
        }
