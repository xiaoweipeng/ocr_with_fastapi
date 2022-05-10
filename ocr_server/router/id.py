import os
import re
import string
import time
from typing import Optional, List

import numpy as np
import requests
from PIL import Image
from fastapi import APIRouter, Body, Request
from loguru import logger
from paddleocr import PaddleOCR
from paddleocr.tools.infer.utility import base64_to_cv2
from pydantic import BaseModel

router = APIRouter()


class IdCardStraight:
    """
    模拟阿里云身份证OCR返回结果，待改进。
    """

    def __init__(self, result):
        self.result = [
            i.replace(" ", "").translate(str.maketrans("", "", string.punctuation))
            for i in result
        ]
        self.out = {"Data": {"Result": {}}}
        self.res = self.out["Data"]["Result"]
        self.res["Name"] = ""
        self.res["IDNumber"] = ""
        self.res["Address"] = ""
        self.res["Gender"] = ""
        self.res["Nationality"] = ""
        self.res["Birth"] = ""
        self.res['isFront'] = True

    def is_front(self):
        for txt in self.result:
            if len(txt) > 1:
                if ("中华人民共和国" in txt or
                        "居民身份证" in txt or
                        "签发" in txt or
                        "机关" in txt or
                        "有效" in txt or
                        "期限" in txt
                ):
                    self.res['isFront'] = False
                    return False
        self.res['isFront'] = True
        return True

    def birth_no(self):
        """
        身份证号码
        """
        for i in range(len(self.result)):
            txt = self.result[i]
            # 身份证号码
            if "X" in txt or "x" in txt:
                res = re.findall("\d{17}[X|x]", txt)
                res[17] = 'X'
            else:
                res = re.findall("\d{18}", txt)

            if len(res) > 0:
                if len(res[0]) == 18:
                    self.res["IDNumber"] = res[0]
                    self.res["Gender"] = "男" if int(res[0][16]) % 2 else "女"
                    year = int(res[0][6:10])
                    month = int(res[0][10:12])
                    day = int(res[0][12:14])
                    #     简单判断年月日是否合法
                    if month >= 13 or month == 0 or day >= 32 or day == 0 or year < 1900 or year > time.localtime(
                            time.time()).tm_year:
                        self.out['error'] = '信息读取不全,重新上传照片'
                    coefficient = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
                    code = [int(i[0]) * int(i[1]) for i in zip(res[0][:17], coefficient)]
                    check_code = sum(code) % 11
                    if not ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2'][check_code] == res[0][17]:
                        self.out['error'] = '身份证号校验错误,重新上传照片'
                    self.result[i] = '-'
                    self.res["Birth"] = f"{year}-{month}-{day}"
                break

    def full_name(self):
        """
        身份证姓名,不限制名字长度(就一行)
        """
        for i in range(len(self.result)):
            txt = self.result[i]
            if ("姓名" in txt or "名" in txt) and len(txt) > 2:
                res = re.findall("名[\u4e00-\u9fa5]+", txt)
                if len(res) > 0:
                    self.res["Name"] = res[0].split("名")[-1]
                    self.result[i] = "-"  # 避免身份证姓名对地址造成干扰
                    break
        # 没有匹配的名字,猜名字,可能会有误差,'名'后面的字符串是名字
        if self.res["Name"] == "":
            for i in range(len(self.result)):
                txt = self.result[i]
                if len(txt) > 1:
                    if (
                            "性别" not in txt
                            and "姓名" not in txt
                            and "民族" not in txt
                            and "住址" not in txt
                            and "出生" not in txt
                            and "号码" not in txt
                            and "身份" not in txt
                    ) or '名' in self.result[i - 1]:
                        self.res["Name"] = self.result[i]
                        self.result[i] = '-'
                        break
                        # result = re.findall("[\u4e00-\u9fa5]", txt)
                        # if len(result) > 0:
                        #     self.res["Name"] = result[0]
                        #     break

    def national(self):
        # 性别女民族汉
        for i in range(len(self.result)):
            txt = self.result[i]
            res = re.findall(".*民族[\u4e00-\u9fa5]+", txt)

            if len(res) > 0:
                self.res["Nationality"] = res[0].split("族")[-1]
                self.result[i] = '-'
                break

    def address(self):
        """
        身份证地址
        """
        addString = []
        for i in range(len(self.result)):
            txt = self.result[i]
            # txt = txt.replace("号码", "")
            # if "公民" in txt:
            #     txt = "temp"
            # 身份证地址
            if (
                    "住址" in txt
                    or "址" in txt
                    or "省" in txt
                    or "市" in txt
                    or "县" in txt
                    or "街" in txt
                    or "乡" in txt
                    or "村" in txt
                    or "镇" in txt
                    or "区" in txt
                    or "城" in txt
                    or "组" in txt
                    or "号" in txt
                    or "幢" in txt
                    or "栋" in txt
            ):
                if "住址" in txt or "省" in txt or "址" in txt:
                    addString.insert(0, txt.split("址")[-1])
                else:
                    addString.append(txt)

                self.result[i] = "-"

        if len(addString) > 0:
            self.res["Address"] = "".join(addString)
        else:
            self.res["Address"] = ""

    def run(self):
        if self.is_front():
            self.birth_no()
            self.full_name()
            self.national()
            self.address()
            for key, value in self.res.items():
                if value == "":
                    self.out['error'] = '信息读取不全,重新上传照片'
        return self.out


class id_OCRsystem():
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

    def do_ocr(self, img):
        # 先找出身份证的文字,得到识别框位置
        boxs = self.model.ocr(img, det=True, cls=False, rec=False)

        # 分割身份证
        def imagecrop(img, box):
            xs = [x[1] for x in box]
            ys = [x[0] for x in box]
            cropimage = img[min(xs):max(xs), min(ys):max(ys)]
            return cropimage

        # 切割出所有字,一起用ocr识别
        cropimages = [imagecrop(img, np.int0(box)) for box in boxs]
        directions = self.model.ocr(cropimages, det=False, cls=True, rec=False)
        directions = [direction[0] for direction in directions]
        # 如果字中有倒置字,停止处理,直接返回错误
        logger.info(directions)
        if '180' in directions:
            temp = set(directions)
            if len(temp) != 1:
                return {'error': '身份证图片不规范'}
            else:
                # 180度旋转图片,先上下翻转再左右翻转
                img = img[::-1, ...][:, ::-1]
        # 没有倒置字,继续处理
        result = self.model.ocr(img, det=True, cls=False, rec=True)
        logger.info(f'图片{str(hash(img.data.tobytes()))}ocr结果{result}')
        txts = [line[1][0] for line in result]
        result = IdCardStraight(txts).run()
        logger.info(f'图片{str(hash(img.data.tobytes()))}身份证处理结果{result}')
        return result

    def ocr_paths(self, paths: List):
        if len(paths) == 0:
            return {'code': 200, 'message': "失败", 'results': "图片路径为空"}
        st = time.time()
        results = []
        for img_path_url in paths:
            try:
                image = np.asarray(Image.open(requests.get(img_path_url, stream=True, timeout=100).raw).convert('RGB'))
                starttime = time.time()
                result = self.do_ocr(image)
                elapse = time.time() - starttime
                if 'error' in result:
                    result2 = {'msg': result['error'],
                               'path': img_path_url,
                               'elapse': elapse,
                               'hash': str(hash(image.data.tobytes()))
                               }
                else:
                    result2 = {'msg': result,
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
        logger.info(results)
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
                result = self.do_ocr(image)
                elapse = time.time() - starttime
                if 'error' in result:
                    result2 = {'msg': result['error'],
                               'elapse': elapse,
                               'hash': str(hash(image.data.tobytes()))
                               }
                else:
                    result2 = {'msg': result,
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
        logger.info(results)
        return {'code': 200, 'message': "成功", 'results': results, 'elapse': time.time() - st}


class Data(BaseModel):
    paths: Optional[List] = None
    images: Optional[List] = None


@router.post("/predict/id", description="图片识别")
async def predict_id(req: Request,
                     data: Data = Body(None, description="传入 路径(paths) 或 base64图片(images)"),
                     type: str = Body(None),
                     ):
    logger.info("ip: " + req.client.host + ' port: ' + str(req.client.port) + ' ' + str(data) + ' type:' + type)
    ocr = id_OCRsystem()
    if data is not None:
        if type == 'image' or type is None:
            if data.paths is not None:
                if len(data.paths) > 0:
                    res = ocr.ocr_paths(data.paths)
                    logger.error(
                        "ip: " + req.client.host + ' port: ' + str(req.client.port) + ' ' + str(data) + ' type:' + str(
                            type) + "result:" + str(res))
                    return res

        if type == 'base64':
            if data.images is not None:
                if len(data.images) > 0:
                    res = ocr.ocr_base64(data.images)
                    logger.error(
                        "ip: " + req.client.host + ' port: ' + str(req.client.port) + ' ' + str(data) + ' type:' + str(
                            type) + "result:" + str(res))
                    return res
    res = {'code': 404, 'message': "data数据缺失", 'data': data, 'type': type}
    logger.error(
        "ip: " + req.client.host + ' port: ' + str(req.client.port) + ' ' + str(data) + ' type:' + str(
            type) + "result:" + str(res))
    return res