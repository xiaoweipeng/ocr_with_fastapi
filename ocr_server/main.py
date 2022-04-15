from typing import List, Dict
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from ocr_server.router import ocr

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

@app.post("/test")
async def test(data:Dict):
    print(data)
    return data

if __name__ == "__main__":
    uvicorn.run(app='main:app', host='0.0.0.0', port=8002, log_config="config/uvicorn_config.json")

