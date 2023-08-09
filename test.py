from ultralytics import YOLO
import numpy as np
import os
import cv2
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

model = YOLO("modelos/mejor/train/weights/best.pt")


img = cv2.imread("static/image_75.jpg")
results = model.predict(img, verbose=False)
file_path = os.path.join('predicted', f'image_75.jpg')
output = results[0].boxes[0].data

x1, y1, x2, y2 = map(int, output[0][:4].tolist())
score = float(output[0][4])
label = int(output[0][5])
category_id = label + 1
name = results[0].names[label]


# Dibujamos el bounding box en la imagen
cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2) # Bounding box con línea verde y grosor 2

# Si deseas añadir el score y el label en la esquina superior izquierda del bounding box
cv2.putText(img, f'{name}:{score:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

cv2.imwrite(file_path,img)

