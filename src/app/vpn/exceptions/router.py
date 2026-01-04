# Import your logic functions. Adjust the import path according to your project structure.
from fastapi import APIRouter, HTTPException, status

from app.core.logger import logger

# Import your schemas
from app.vpn.exceptions.schemas import DomainExceptionResponse
from app.vpn.exceptions.service import domain_exceptions_needs_sync, get_domain_exceptions_as_datatype

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
        logger.debug("Get domain exception route")
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
