import os

os.system("pip install --user -r requirements.txt")

import urllib

print "Downloading last file"
urllib.urlretrieve ("https://pjreddie.com/media/files/yolov3.weights", "./cfg/yolo.weights")
