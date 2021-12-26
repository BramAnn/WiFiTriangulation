import pyshark
import math
import os
import sys
import time
import numpy as np
import tkinter as tk
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF, renderPM
from PIL import Image, ImageTk
from kalman import SingleStateKalmanFilter
from rectangle import Rectangle

# BSSID Bonnie 30:ae:a4:4e:6b:e1
# BSSID Clyde 80:7d:3a:93:72:bd
# BSSID VOO-312606 04:a1:51:e0:da:47


REFERENCEDISTANCE = 1
BONNIE_COORDINATES = [1.3, 10.28]
CLYDE_COORDINATES = [8.96, 7.95]
VOO_COORDINATES = [4.7, 0.10]

SCALE_FACTOR = 37.79

ROOMS = []


class Locator:
	accespoints = ["30:ae:a4:4e:6b:e1", "80:7d:3a:93:72:bd", "04:a1:51:e0:da:47"]
	ogVOO = "04:a1:51:e0:da:47"
	bssidUBNT = "78:8a:20:da:64:9b"

	environment = 3.8
	# set True om pre en post kalman filter te loggen
	isLogCsvEnabled = False
	ap0 = []
	ap1 = []
	ap2 = []

	rooms = []

	cap = pyshark.LiveCapture(interface='wlan0', display_filter="wlan.fc.type_subtype == 0x8")

	def __init__(self, ap=None):
		if ap is not None:
			accespoints = ap
			print("You have chosen following basestations: ", end="")
			for a in accespoints:
				print(a, end=", ")
			print("\n", flush=True)

		self.init_rooms()

		self.init_kalman_filter()

		self.init_canvas()

	def init_rooms(self):
		# NAAM, N, TL, TR, BL, BR
		self.rooms.append(Rectangle("Woonkamer", 4.35, [0, 0], [8.46, 0], [0, 3.91], [8.46, 3.91]))
		self.rooms.append(Rectangle("Woonkamer", 4.35, [4.25, 3.91], [5.60, 3.91], [4.25, 4.66], [5.60, 4.66]))
		self.rooms.append(Rectangle("Woonkamer", 4.35, [5.60, 4.69], [8.46, 4.69], [5.60, 5.44], [8.46, 5.44]))
		self.rooms.append(Rectangle("Keuken", 4.35, [5.60, 5.44], [9.06, 5.44], [5.60, 10.44], [9.06, 10.44]))
		self.rooms.append(Rectangle("Hal", 4.35, [0.90, 3.91], [4.25, 3.91], [0.90, 7.33], [4.25, 7.33]))
		self.rooms.append(Rectangle("Gang", 4.35, [4.25, 4.66], [5.60, 4.66], [4.25, 8.91], [5.60, 8.91]))
		self.rooms.append(Rectangle("WC", 4.35, [4.025, 8.91], [5.60, 8.91], [4.25, 10.44], [5.60, 10.44]))
		self.rooms.append(Rectangle("Bureau", 4.35, [0.90, 7.33], [4.25, 7.33], [0.90, 10.44], [4.25, 10.44]))
		self.rooms.append(Rectangle("Bijkeuken", 4.35, [6.00, 10.44], [10.53, 10.44], [6.00, 12.29], [10.53, 12.29]))

		# UNCOMMENT OM FINGERPRINTING TEST SETUP TE GEBRUIKEN
		""" self.rooms.append(Rectangle("Woonkamer", 4.8, [0,0], [8.46,0], [0,3.91], [8.46,3.91]))
		self.rooms.append(Rectangle("Woonkamer", 4.8, [4.25,3.91], [5.60,3.91], [4.25,4.66], [5.60,4.66]))
		self.rooms.append(Rectangle("Woonkamer", 4.8, [5.60,4.69], [8.46,4.69], [5.60,5.44], [8.46,5.44]))
		self.rooms.append(Rectangle("Keuken", 5.3, [5.60,5.44], [9.06,5.44], [5.60,10.44], [9.06,10.44]))
		self.rooms.append(Rectangle("Hal", 5,[0.90,3.91], [4.25,3.91], [0.90,7.33], [4.25,7.33]))
		self.rooms.append(Rectangle("Gang", 4.9, [4.25,4.66], [5.60,4.66], [4.25,8.91], [5.60,8.91]))
		self.rooms.append(Rectangle("WC", 5.5, [4.025,8.91], [5.60,8.91], [4.25,10.44], [5.60,10.44]))
		self.rooms.append(Rectangle("Bureau", 4.2, [0.90,7.33], [4.25,7.33], [0.90,10.44], [4.25,10.44]))
		self.rooms.append(Rectangle("Bijkeuken", 5.5, [6.00,10.44], [10.53,10.44], [6.00,12.29], [10.53,12.29]))

		 """

	def init_kalman_filter(self):
		# Initialise the Kalman Filter
		A = 1  # No process innovation
		C = 1  # Measurement
		B = 0  # No control input
		Q = 0.005  # Process covariance
		R = 1  # Measurement covariance
		x = -70  # Initial estimate
		P = 1  # Initial covariance
		self.kalmanfilterAP0 = SingleStateKalmanFilter(A, B, C, x, P, Q, R)
		self.kalmanfilterAP1 = SingleStateKalmanFilter(A, B, C, x, P, Q, R)
		self.kalmanfilterAP2 = SingleStateKalmanFilter(A, B, C, x, P, Q, R)

	def init_canvas(self):
		# init canvas & image
		if os.environ.get('DISPLAY', '') == '':
			print('no display found. Using :0.0')
			os.environ.__setitem__('DISPLAY', ':0.0')

		self.window = tk.Tk()
		self.window.geometry("600x470")

		houseImage = Image.open(r'house_with_names.png')
		self.pimg = ImageTk.PhotoImage(houseImage)
		size = houseImage.size
		self.frame = tk.Canvas(self.window, width=size[0] + 2, height=size[1] + 2)

		currentRoomLabel = tk.Label(self.window, text='Current room:')
		currentRoomLabel.config(font=('helvetica', 14))
		currentRoomLabel.place(x=420, y=20)

		self.currentRoom = tk.StringVar()
		currentRoomLabel = tk.Label(self.window, textvariable=self.currentRoom)
		self.currentRoom.set("")
		currentRoomLabel.place(x=420, y=50)

		self.frame.pack(side=tk.LEFT)
		self.frame.create_image(2, 2, anchor='nw', image=self.pimg)
		self.window.update()

	def start(self):
		if self.isLogCsvEnabled:
			fAp0 = open("ap0Filtered.csv", "w")
			fAp1 = open("ap1Filtered.csv", "w")
			fAp2 = open("ap2Filtered.csv", "w")

		tempAp0, tempAp1, tempAp2 = -80, -80, -80

		for packet in self.cap.sniff_continuously():
			beaconCounter = 0
			bssid = packet["WLAN"].BSSId
			# dbm = packet["WLAN_RADIO"].signal_dbm
			# print(packet["WLAN_RADIO"].signal_dbm + " - " + packet["radiotap"].dbm_antsignal)
			dbm = packet["radiotap"].dbm_antsignal
			if (bssid == self.accespoints[0]):
				self.kalmanfilterAP0.step(0, int(dbm))
				tempAp0 = self.kalmanfilterAP0.current_state()

				# print("AP0: OG: " + str(dbm) + " | Kalman: " + str(self.kalmanfilterAP0.current_state()), flush=True)
				if self.isLogCsvEnabled:
					fAp0.write(str(dbm) + ", " + str(self.kalmanfilterAP0.current_state()) + " \n")

			elif (bssid == self.accespoints[1]):
				self.kalmanfilterAP1.step(0, int(dbm))
				tempAp1 = self.kalmanfilterAP1.current_state()

				# print("AP1: OG: " + str(dbm) + " | Kalman: " + str(self.kalmanfilterAP1.current_state()), flush=True)
				if self.isLogCsvEnabled:
					fAp1.write(str(dbm) + ", " + str(self.kalmanfilterAP1.current_state()) + " \n")

			elif (bssid == self.accespoints[2]):
				self.kalmanfilterAP2.step(0, int(dbm))
				tempAp2 = self.kalmanfilterAP2.current_state()

				# print("AP2: OG: " + str(dbm) + " | Kalman: " + str(self.kalmanfilterAP2.current_state()), flush=True)
				if self.isLogCsvEnabled:
					fAp2.write(str(dbm) + ", " + str(self.kalmanfilterAP2.current_state()) + " \n")

			self.start_triangulation(tempAp0, tempAp1, tempAp2)

	def start_triangulation(self, ap0, ap1, ap2):
		dAP0 = self.calculate_distance(ap0, 2437)
		dAP1 = self.calculate_distance(ap1, 2437)
		dAP2 = self.calculate_distance(ap2, 2437)

		self.calculate_location(dAP0, dAP1, dAP2)

	def filter(self, values):
		average = 0
		for value in values:
			average = average + value
		average = average / len(values)
		return average

	# de formules voor de trilateration hebben we genomen uit volgende bron:
	# bron: https://www.101computing.net/cell-phone-trilateration-algorithm/
	def calculate_location(self, distanceBonnie, distanceClyde, distanceVOO):
		# BSSID Bonnie 30:ae:a4:4e:6b:e1
		# BSSID Clyde 80:7d:3a:93:72:bd
		# BSSID VOO-312606 04:a1:51:e0:da:47
		x, y = 0, 1
		A = 2 * CLYDE_COORDINATES[x] - 2 * BONNIE_COORDINATES[x]
		B = 2 * CLYDE_COORDINATES[y] - 2 * BONNIE_COORDINATES[y]
		C = distanceBonnie ** 2 - distanceClyde ** 2 - BONNIE_COORDINATES[x] ** 2 + CLYDE_COORDINATES[x] ** 2 - \
			BONNIE_COORDINATES[y] ** 2 + CLYDE_COORDINATES[y] ** 2
		D = 2 * VOO_COORDINATES[x] - 2 * CLYDE_COORDINATES[x]
		E = 2 * VOO_COORDINATES[y] - 2 * CLYDE_COORDINATES[y]
		F = distanceClyde ** 2 - distanceVOO ** 2 - CLYDE_COORDINATES[x] ** 2 + VOO_COORDINATES[x] ** 2 - \
			CLYDE_COORDINATES[y] ** 2 + VOO_COORDINATES[y] ** 2
		posX = (C * E - F * B) / (E * A - B * D)
		posY = (C * D - A * F) / (B * D - A * E)

		self.draw_radiuses(distanceBonnie, distanceClyde, distanceVOO)
		self.draw_position(posX, posY)

		for room in self.rooms:

			if room.does_it_fit(posX, posY):
				# self.ENVIRONMENT = 4.77
				self.environment = room.n
				self.currentRoom.set(room.name)
				print("ROOM: " + room.name + " | N: " + str(self.environment))
		print(posX, posY)

	def calculate_distance(self, rssiValue, frequencyMhz):
		rssiValue = rssiValue * -1
		wavelength = self.calculate_wavelength(frequencyMhz)
		exponent = (((rssiValue - (20 * math.log((4 * math.pi * REFERENCEDISTANCE) / wavelength, 10))) / (
					10 * self.environment)) * REFERENCEDISTANCE)
		distance = math.pow(10, exponent)
		print("rssi: " + str(rssiValue) + " | distance: " + str(distance), flush=True)
		return distance

	def calculate_wavelength(self, frequencyMhz):
		speedOfLight = 299.792458
		wavelength = speedOfLight / frequencyMhz
		return wavelength

	def draw_radiuses(self, bonnieRadius, clydeRadius, vooRadius):
		# print("drawing radius")
		try:
			self.frame.delete(self.bonnieDrawing)
			self.frame.delete(self.clydeDrawing)
			self.frame.delete(self.vooDrawing)
		except:
			print("Could not delete circles")
		# huissetup
		bonnieWidth = SCALE_FACTOR * 1.5
		bonnieHeight = SCALE_FACTOR * 10.26
		# livingSetup
		# bonnieWidth = SCALE_FACTOR * 0.55
		# bonnieHeight = SCALE_FACTOR * 3.8
		bonnieRadius = SCALE_FACTOR * bonnieRadius

		# huissetup
		clydeWidth = SCALE_FACTOR * 9.03
		clydeHeight = SCALE_FACTOR * 8.02
		# livingsetup
		# clydeWidth = SCALE_FACTOR * 8.35
		# clydeHeight = SCALE_FACTOR * 4.7
		clydeRadius = SCALE_FACTOR * clydeRadius

		vooWidth = SCALE_FACTOR * 4.8
		vooHeight = SCALE_FACTOR * 0.3
		vooRadius = SCALE_FACTOR * vooRadius

		self.bonnieDrawing = self.frame.create_oval(bonnieWidth - bonnieRadius, bonnieHeight - bonnieRadius,
													bonnieWidth + bonnieRadius, bonnieHeight + bonnieRadius,
													outline='red')
		self.clydeDrawing = self.frame.create_oval(clydeWidth - clydeRadius, clydeHeight - clydeRadius,
												   clydeWidth + clydeRadius, clydeHeight + clydeRadius, outline='green')
		self.vooDrawing = self.frame.create_oval(vooWidth - vooRadius, vooHeight - vooRadius, vooWidth + vooRadius,
												 vooHeight + vooRadius)

		self.window.update()

	def draw_position(self, calculatedX, calculatedY):
		# print("drawing position")
		try:
			self.frame.delete(self.currentPosition)
		except:
			print("Could not delete position rectangle")

		currentWidth = SCALE_FACTOR * calculatedX
		currentHeight = SCALE_FACTOR * calculatedY
		self.currentPosition = self.frame.create_rectangle(currentWidth - 5, currentHeight - 5, currentWidth + 5,
														   currentHeight + 5, fill="blue")

		self.window.update()
