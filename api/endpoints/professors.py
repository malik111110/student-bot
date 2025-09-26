from fastapi import APIRouter
from core.data_loader import load_json_data

router = APIRouter()

@router.get("/", summary="Get all professors")
def get_professors():
    """
    Retrieve a list of all professors with their contact information.
    """
    return load_json_data("professors.json")
