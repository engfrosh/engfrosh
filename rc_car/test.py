"""Car test script with properly aligned motors. Drives forward for 2 seconds."""

import PiMotor
import time

back_left = PiMotor.Motor("MOTOR1", 2)
back_right = PiMotor.Motor("MOTOR2", 1)
front_right = PiMotor.Motor("MOTOR3", 2)
front_left = PiMotor.Motor("MOTOR4", 1)
all_motors = PiMotor.LinkedMotors(front_left, front_right, back_left, back_right)

arrow_back = PiMotor.Arrow(1)
arrow_left = PiMotor.Arrow(2)
arrow_forward = PiMotor.Arrow(3)
arrow_right = PiMotor.Arrow(4)


front_left.forward(50)
front_right.forward(50)
back_left.forward(50)
back_right.forward(50)
time.sleep(2)
all_motors.stop()
