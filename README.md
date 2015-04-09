# water-level
Water level detector using Python on Raspberry Pi and an aquarium pump.

This is a Python program that reads the temperature and pressure from two BMP-085 pressure sensors.
One sensor monitors the
ambient air pressure and the other monitors the pressure of a tube connected to an aquarium pump and
the free end is held
under water. The latter pressure reflects the depth of the water above the tube opening plus the ambient air pressure. The difference of the two pressures is the pressure of the water plus some 
pressure gain caused by the resistance of the tubing. This resistance is assumed to be constant and
can be subtracted off. [It is possible that the resistance is dependant on humidity.] A pressure tank (a
water bottle in this case) is used to smooth out the pressure fluctuations caused by the aquarium pump.

The water tube should be at least 12" below the surface of the water. It seems that the depth indication
is not linear on shallow placement. Depth of the water tube is dependent on the pressure delivered by the
aquarium pump. The placement should also reflect the anticipated changes in water levels.

Data is displayed on an LCD mounted on an Adafruid LCD Pi Plate.
A user can select various meausurements using the Pi Plate buttons.
[This part of the code is implemented as a Finite State Machine (FSM). The buttons
and a simple timer are used as events to drive the FSM.]

Data will be sent over a RESTful connection to a web page. This is based on the emoncms.org implementation of
emoncms, which allows data to be displayed graphically on web browsers and to allow web page widgets to
access the real-time data

Things to do:
- perhaps separate out the parameter editing from the normal display functions.
- generalize the editing capabilities to apply to other parameters.
- handle the case when a WiFi connection cannot be established.
