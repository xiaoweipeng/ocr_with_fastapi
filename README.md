# ocr_with_fastapi
基于fastapi的paddleocr服务

启动命令:
``` shell
uvicorn ocr_server.main:app --host 0.0.0.0 --port 8002
```
使用gunicorn管理uvicorn时要注意gunicorn有很多默认的参数，比如--workers=4,--timeout=60,--log-level=info等等, 此项目需要设置timeout,如果运算太慢,gunicorn就自动kill进程了.
```shell
gunicorn -k uvicorn.workers.UvicornWorker ocr_server.main:app --bind 0.0.0.0:8002 --timeout 3000
```

支持传入图片和pdf,图片可以传入url或者base64编码,pdf可以传入url

http://ip/ 会重定向至 http://ip/docs

http://ip/predict/ocr 只接收POST请求,格式如下:
```json{
  "data": {
    "paths": [
    "http://127.0.0.1:8000/1.jpg",
    "http://127.0.0.1:8000/11.jpg"
    ],
    "images": [
      "base64code",
      "base64code"
      ]
  },
  "type": "image/pdf/base64"
}
```
---
<h5>入参</h5>
json格式

如果type为image,读取paths内数据,

如果type为base64,读取images内数据.

如果type为pdf,只处理paths内数据,会将pdf读取到内存后转为图片再进行ocr

---
<h5>返回结果</h5>
json格式

如果是图片:结果在"results"中,一个图片对应一个{},ocr结果在"msg"中,"elapse"为处理时间,"hash"为对图片的hash数据用于校验确认

如果是pdf:结果在"results"中,一个pdf 对应一个{},ocr结果在"msg"中,每张图一个字符串,"elapse"为处理时间,"hash"为对pdf的hash数据用于校验确认

---
<h5>一些说明</h5>
因为图片转为ndarray会占用大量内存,使用for循环逐个推理,不使用列表推导式.因为paddleocr使用的cpu和mkldnn,每此预测会吃满CPU,此方法不进行异步(异步会互相抢占CPU,导致运算更慢),async只是防止paddle并发报错,结果是其他接口也会无反应,若想多线程,可以去掉async.

使用paddleocr对图片进行处理,使用了ppocr_server和ppocr_mobile的推理库以及ppocr的字典,返回一张图所有字符串连接起来的结果,没有断句

因为项目使用了pymupdf,会被AGPL污染,如果介意,可以使用其他pdf处理库
