import cv2
import numpy as np
import math

#HSV constants
# --- BLUE CONSTANTS ---
blueLow = np.array([100, 60, 60])
blueHigh = np.array([140, 255, 255])

# --- RED CONSTANTS ---
redTopLow = np.array([170, 70, 50])
redTopHigh = np.array([180, 255, 255])

redBottomLow = np.array([0, 70, 50])
redBottomHigh = np.array([10, 255, 255])

# --- YELLOW CONSTANTS ---
yellowLow = np.array([20, 80, 80])
yellowHigh = np.array([35, 255, 255])

# Algorithm details:
# 1.

img = cv2.imread("imgs/adam1.jpg")

dim = (640, 480)
img = cv2.resize(img, dim)

# Distortion stuff is handled by logitech here
# Automatically undistorted, so there's no need for us to do that

# Perspective transform
# bounds = [(140, 48), (500, 46), (710, 360),  (0, 350)]
# bounds = [(200, 48), (500, 46), (630, 360),  (60, 330)]
# adam bounds
bounds = [(100, 130), (500, 80), (540, 300),  (110, 340)]

matrix = cv2.getPerspectiveTransform(np.float32(bounds), np.float32([[0, 0], [dim[0], 0], dim, [0, dim[1]]]))
transformed_image = cv2.warpPerspective(img, matrix, dim)


#Blur -> For smoothing, helps with canny edge detection. Do it 15 times and it makes it worse though
for i in range(5):
  transformed_image = cv2.GaussianBlur(transformed_image,(5,5),0)

# Can erode here if we want, makes contours worse so we don't do it
# element = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2), (-1, -1))
# transformed_image = cv2.morphologyEx(transformed_image, cv2.MORPH_OPEN, element)

#Hough is hough lines on the transformed image, raw_hough is empty mask for hough
hough = transformed_image.copy()
raw_hough = np.zeros(transformed_image.shape[:2], np.uint8)

hsv_image = cv2.cvtColor(transformed_image, cv2.COLOR_BGR2HSV)
# Threshold for HSV
red1_threshold = cv2.inRange(hsv_image, redTopLow, redTopHigh)
red2_threshold = cv2.inRange(hsv_image, redBottomLow, redBottomHigh)
blue_threshold = cv2.inRange(hsv_image, blueLow, blueHigh)
yellow_threshold = cv2.inRange(hsv_image, yellowLow, yellowHigh)

CONTOUR_THRESH_LOW = 500
CONTOUR_THRESH_HIGH = 10000

# Find contours in masks
r1c, _ = cv2.findContours(red1_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
r2c, _ = cv2.findContours(red2_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
bc, _ = cv2.findContours(blue_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
yc, _ = cv2.findContours(yellow_threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

contours = r1c + r2c + bc + yc

# Build mask of zeros (Bitwise AND is matrix multiplication, so anything 0 stays 0)
mask = np.zeros(transformed_image.shape[:2], np.uint8)
cv2.drawContours(mask, contours, -1, 255, thickness=cv2.FILLED)

# Erode the contours because of noise
element = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10), (-1, -1))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, element)

#Find Edges
edges = cv2.Canny(transformed_image, 50, 70)

# # Use the HSV mask to clarify canny
# # This is not working right now
# cv2.bitwise_and(edges, mask)

cv2.imshow("contours/mask", mask)
cv2.imshow("masked edges", edges)
cv2.imshow("transformed", transformed_image)

#Build hough lines
pixels_for_line = 10
linesP = cv2.HoughLinesP(edges, 1, 1 * np.pi/180, pixels_for_line, None, 10, 15)

# Draw the lines
if linesP is not None:
    for i in range(0, len(linesP)):
        l = linesP[i][0]
        cv2.line(hough, (l[0], l[1]), (l[2], l[3]), (0,0,255), 3, cv2.LINE_AA)
        cv2.line(raw_hough, (l[0], l[1]), (l[2], l[3]), 255, 10, cv2.LINE_AA)  

# ALSO NOT WORKIGN RN WTF
# cv2.bitwise_and(raw_hough, mask)

hough_contours, _ = cv2.findContours( 
    raw_hough, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 

# SHAPE DETECTION

coords = []

for contour in hough_contours:
  # Skip first thing cuz it just works like that
  if i == 0: 
    i = 1
    continue

  # cv2.approxPloyDP() function to approximate the shape 
  approx = cv2.approxPolyDP( 
      contour, 0.01 * cv2.arcLength(contour, True), True) 
    
  size = cv2.contourArea(contour)
  if size < 40:
     continue

  # finding center point of shape 
  M = cv2.moments(contour) 
  if M['m00'] != 0.0: 
      x = int(M['m10']/M['m00']) 
      y = int(M['m01']/M['m00']) 

  if (mask[y][x] == 0):
    continue
  
  # shape detection
  # if len(approx) == 4: 
  #     cv2.putText(raw_hough, 'Quadrilateral', (x, y), 
  #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) 

  # elif len(approx) == 5: 
  #     cv2.putText(raw_hough, 'Pentagon', (x, y), 
  #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) 

  # elif len(approx) == 6: 
  #     cv2.putText(raw_hough, 'Hexagon', (x, y), 
  #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) 

  # else: 
  #     cv2.putText(raw_hough, 'circle', (x, y), 
  #                 cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2) 
      
  cv2.circle(raw_hough, (x, y), 3, (255, 0, 0), 1)
  coords.append([x, y])

for bound in bounds:
  cv2.circle(img, bound, 2, (255, 0, 0), 2)

cv2.polylines(img, [np.int32(bounds)], True, (255, 0, 0), 5)

cv2.imshow("hough", hough)
cv2.imshow("raw hough", raw_hough)

cv2.imshow("raw", img)
cv2.waitKey(0)