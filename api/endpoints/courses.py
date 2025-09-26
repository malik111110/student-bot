from fastapi import APIRouter
from core.data_loader import load_json_data

router = APIRouter()

@router.get("/", summary="Get all courses")
def get_courses():
    """
    Retrieve a list of all available courses.
    """
    return load_json_data("courses.json")
