from paddleocr import PaddleOCR

model = PaddleOCR(det_model_dir='./inference/ch_ppocr_server_v2.0_det_infer',
                          rec_model_dir='./inference/ch_ppocr_server_v2.0_rec_infer',
                          rec_char_dict_path='./inference/ppocr_keys_v1.txt',
                          cls_model_dir='./inference/ch_ppocr_mobile_v2.0_cls_infer',
                          use_angle_cls=True
                  )
