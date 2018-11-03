import os

os.system("pip2 install --user -r requirements.txt")
os.system("(cd ./darknet && make clean && make)")

import urllib

print "Downloading last file"
urllib.urlretrieve ("https://pjreddie.com/media/files/yolov3.weights", "./cfg/yolo.weights")
