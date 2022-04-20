import os
import time
from typing import Optional,List
import fitz
import requests
from PIL import Image
import numpy as np
from fastapi import APIRouter, Body
from paddleocr.tools.infer.utility import base64_to_cv2
from pydantic import BaseModel
from loguru import logger
from paddleocr import PaddleOCR
import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)

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

    def read_images_path(self, paths):
        images = []
        for img_path_url in paths:
            try:
                image = np.asarray(Image.open(requests.get(img_path_url,stream=True).raw))
            except Exception as e:
                image = None
            images.append(image)
        return images

    def do_ocr(self, images):
        results = []
        starttime = time.time()
        for image in images:
            if image is None:
                results.append('图片不存在')
                continue
            result = self.model.ocr(image, cls=True)
            results.append(''.join([i[1][0] for i in result]))
        elapse = time.time() - starttime
        return results, elapse

    def ocr_paths(self, paths: List):
        if len(paths) == 0:
            return {'code': 200, 'message': "失败", 'results': "图片路径为空"}
        images = self.read_images_path(paths)
        results, elapse = self.do_ocr(images)
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': elapse}

    def ocr_images(self, images: List):
        if len(images) == 0:
            return {'code': 200, 'message': "失败", 'results': "图片列表为空"}
        images = [base64_to_cv2(image) for image in images]
        return self.do_ocr(images)
        # return {'code': 200, 'message': "成功", 'results': results, 'elapse': elapse}

    def ocr_pdf(self, pdf_path: List[str]):
        results = []
        starttime = time.time()

        for path in pdf_path:
            if path.startswith('http'):
                try:
                    resp = requests.get(path)
                    doc = fitz.Document(stream=resp.content, filetype='pdf')
                except Exception as e:
                    doc= {'path': path, 'msg': '文件下载失败'}
            else:
                if os.path.isfile(path):
                    try:
                        doc = fitz.open(path)
                    except Exception as e:
                        doc = {'path': path, 'msg': '文件路径错误,文件不存在'}
                else:
                    doc = {'path': path, 'msg': '文件路径错误,文件不存在'}

            if isinstance(doc, dict):
                results.append(doc)
                continue

            pixs = [page.get_pixmap(dpi=300) for page in doc]
            images = [np.frombuffer(buffer=pix.samples_mv, dtype=np.uint8).
                          reshape((pix.height, pix.width, 3))
                      for pix in pixs]
            result = []
            for image in images:
                res = self.model.ocr(image)
                result.append(res)
            # result = [self.model.ocr(image, cls=True) for image in images]
            results.append([''.join([i[1][0] for i in res]) for res in result])

        elapse = time.time() - starttime
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': elapse}



class Data(BaseModel):
    paths: Optional[List] = None
    images: Optional[List] = None


class Func(BaseModel):
    type: Optional[str] = None


router = APIRouter()


@router.post("/predict/ocr", description="图片识别")
async def predict_ocr(data: Data = Body(None, description="传入 路径(paths) 或 base64图片(images)"),
                      type: str = Body(None)
                      ):
    # print(data.paths)
    # print(data.images)
    # print(type)
    print(data)
    print(type)
    ocr = OCRsystem()
    if type == 'image' or type is None:
        if data.paths:
            return ocr.ocr_paths(data.paths)
        elif data.images:
            return ocr.ocr_images(data.images)
    if type == 'pdf':
        return ocr.ocr_pdf(data.paths)
        # raise HTTPException(status_code=404, detail={'code': 404, 'message': "POST数据缺失"})
    return {'code': 404, 'message': "data数据缺失"}
