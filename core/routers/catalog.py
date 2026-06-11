from fastapi import APIRouter

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/programming-languages")
async def get_programming_languages():
    return ""


@router.get("/technologies")
async def get_technologies():
    return ""


@router.get("/addons")
async def get_addons():
    return ""


@router.get("/programming-languages/random")
async def get_random_programming_language():
    return {"programming_language": ""}


@router.get("/technologies/random")
async def get_random_technology():
    return {"technology": ""}


@router.get("/addons/random")
async def get_random_addon():
    return {"addon": ""}
