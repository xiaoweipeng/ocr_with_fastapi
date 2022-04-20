from typing import List, Dict
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.responses import RedirectResponse
# import sys
# sys.path.append('../')
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
    logger.add("log/file_{time}.log",rotation="1 day")

if __name__ == "__main__":
    # logger.debug("That's it, beautiful and simple logging!")
    uvicorn.run(app='main:app', host='0.0.0.0', port=8002, log_config="config/uvicorn_config.json")

