from typing import Dict

import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

from ocr_server.dependencies import Rotator
from ocr_server.router import ocr
from ocr_server.router.ocr import logger

app = FastAPI(
        title="OCR Server",
        description="OCR服务器接口文档",
        version="0.1.0",

)
app.include_router(ocr.router)


@app.get("/")
async def root():
    return RedirectResponse("/docs")
    # return {"message": "查看/docs以了解接口使用方法"}

@app.get("/test/{name}")
async def test_name(name:str):
    return name
    # return {"message": "查看/docs以了解接口使用方法"}

@app.post("/test")
async def test(data:Dict):
    print(data)
    return data

@app.on_event("startup")
async def startup_event():
    rotator = Rotator("10 MB", "00:00")
    logger.add("logs/file_{time}.log",rotation=rotator.should_rotate,diagnose=False,catch=False)
    logger.success("startup")

@app.on_event("shutdown")
async def shutdown_event():
    logger.success("shutdown")

if __name__ == "__main__":
    uvicorn.run(app='main:app', host='0.0.0.0', port=8002, log_config="config/uvicorn_config.json")

