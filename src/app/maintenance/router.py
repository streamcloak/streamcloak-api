from fastapi import APIRouter, HTTPException

from .schemas import RebootScheduleRequest, RebootScheduleResponse
from .service import MaintenanceService

router = APIRouter()


@router.get("/reboot-schedule", response_model=RebootScheduleResponse)
async def get_reboot_schedule():
    """
    Get the currently configured auto-reboot schedule.
    """
    return MaintenanceService.get_reboot_schedule()


@router.post("/reboot-schedule")
async def set_reboot_schedule(schedule: RebootScheduleRequest):
    """
    Update or disable the system auto-reboot schedule.
    """
    try:
        MaintenanceService.set_reboot_schedule(schedule)
        return {"message": "Reboot schedule updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
