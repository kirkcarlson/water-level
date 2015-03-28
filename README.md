# water-level
Water level detector using Python on Raspberry Pi and an aquarium pump

This is a Python program that reads the temperature and pressure from two BMP-085 pressure sensors. One sensor monitors the
ambient air pressure and the other monitors the pressure of a tube connected to an aquarium pump and the free end is held
under water. The latter pressure reflects the depth of the water above the tube opening plus the ambient air pressure which
should be subtracted off. There is some additional pressure gain caused by the resistance of the tubing. A pressure tank (a
water bottle in this case) is used to smooth out the pressure fluctuations caused by the aquarium pump.

An LCD mounted on an Adafruid LCD Pi Plate is used to display information near the data collection point. Most of the time the
data will be sent over a RESTful connection to a web page. The display control is implemented as a finite state machine.
