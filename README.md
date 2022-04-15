# ocr_with_fastapi
基于fastapi的paddleocr服务

支持传入图片和pdf,图片可以传入url或者base64编码,pdf可以传入url

http://ip/ 会重定向至 http://ip/docs
http://ip/predict/ocr 只接收POST请求,格式如下:
```json{
  "data": {
    "paths": [
    "http://127.0.0.1:8000/1.jpg",
    "http://127.0.0.1:8000/11.jpg",
  ],
    "images": [
      "base64code",
      "base64code"
    ]
  },
  "type": "image/pdf"
}
```

如果type为image,优先读取paths内数据,若为空,才读取images内数据.

如果type为pdf,只处理paths内数据,会将pdf下载到本地后转为图片再进行ocr

使用paddleocr对图片进行处理,使用了ppocr_server和ppocr_mobile的推理库以及ppocr的字典,返回一张图所有字符串连接起来的结果,没有断句

因为项目使用了pymupdf,会被AGPL污染,如果介意,可以使用其他pdf处理库
