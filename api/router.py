from fastapi import APIRouter

from api.endpoints import ai, courses, news, professors, schedule

api_router = APIRouter()

api_router.include_router(professors.router, prefix="/professors", tags=["professors"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(schedule.router, prefix="/schedule", tags=["schedule"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
