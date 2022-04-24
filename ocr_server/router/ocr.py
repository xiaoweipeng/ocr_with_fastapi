import os
import time
import warnings
from typing import Optional, List

import fitz
import numpy as np
import requests
from PIL import Image
from fastapi import APIRouter, Body, Request
from loguru import logger
from paddleocr import PaddleOCR
from paddleocr.tools.infer.utility import base64_to_cv2
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=DeprecationWarning)


class OCRsystem():
    def __init__(self):
        project_path = os.path.abspath(__file__).split("router")[0]
        self.model = PaddleOCR(det_model_dir=os.path.join(project_path, "inference/ch_ppocr_server_v2.0_det_infer"),
                               rec_model_dir=os.path.join(project_path, "inference/ch_ppocr_server_v2.0_rec_infer"),
                               rec_char_dict_path=os.path.join(project_path, "inference/ppocr_keys_v1.txt"),
                               cls_model_dir=os.path.join(project_path, "inference/ch_ppocr_mobile_v2.0_cls_infer"),
                               use_angle_cls=True,
                               enable_mkldnn=True,
                               show_log=False)
        # self.model=PaddleOCR(use_angle_cls=True, lang='ch')

    def ocr_paths(self, paths: List):
        if len(paths) == 0:
            return {'code': 200, 'message': "失败", 'results': "图片路径为空"}
        st = time.time()
        results = []
        for img_path_url in paths:
            try:
                image = np.asarray(Image.open(requests.get(img_path_url, stream=True).raw).convert('RGB'))
                starttime = time.time()
                result = self.model.ocr(image)
                elapse = time.time() - starttime
                result2 = {'msg': ''.join([i[1][0] for i in result]),
                           'path': img_path_url,
                           'elapse': elapse,
                           'hash': str(hash(image.data.tobytes()))
                           }
                results.append(result2)
                logger.info(result2)
            except Exception as e:
                result2 = {'msg': '图片不存在',
                           'path': img_path_url,
                           'elapse': 0}
                results.append(result2)
                temp = result2.copy()
                temp['error'] = str(e)
                logger.error(temp)
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': time.time() - st}

    def ocr_base64(self, images: List):
        if len(images) == 0:
            return {'code': 200, 'message': "失败", 'results': "图片列表为空"}
        st = time.time()
        results = []
        for img in images:
            try:
                image = base64_to_cv2(img)
                starttime = time.time()
                result = self.model.ocr(image)
                elapse = time.time() - starttime
                result2 = {'msg': ''.join([i[1][0] for i in result]),
                           'elapse': elapse,
                           'hash': str(hash(image.data.tobytes()))
                           }
                results.append(result2)
                logger.info(result2)
            except Exception as e:
                result2 = {'msg': '图片不存在',
                           'elapse': 0}
                results.append(result2)
                temp = result2.copy()
                temp['error'] = str(e)
                temp['img'] = img
                logger.error(temp)
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': time.time() - st}

    def ocr_pdf(self, pdf_path: List[str]):
        results = []
        st = time.time()

        for path in pdf_path:
            starttime = time.time()
            if path.startswith('http'):
                try:
                    resp = requests.get(path)
                    doc = fitz.Document(stream=resp.content, filetype='pdf')
                except Exception as e:
                    doc = {'msg': '文件下载失败', 'path': path}
            else:
                if os.path.isfile(path):
                    try:
                        doc = fitz.open(path)
                    except Exception as e:
                        doc = {'msg': '文件路径错误,文件不存在', 'path': path}
                else:
                    doc = {'msg': '文件路径错误,文件不存在', 'path': path}

            if isinstance(doc, dict):
                results.append(doc)
                logger.error(doc)
                continue
            result_pages = []
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                image = np.frombuffer(buffer=pix.samples_mv, dtype=np.uint8).reshape((pix.height, pix.width, -1))
                result = self.model.ocr(image)
                result_pages.append(result)

            result2 = {'msg': [''.join([i[1][0] for i in res]) for res in result_pages],
                       'path': path,
                       'elapse': time.time() - starttime,
                       'hash': str(hash(doc))
                       }
            results.append(result2)
            logger.info(result2)
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': time.time() - st}


class Data(BaseModel):
    paths: Optional[List] = None
    images: Optional[List] = None


class Func(BaseModel):
    type: Optional[str] = None


router = APIRouter()


@router.post("/predict/ocr", description="图片识别")
async def predict_ocr(req: Request,
                      data: Data = Body(None, description="传入 路径(paths) 或 base64图片(images)"),
                      type: str = Body(None),
                      ):
    logger.info("ip: "+req.client.host+' port: '+str(req.client.port)+' '+str(data) + ' type:' + type)
    ocr = OCRsystem()
    if type == 'image' or type is None:
        return ocr.ocr_paths(data.paths)
    if type == 'base64':
        return ocr.ocr_base64(data.images)
    if type == 'pdf':
        return ocr.ocr_pdf(data.paths)
        # raise HTTPException(status_code=404, detail={'code': 404, 'message': "POST数据缺失"})
    return {'code': 404, 'message': "data数据缺失"}
