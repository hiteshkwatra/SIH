import imutils
import cv2
import sys
import time
import playsound
from threading import Thread
import pyximport; 
import ddestimator
import pandas as pd
import tkinter as tk
import pyttsx3
import requests
from tkinter import messagebox


st=int(round(time.time()))
er=0
aft=0
talking_theshold=0
talking_frames_threshold=10
engine = pyttsx3.init()
alarm_frames_threshold=16
last_alert=int(round(time.time()))
last_alcohol_alert=0
alcohol_bool= False
url = "https://www.fast2sms.com/dev/bulk"
payload = "sender_id=FSTSMS&message=Akshay seems to be DROWSY&language=english&route=p&numbers=8826268477"
headers = {'authorization': "Nex37zT5xHjqvgUGIwgOqqTXqTYCcdOchCZUGGA69uaSujwPCyBhu86M963s",
'Content-Type': "application/x-www-form-urlencoded",
'Cache-Control': "no-cache",}

def textsms():
	global url,payload,headers
	respo = requests.request("POST", url, data=payload, headers=headers)
	print(respo.text)




def fun():
	global engine
	engine.say('Alert you need to halt and get fresh before driving any further')
	engine.runAndWait()
    #playsound.playsound(r"C:\Users\hites\Downloads\Tires Squealing-SoundBible.com-1814115127.wav")

class demo1:

	FRAME_WIDTH = 750
	WINDOW_TITLE = "Demo #1: live distraction and drowsiness estimation"

	PROCESS_INTERVAL = 50
	

	K_ESC = 27
	K_QUIT = ord('q')
	K_POINTS = ord('p')
	K_BOUNDING = ord('b')
	K_GAZE = ord('g')
	K_EYES = ord('e')
	K_MOUTH = ord('m')
	K_DD = ord('d')
	K_NONE = ord('n')
	K_REFRESH = ord('r')
	K_SAVE_LOG = ord('l')
	K_HELP = ord('h')

	LOG_PATH = './kss_%ts.csv'

	CALIBRATE_CAMERA_ANGLES = True

	def __init__(self):
		self.rootwin = tk.Tk()
		self.rootwin.withdraw()
		cv2.namedWindow(demo1.WINDOW_TITLE)
		self.show_points = False
		self.show_bounding = False
		self.show_gaze = False
		self.show_ear = False
		self.show_mar = False
		self.show_dd = True
		self.ddestimator = ddestimator.ddestimator()
		self.has_calibrated = False

	def run(self):
		global er
		self.cap=cv2.VideoCapture(0)
		#self.cap = cv2.VideoCapture(r"C:\Users\hites\Downloads\ezgif.com-rotate.mp4")
		if not self.cap.isOpened():
			print("Unable to connect to camera.")
			return
		while self.cap.isOpened():
			self.key_strokes_handler()
			ret, frame = self.cap.read()
			#frame= cv2.flip(frame,-1)

			if ret:
				frame = imutils.resize(frame, width=demo1.FRAME_WIDTH)
				frame = self.process_frame(frame,er/5)
				print('ear', er/5)
				cv2.imshow(demo1.WINDOW_TITLE, frame)
				cv2.moveWindow(demo1.WINDOW_TITLE, 0, 0)

	def process_frame(self, frame=None,eyethresh=0):
		global st, er

		#Detect faces in frame
		faces_loc = self.ddestimator.detect_faces(frame, None, True)

		cv2.putText(frame, "TEDDY HACKERS", (20,25),
						cv2.FONT_HERSHEY_TRIPLEX, 0.9, (36,36,240), thickness=2)


		#If there's more than one face...
		if len(faces_loc) > 0:

			#Only interested in first face found (for his demo)
			face_loc = faces_loc[0]

			#Predict coordinates of 68 points of this face using ML trained model
			points = self.ddestimator.pred_points_on_face(frame, face_loc)

			#All immediate estimations based on points locations
			euler, rotation, translation = self.ddestimator.est_head_dir(points)
		
		
			if demo1.CALIBRATE_CAMERA_ANGLES and not self.ddestimator.has_calibrated:
				has_calibration, _, meds = self.ddestimator.get_med_eulers()
				if has_calibration:
					self.ddestimator.calibrate_camera_angles(meds)
			_, _, gaze_D = self.ddestimator.est_gaze_dir(points)
			ear_B, ear_R, ear_L = self.ddestimator.est_eye_openness(points)

			if abs(st-int(round(time.time()))) <5:
				er+=ear_B
				return frame


			mar = self.ddestimator.est_mouth_openess(points)

			#All timescale estimations based on points locations
			head_distraction, _, _ = self.ddestimator.est_head_dir_over_time()
			if not head_distraction:
				gaze_distraction, _, _ = self.ddestimator.est_gaze_dir_over_time()
			else:
				gaze_distraction = False
			eye_drowsiness, _, _, eye_closedness = self.ddestimator.get_eye_closedness_over_time(ear_threshold=eyethresh)
			did_yawn, _, _, _ = self.ddestimator.get_mouth_openess_over_time()
#########################################
##########################################
			global alarm_frames_threshold, aft,last_alert,talking_frames_threshold, talking_theshold

			if mar>0.17 and mar <eyethresh:
				talking_theshold+=1
			else:
				talking_theshold=0

			#if talking_theshold>talking_frames_threshold:
				#cv2.putText(frame, "Talking", (frame.shape[1]//2,frame.shape[0]//2 ),
								#cv2.FONT_HERSHEY_COMPLEX, 0.8, (8,8,183), thickness=2)




			if (eye_drowsiness and eye_closedness) or did_yawn:
				aft+=2
			if head_distraction or gaze_distraction:
				aft+=1
				
	
			t = Thread(target=fun)
			if aft> alarm_frames_threshold:
				if abs(last_alert- int(round(time.time()))) >7  :

					
					
					t.deamon=True
					t.start()
					t2= Thread(target=textsms)
					t2.deamon=True
					#t2.start()
					last_alert=int(round(time.time()))
				aft=0



			kss = self.ddestimator.calc_kss()
			if kss is not None:
				print("\t%.2f" % (kss*10))

			#Show results on frame
			if self.show_points:
				frame = self.ddestimator.draw_points_on_face(frame, points, (0, 0, 255))

			if self.show_bounding:
				bc_2d_coords = self.ddestimator.proj_head_bounding_cube_coords(rotation, translation)
				frame = self.ddestimator.draw_bounding_cube(frame, bc_2d_coords, (250, 149, 104), euler)

			if self.show_gaze:
				gl_2d_coords = self.ddestimator.proj_gaze_line_coords(rotation, translation, gaze_D)
				self.ddestimator.draw_gaze_line(frame, gl_2d_coords, (0, 70, 150), gaze_D)

			if self.show_ear:
				frame = self.ddestimator.draw_eye_lines(frame, points, ear_R, ear_L)

			if self.show_mar:
				frame = self.ddestimator.draw_mouth(frame, points, mar)


			if self.show_dd:
				h = frame.shape[0]
				if head_distraction:
					print()

				
				elif self.show_gaze and gaze_distraction:
					cv2.putText(frame, "Distration due to Gaze", (frame.shape[1]//2, h - 60),
								cv2.FONT_HERSHEY_COMPLEX, 0.8, (8,8,183), thickness=2)
				if did_yawn:
					cv2.putText(frame, "Yawn", (frame.shape[1]//2, h - 40),
								cv2.FONT_HERSHEY_COMPLEX, 0.8, (8,8,183), thickness=2)

				if eye_closedness:
					cv2.putText(frame, "DROWSY ", (frame.shape[1]//2, h - 20),
								cv2.FONT_HERSHEY_COMPLEX, 0.8, (8,8,183), thickness=2)
				elif self.show_ear and eye_drowsiness:
					cv2.putText(frame, "DROWSY", (frame.shape[1]//2, h - 20),
								cv2.FONT_HERSHEY_COMPLEX, 0.8, (8,8,183), thickness=2)


		return frame

	def key_strokes_handler(self):
		pressed_key = cv2.waitKey(1) & 0xFF

		if pressed_key == demo1.K_ESC or pressed_key == demo1.K_QUIT:
			print('-> QUIT')
			self.cap.release()
			cv2.destroyAllWindows()
			sys.exit(0)

		elif pressed_key == demo1.K_POINTS:
			print('-> SHOW FACIAL LANDMARKS')
			self.show_points = True
			return None

		elif pressed_key == demo1.K_BOUNDING:
			print('-> SHOW BOUNDING CUBE FOR HEAD DIRECTION ESTIMATION')
			self.show_bounding = True
			return None

		elif pressed_key == demo1.K_GAZE:
			print('-> SHOW LINES FOR GAZE DIRECTION ESTIMATION')
			self.show_gaze = True
			return None

		elif pressed_key == demo1.K_EYES:
			print('-> SHOW EYE OPENNESS ESTIMATION')
			self.show_ear = True
			return None

		elif pressed_key == demo1.K_MOUTH:
			print('-> SHOW MOUTH OPENNESS ESTIMATION')
			self.show_mar = True
			return None

		elif pressed_key == demo1.K_DD:
			print('-> SHOW DROWSINESS & DISTRACTION ESTIMATIONS')
			self.show_dd = True
			return None

		elif pressed_key == demo1.K_NONE:
			print('-> SHOW NO ESTIMATIONS')
			self.show_bounding = False
			self.show_gaze = False
			self.show_ear = False
			self.show_mar = False
			self.show_dd = False
			self.show_points = False
			return None

		elif pressed_key == demo1.K_REFRESH:
			print('-> RESET SHOW TO DEFAULT')
			self.show_bounding = False
			self.show_gaze = False
			self.show_ear = False
			self.show_mar = False
			self.show_dd = True
			self.show_points = False
			return None

		elif pressed_key == demo1.K_SAVE_LOG:
			print('-> SAVE LOG FILE WITH KSS ESTIMATIONS')
			kss_log = self.ddestimator.fetch_log('kss')
			ts = int(round(time.time() * 1000))
			path = (demo1.LOG_PATH).replace('%ts', str(ts))
			print("\t"+path)
			kss_log.to_csv(path)
			return None

		elif pressed_key == demo1.K_HELP:
			tk.messagebox.showinfo("Help",
			                       "'p': Show facial landmarks\r\n'b': Show bounding cube\r\n'g': Show gaze line\r\n'e': Show eye info\r\n'm': Show mouth info\r\n'd': Show drowsiness & distraction info\r\n'n': Show nothing\r\n'r': Refresh/clear the frame of all info\r\n'l': Save log file\r\n'q': Quit the program")
			return None

		else:
			return None

if __name__ == '__main__':
	demo1 = demo1()
	demo1.run()