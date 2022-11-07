from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.models import Entries
from rest_framework import status
from api.serializers.entries import EntriesSerializer
import numpy as np
import cv2
from matplotlib import pyplot as plt
import imutils
import easyocr
import traceback
import base64
import io


@api_view(['GET'])
def getAllEntries(request):
    try:
        entries = Entries.objects.all()
        serializer = EntriesSerializer(entries, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def createEntry(request):
    try:
        data = request.data
        processImages = {}
        # image from request
        image = request.FILES['image']
        img = cv2.imdecode(np.fromstring(
            image.read(), np.uint8), cv2.IMREAD_UNCHANGED)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # saving image to process images dictionary
        pic_IObytes = io.BytesIO()
        plt.imsave(pic_IObytes, gray, format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        processImages['gray'] = pic_hash
        # Adding filter to image
        bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(bfilter, 30, 200)
        # saving image to process images dictionary
        pic_IObytes = io.BytesIO()
        plt.imsave(pic_IObytes, edged, format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        processImages['edged'] = pic_hash
        # Finding contours
        keypoints = cv2.findContours(
            edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        # Init location of number plate
        location = None
        # loop over contours
        for contour in contours:
            # approximate the contour
            approx = cv2.approxPolyDP(contour, 10, True)
            if len(approx) == 4:
                location = approx
                break
            else:
                approx = cv2.approxPolyDP(contour, 15, True)
                if len(approx) == 4:
                    location = approx
                    break
        
        mask = np.zeros(gray.shape, np.uint8)
        new_image = cv2.drawContours(mask, [location], 0, 255, -1)
        new_image = cv2.bitwise_and(img, img, mask=mask)
        pic_IObytes = io.BytesIO()
        plt.imsave(pic_IObytes, new_image, format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        processImages['new_image'] = pic_hash
        if location is None:
            return Response({'error': "No location found", "processImages": processImages}, status=status.HTTP_400_BAD_REQUEST)
        (x, y) = np.where(mask == 255)
        (x1, y1) = (np.min(x), np.min(y))
        (x2, y2) = (np.max(x), np.max(y))
        cropped_image = gray[x1:x2+1, y1:y2+1]

        pic_IObytes = io.BytesIO()
        plt.imsave(pic_IObytes, cropped_image, format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        processImages['cropped_image'] = pic_hash

        reader = easyocr.Reader(['en'])
        result = reader.readtext(cropped_image)

        if len(result) == 0:
            reader = easyocr.Reader(['en'], gpu=False)
            result = reader.readtext(cropped_image)
            if len(result) == 0:
                return Response({'error': "No text found", "processImages": processImages}, status=status.HTTP_400_BAD_REQUEST)

        text = result[0][-2]
        accuracy = result[0][-1]
        font = cv2.FONT_HERSHEY_SIMPLEX
        res = cv2.putText(img, text=text, org=(
            approx[0][0][0], approx[1][0][1]+60), fontFace=font, fontScale=1, color=(0, 255, 0), thickness=2, lineType=cv2.LINE_AA)
        res = cv2.rectangle(img, tuple(approx[0][0]), tuple(
            approx[2][0]), (0, 255, 0), 3)
        pic_IObytes = io.BytesIO()
        plt.imsave(pic_IObytes, res, format='png')
        pic_IObytes.seek(0)
        pic_hash = base64.b64encode(pic_IObytes.read())
        processImages['res'] = pic_hash

        # serializer = EntriesSerializer(data=data)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "success",
            "data": {
                "text": text,
                "images": processImages,
                "accuracy": accuracy
            }
        },
            status=status.HTTP_201_CREATED)
    except Exception as e:
        # print error with line number and full details
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
