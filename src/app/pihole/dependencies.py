from .client import PiholeClient

# Create a singleton instance
_pihole_client_instance = None


def get_pihole_service() -> PiholeClient:
    """
    Dependency injection for PiholeClient.
    Ensures we reuse the authenticated session.
    """
    global _pihole_client_instance
    if _pihole_client_instance is None:
        _pihole_client_instance = PiholeClient()
    return _pihole_client_instance
