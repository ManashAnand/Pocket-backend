from fastapi import APIRouter

router = APIRouter()

@router.get('/nice-health')
def nice_health():
    return {"health":"nice"}