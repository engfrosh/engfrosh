import PiMotor
import time


class RC_Car:

    def __init__(self, speed):
        self.speed = speed
        self._back_left = PiMotor.Motor("MOTOR1", 2)
        self._back_right = PiMotor.Motor("MOTOR2", 1)
        self._front_left = PiMotor.Motor("MOTOR4", 1)
        self._front_right = PiMotor.Motor("MOTOR3", 2)
        self._all_motors = PiMotor.LinkedMotors(self._front_left, self._front_right, self._back_left, self._back_right)
        self._left_motors = PiMotor.LinkedMotors(self._front_left, self._back_left)
        self._right_motors = PiMotor.LinkedMotors(self._front_right, self._back_right)

        self._arrow_forward = PiMotor.Arrow(3)
        self._arrow_back = PiMotor.Arrow(1)
        self._arrow_left = PiMotor.Arrow(2)
        self._arrow_right = PiMotor.Arrow(4)

    # def handle_command(self, speed:float, direction:str, time:float):
    #    pass

    def test_motor(self, speed):
        self._front_left.forward(speed)
        time.sleep(1)
        self._front_left.stop()

        self._front_right.forward(speed)
        time.sleep(1)
        self._front_right.stop()

        self._back_left.forward(speed)
        time.sleep(1)
        self._back_left.stop()

        self._back_right.forward(speed)
        time.sleep(1)
        self._back_right.stop()

    def back(self, speed):
        self._all_motors.reverse(self.speed)
        self._arrow_back.on()
        time.sleep(0.75)
        self._all_motors.stop()
        self._arrow_back.off()

    def drive(self, speed):
        self._all_motors.forward(self.speed)
        self._arrow_forward.on()
        time.sleep(0.75)
        self._all_motors.stop()
        self._arrow_forward.off()

    def turn_left(self, speed):
        self._right_motors.forward(self.speed)
        time.sleep(1)
        self._all_motors.stop()

    def turn_right(self, speed):
        self._left_motors.forward(self.speed)
        time.sleep(1)
        self._all_motors.stop()


benny = RC_Car(60)

benny.back(50)
# benny.turn_left(70)
# benny.test_motor(60)
