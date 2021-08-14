import PiMotor
import time

BACK_LEFT = PiMotor.Motor("MOTOR1", 2)
BACK_RIGHT = PiMotor.Motor("MOTOR2", 1)
FRONT_RIGHT = PiMotor.Motor("MOTOR3", 2)
FRONT_LEFT = PiMotor.Motor("MOTOR4", 1)
ALL_MOTORS = PiMotor.LinkedMotors(FRONT_LEFT, FRONT_RIGHT, BACK_LEFT, BACK_RIGHT)
LEFT_MOTORS = PiMotor.LinkedMotors(FRONT_LEFT, BACK_LEFT)
RIGHT_MOTORS = PiMotor.LinkedMotors(FRONT_RIGHT, BACK_RIGHT)

ARROW_BACK = PiMotor.Arrow(1)
ARROW_LEFT = PiMotor.Arrow(2)
ARROW_FORWARD = PiMotor.Arrow(3)
ARROW_RIGHT = PiMotor.Arrow(4)


class RC_Car:

    def __init__(self, speed):
        self.speed = speed
        self._back_left = BACK_LEFT
        self._back_right = BACK_RIGHT
        self._front_left = FRONT_LEFT
        self._front_right = FRONT_RIGHT
        self._arrow_forward = ARROW_FORWARD
        self._arrow_back = ARROW_BACK
        self._arrow_left = ARROW_LEFT
        self._arrow_right = ARROW_RIGHT
        self._all_motors = ALL_MOTORS
        self._left_motors = LEFT_MOTORS
        self._right_motors = RIGHT_MOTORS

    def turn_left(self, speed=None):
        if speed is None:
            speed = self.speed

        self._arrow_left.on()
        self._arrow_right.on()
        self._left_motors.reverse(self.speed)
        # self._right_motors.forward(self.speed)
        time.sleep(5)
        self._arrow_left.off()
        self._arrow_right.off()
        self._all_motors.stop()


benny = RC_Car(60)

print(benny.speed)
benny.turn_left()
