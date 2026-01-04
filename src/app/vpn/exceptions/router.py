from fastapi import APIRouter, HTTPException, Path, status

from app.core.logger import logger
from app.vpn.exceptions.schemas import DomainExceptionEntry, DomainExceptionResponse
from app.vpn.exceptions.service import (
    delete_domain_exception,
    domain_exceptions_needs_sync,
    get_domain_exceptions_as_datatype,
    sync_domain_exceptions,
    update_domain_exceptions,
)

router = APIRouter()


@router.get(
    "/domains",
    response_model=DomainExceptionResponse,
    summary="Get Domain Exceptions",
    description="Retrieves the list of domains routed outside the VPN tunnel and the sync status.",
)
async def get_domain_exceptions_route():
    """
    Fetches current domain exception configuration.

    Returns:
        DomainExceptionResponse: Object containing the list of domains and the sync flag.
    """
    try:
        logger.debug("Retrieving domain exceptions.")
        # Fetch data using the provided low-level functions
        exceptions_list = get_domain_exceptions_as_datatype()
        sync_needed = domain_exceptions_needs_sync()

        # Construct the response object based on the Pydantic schema
        return DomainExceptionResponse(domain_exceptions=exceptions_list, domain_exceptions_needs_sync=sync_needed)

    except Exception as e:
        logger.error(f"Failed to retrieve domain exceptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve domain exceptions: {str(e)}"
        ) from e


@router.post(
    "/domains",
    status_code=status.HTTP_200_OK,
    summary="Add or Update Domain Exception",
    description="Adds a new domain or updates the active status of an existing domain.",
)
async def update_domain_exception_route(entry: DomainExceptionEntry):
    """
    Updates or adds a domain exception entry.

    Args:
        entry (DomainExceptionEntry): The domain data containing the URL and active status.
    """
    try:
        logger.debug(f"Updating domain exception for: {entry.domain_url}")
        update_domain_exceptions(entry.domain_url, entry.active)
        return {"detail": "Domain updated successfully.", "domain": entry.domain_url}

    except HTTPException as e:
        # Re-raise HTTPExceptions explicitly raised by the service (e.g. Bad Request)
        raise e
    except Exception as e:
        logger.error(f"Failed to update domain exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update domain exception: {str(e)}"
        ) from e


@router.delete(
    "/domains/{domain_url}",
    status_code=status.HTTP_200_OK,
    summary="Delete Domain Exception",
    description="Removes a domain from the exception list.",
)
async def delete_domain_exception_route(
    domain_url: str = Path(..., description="The domain URL to be removed (e.g., example.com)"),
):
    """
    Deletes a specific domain exception.

    Args:
        domain_url (str): The domain to remove.
    """
    try:
        logger.debug(f"Deleting domain exception: {domain_url}")
        delete_domain_exception(domain_url)
        return {"detail": f"Domain '{domain_url}' deleted successfully."}

    except HTTPException as e:
        # Re-raise HTTPExceptions explicitly raised by the service (e.g. Not Found)
        raise e
    except Exception as e:
        logger.error(f"Failed to delete domain exception: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete domain exception: {str(e)}"
        ) from e


@router.post(
    "/domains/sync",
    status_code=status.HTTP_200_OK,
    summary="Sync Domain Exceptions",
    description="Applies changes to the system (Firewall/OpenVPN) if the sync flag is set.",
)
async def sync_domain_exceptions_route():
    """
    Triggers the synchronization process to apply changes to the firewall/VPN.
    """
    try:
        logger.info("Triggering domain exception synchronization via API.")

        # Check if sync is actually needed logic could be added here,
        # but service.sync_domain_exceptions handles the process regardless.
        sync_domain_exceptions()

        return {"detail": "Domain exceptions synchronized successfully."}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to sync domain exceptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to sync domain exceptions: {str(e)}"
        ) from e
