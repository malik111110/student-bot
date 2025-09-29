from fastapi import APIRouter

from core.data_loader import load_json_data

router = APIRouter()


@router.get("/", summary="Get the weekly schedule")
def get_schedule():
    """
    Retrieve the course schedule for the current week.
    """
    return load_json_data("schedule.json")
