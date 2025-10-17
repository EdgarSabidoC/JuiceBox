from fastapi import APIRouter
from WebClient.models.juiceShop import Response
from JuiceBox.Engine.api import JuiceBoxAPI

router = APIRouter()


@router.post("/", response_model=Response)
async def create():
    resp = await JuiceBoxAPI.start_js_container()
    return Response(message=resp.message, status=resp.status, data=resp.data)


@router.get("/", response_model=Response)
async def list_js_containers():
    resp = await JuiceBoxAPI.get_js_status()
    return Response(message=resp.message, status=resp.status, data=resp.data)
