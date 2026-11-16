# FoxCamera
# watches the visitor with the camera (mediapipe finds their body)
# and sends 6 numbers to wekinator, many times a second:
#   1. across       where they are: -1 = left edge of the picture, 0 = middle, 1 = right edge
#   2. away         how far away they are, in metres (3 = nobody there)
#   3. leftArmOut   how far the left hand is out to the side
#   4. leftArmUp    how high the left hand is (-1.5 = hanging down)
#   5. rightArmOut  same for the right hand
#   6. rightArmUp
#
# how it all fits together:
# this script -> wekinator -> FoxHeadsBridge (processing) -> arduino
#
# to run it: open Terminal in this folder and type  python3 fox_camera.py
# press q to quit
# press c while standing 1 m from the camera to set up the distance.
# (do this BEFORE training wekinator. if you do it after, train wekinator again.)

import time
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from pythonosc import udp_client

smooth = 0.3  # smaller = smoother but slower
sure = 0.5    # how sure it has to be it can see a body part

# distance - stand 1 m from the camera, press c, then copy the 2 numbers it prints into here
shoulders1m = 350  # how wide your body looks at 1 m, in pixels
eyes1m = 75        # how far apart your eyes look at 1 m, in pixels

# camera - change the 0 to 1 if its the wrong camera (eg the iphone)
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("cant open the camera!")
    print("run this from the Terminal app, and allow Terminal in")
    print("System Settings > Privacy & Security > Camera")
    exit()

# body tracker. the file pose_landmarker_full.task has to be in the same folder as this
options = vision.PoseLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path="pose_landmarker_full.task"),
    running_mode=vision.RunningMode.VIDEO,
)
tracker = vision.PoseLandmarker.create_from_options(options)

# wekinator listens on 6448
wekinator = udp_client.SimpleUDPClient("127.0.0.1", 6448)

# the numbers we send
# they have to be written with a dot (3.0 not 3). wekinator only reads decimal numbers,
# a whole number like 3 arrives as 0.
across = 0.0
away = 3.0  # 3 m = nobody close
leftArmOut = 0.0
leftArmUp = 0.0
rightArmOut = 0.0
rightArmUp = 0.0

# how many frames we havent seen anyone for
lostFrames = 300  # start as if nobody has been there for ages

# body size and eye gap this frame (for pressing c)
shoulders = 0
eyes = 0


# move a number a little bit towards a new number. this smooths out the wobble.
def lerp(a, b, amount):
    return a + (b - a) * amount


# true if a body part is seen and inside the picture (not cut off at the edge)
def inPicture(point):
    return point.visibility > sure and 0.02 < point.x < 0.98 and 0.02 < point.y < 0.98


# this loop runs once for every picture from the camera
while True:
    # get a picture from the camera. if it didnt work, try again
    ok, frame = camera.read()
    if not ok:
        continue

    # mediapipe wants rgb, the camera gives bgr
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    picture = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = tracker.detect_for_video(picture, int(time.time() * 1000))

    if len(result.pose_landmarks) > 0:
        lostFrames = 0
        body = result.pose_landmarks[0]
        # the numbers mediapipe uses for each body part
        nose = body[0]
        leftShoulder = body[11]
        rightShoulder = body[12]
        leftWrist = body[15]
        rightWrist = body[16]
        leftEye = body[2]
        rightEye = body[5]

        # mediapipe gives 0 to 1, so times by the picture size to get pixels
        w = frame.shape[1]
        h = frame.shape[0]
        leftHip = body[23]
        rightHip = body[24]

        # how big the person looks = how close they are
        # shoulder width shrinks when you turn sideways, so also measure
        # shoulders to hips (that stays the same when you turn) and use the bigger one
        shoulders = ((leftShoulder.x - rightShoulder.x) ** 2 + (leftShoulder.y - rightShoulder.y) ** 2) ** 0.5 * w
        if inPicture(leftHip) and inPicture(rightHip):
            torso = ((leftShoulder.y + rightShoulder.y) / 2 - (leftHip.y + rightHip.y) / 2) * h
            torso = abs(torso) * 0.7  # torso is longer than shoulders are wide
            if torso > shoulders:
                shoulders = torso
        if shoulders < 10:
            shoulders = 10  # stops it dividing by 0

        # gap between the eyes. you can still see it when you're too close to see your shoulders
        eyes = ((leftEye.x - rightEye.x) ** 2 + (leftEye.y - rightEye.y) ** 2) ** 0.5 * w
        if eyes < 2:
            eyes = 2

        # twice as close = looks twice as big
        # use the shoulders if both are in the picture (more accurate), if not use the eyes
        if inPicture(leftShoulder) and inPicture(rightShoulder):
            metres = shoulders1m / shoulders
            measuring = "using shoulders"
        else:
            metres = eyes1m / eyes
            measuring = "using eyes"

        # across: -1 = left edge of the picture, 0 = middle, 1 = right edge
        across = lerp(across, (nose.x - 0.5) * 2, smooth)
        away = lerp(away, metres, smooth)

        # left hand
        if leftWrist.visibility > sure:
            leftArmOut = lerp(leftArmOut, (leftWrist.x - leftShoulder.x) * w / shoulders, smooth)
            leftArmUp = lerp(leftArmUp, (leftShoulder.y - leftWrist.y) * h / shoulders, smooth)
            cv2.circle(frame, (int(leftWrist.x * w), int(leftWrist.y * h)), 8, (0, 255, 0), -1)
        else:
            # cant see it so pretend its down
            leftArmOut = lerp(leftArmOut, 0, smooth)
            leftArmUp = lerp(leftArmUp, -1.5, smooth)

        # right hand
        if rightWrist.visibility > sure:
            rightArmOut = lerp(rightArmOut, (rightWrist.x - rightShoulder.x) * w / shoulders, smooth)
            rightArmUp = lerp(rightArmUp, (rightShoulder.y - rightWrist.y) * h / shoulders, smooth)
            cv2.circle(frame, (int(rightWrist.x * w), int(rightWrist.y * h)), 8, (0, 255, 0), -1)
        else:
            rightArmOut = lerp(rightArmOut, 0, smooth)
            rightArmUp = lerp(rightArmUp, -1.5, smooth)

        # say what it's using to measure the distance
        cv2.putText(frame, measuring, (10, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # green dots on the nose, eyes and shoulders
        for point in [nose, leftEye, rightEye, leftShoulder, rightShoulder]:
            cv2.circle(frame, (int(point.x * w), int(point.y * h)), 8, (0, 255, 0), -1)
    else:
        lostFrames = lostFrames + 1

        # if they were close when we lost them, they've probably come too close
        # for the camera to see them. keep the old numbers so the fox stays hidden.
        # (300 frames = about 10 seconds)
        if away < 0.7 and lostFrames < 300:
            cv2.putText(frame, "too close!", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            # nobody there
            across = 0.0
            away = 3.0  # 3 m = nobody close
            leftArmOut = 0.0
            leftArmUp = -1.5
            rightArmOut = 0.0
            rightArmUp = -1.5

    # print numbers on screen for testing
    cv2.putText(frame, "across %.2f  away %.2f m" % (across, away), (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, "left arm out %.2f  up %.2f" % (leftArmOut, leftArmUp), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, "right arm out %.2f  up %.2f" % (rightArmOut, rightArmUp), (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.imshow("FoxCamera", frame)

    # wekinator was only trained from about 1.1 m away.
    # so anything nearer than 1 m is sent as 1 m. that still counts as close.
    sendAway = away
    if sendAway < 1.0:
        sendAway = 1.0

    # send to wekinator
    wekinator.send_message("/wek/inputs", [across, sendAway, leftArmOut, leftArmUp, rightArmOut, rightArmUp])

    key = cv2.waitKey(1)
    if key == ord("q"):
        break

    # press c while standing 1 m away to set up the distance
    if key == ord("c") and lostFrames == 0:
        shoulders1m = shoulders
        eyes1m = eyes
        print("copy these into the top of the code:")
        print("shoulders1m = %d" % shoulders1m)
        print("eyes1m = %d" % eyes1m)

camera.release()
cv2.destroyAllWindows()
