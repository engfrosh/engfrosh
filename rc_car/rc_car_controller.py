import PiMotor
import time

class RC_Car:

    def __init__(self,speed):
        self.speed = speed
        self._back_left = PiMotor.Motor("MOTOR1",2)
        self._back_right = PiMotor.Motor("MOTOR2",1)
        self._front_left = PiMotor.Motor("MOTOR4",1)
        self._front_right = PiMotor.Motor("MOTOR3",2)
        self._all_motors = PiMotor.LinkedMotors(self._front_left, self._front_right, self._back_left, self._back_right)
        self._left_motors = PiMotor.LinkedMotors(self._front_left, self._back_left)
        self._right_motors = PiMotor.LinkedMotors(self._front_right, self._back_right)

        self._arrow_forward = PiMotor.Arrow(3) 
        self._arrow_back = PiMotor.Arrow(1)
        self._arrow_left = PiMotor.Arrow(2)
        self._arrow_right = PiMotor.Arrow(4)

    #def handle_command(self, speed:float, direction:str, time:float):
    #    pass

    # test function to make sure all motors work
    def test_motor(self, speed, duration):
        self._front_left.forward(speed)
        time.sleep(duration)
        self._front_left.stop()

        self._front_right.forward(speed)
        time.sleep(duration)
        self._front_right.stop()

        self._back_left.forward(speed)
        time.sleep(duration)
        self._back_left.stop()

        self._back_right.forward(speed)
        time.sleep(duration)
        self._back_right.stop()

    def back(self, speed, duration):
        self._all_motors.reverse(self.speed)
        self._arrow_back.on()
        time.sleep(duration)
        self._all_motors.stop() 
        self._arrow_back.off()

    def drive(self, speed, duration):
        self._all_motors.forward(self.speed)
        self._arrow_forward.on()
        time.sleep(duration)
        self._all_motors.stop() 
        self._arrow_forward.off()

    def turn_left(self, speed, duration):
        self._right_motors.forward(self.speed)
        self._arrow_left.on()
        time.sleep(duration)
        self._all_motors.stop()
        self._arrow_left.off()

    def turn_right(self, speed, duration):
        self._left_motors.forward(self.speed)
        self._arrow_right.on()
        time.sleep(duration)
        self._all_motors.stop()
        self._arrow_right.off()

#benny = RC_Car(60)

#benny.back(50)
#benny.turn_left(70)
#benny.test_motor(60)