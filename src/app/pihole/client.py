from typing import Any, Dict, List, Optional

import requests
import urllib3
from fastapi import HTTPException, status
from urllib3.exceptions import InsecureRequestWarning

from app.core.config import get_settings

settings = get_settings()

# In a secure environment, we should trust the CA,
# but for local Pi-hole self-signed certs, we suppress warnings.
urllib3.disable_warnings(InsecureRequestWarning)


class PiholeClient:
    def __init__(self):
        self.base_url = settings.PIHOLE_API_URL
        self.password = settings.PIHOLE_PASSWORD
        self.sid: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False  # Explicitly disable verification for local setup
        self.session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})

    def _authenticate(self) -> None:
        """Authenticates against Pi-hole and stores the Session ID (SID)."""
        url = f"{self.base_url}/auth"
        payload = {"password": self.password}

        try:
            response = self.session.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.sid = data.get("session", {}).get("sid")
                if not self.sid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED, detail="Pi-hole auth failed: No SID returned"
                    )
            else:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pi-hole authentication failed")
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Connection failure: {str(e)}"
            ) from e

    def _request(self, method: str, endpoint: str, json: Optional[Dict] = None, retry: bool = True) -> Any:
        """
        Internal wrapper to handle SID injection and auto-re-login on 401.
        """
        if not self.sid:
            self._authenticate()

        headers = {"sid": self.sid}
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, headers=headers, json=json)

            # If unauthorized, try to re-auth once
            if response.status_code == 401 and retry:
                self._authenticate()
                # Update header with new SID
                headers["sid"] = self.sid
                response = self.session.request(method, url, headers=headers, json=json)

            if not response.ok:
                # Attempt to extract error message from Pi-hole
                try:
                    error_detail = response.json().get("error", response.reason)
                except ValueError:
                    error_detail = response.reason

                raise HTTPException(status_code=response.status_code, detail=f"Pi-hole API Error: {error_detail}")

            # Return empty dict for 204 No Content, else JSON
            if response.status_code == 204:
                return {}
            return response.json()

        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Network Error: {str(e)}"
            ) from e

    # --- Business Logic Methods ---

    def get_summary(self) -> Dict:
        """
        Fetches summary and transforms nested Pi-hole API structure
        to a flat structure compliant with SummaryResponse schema.
        """
        raw_data = self._request("GET", "/stats/summary")

        # Extract nested values safely using .get() to avoid KeyErrors
        queries = raw_data.get("queries", {})
        gravity = raw_data.get("gravity", {})
        clients = raw_data.get("clients", {})

        # Prepare values
        active_clients = clients.get("active", 0)
        total_clients = clients.get("total", 0)

        # Logic: Remove localhost (Gateway itself) from stats if > 0
        if active_clients > 0:
            active_clients -= 1
            total_clients -= 1

        # Build response matching schemas.SummaryResponse
        transformed_data = {
            "domains_being_blocked": gravity.get("domains_being_blocked", 0),
            "dns_queries_today": queries.get("total", 0),
            "ads_blocked_today": queries.get("blocked", 0),
            "ads_percentage_today": int(round(queries.get("percent_blocked", 0.0))),
            "clients": {
                "active": active_clients,
                "total": total_clients,
            },
        }

        return transformed_data

    def get_status(self) -> bool:
        data = self._request("GET", "/dns/blocking")
        # Map 'enabled'/'disabled' to boolean
        return data.get("blocking") == "enabled"

    def set_status(self, enabled: bool) -> bool:
        payload = {
            "blocking": enabled,
            "timer": None,  # Permanent change
        }
        data = self._request("POST", "/dns/blocking", json=payload)
        return data.get("blocking") == "enabled"

    def get_whitelist(self) -> List[Dict]:
        data = self._request("GET", "/domains/allow")
        return data.get("domains", [])

    def update_whitelist(self, domain: str, enabled: bool) -> None:
        """Updates detailed domain setting or creates it if missing."""
        # 1. Check if exists
        try:
            resp = self._request("GET", f"/domains/allow/exact/{domain}")
            existing = resp.get("domains", [])
        except HTTPException:
            existing = []

        if existing:
            # Update
            self._request("PUT", f"/domains/allow/exact/{domain}", json={"enabled": enabled})
        else:
            # Create
            payload = {
                "domain": domain,
                "groups": [0],  # Default group
                "enabled": enabled,
            }
            self._request("POST", "/domains/allow/exact", json=payload)

    def delete_whitelist(self, domain: str) -> None:
        self._request("DELETE", f"/domains/allow/exact/{domain}")
