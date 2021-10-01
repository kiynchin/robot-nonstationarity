from actuonix_driver import LinearDriver
from dynamixel_driver import dxl
import numpy as np
import time


class FiveBar():
    def __init__(self, ids=[1, 2], motor_type="X",
                 device="/dev/ttyUSB0", baudrate=int(1e6), protocol=2):
        self.servos = dxl(motor_id=ids, motor_type=motor_type,
                          devicename=device, baudrate=baudrate, protocol=protocol)
        self.servos.open_port()
        self.theta_range = 2*np.pi*(0.5)
        self.theta_diff_max = np.pi/8
        self.theta1_mid = 2*np.pi*(0.5+0.06)
        self.theta2_mid = 2*np.pi*(0.5-0.06)
        self.theta1_min = self.theta1_mid - self.theta_range/2
        self.theta1_max = self.theta1_mid + self.theta_range/2
        self.theta2_min = self.theta2_mid - self.theta_range/2
        self.theta2_max = self.theta2_mid + self.theta_range/2

        self.linear = LinearDriver()
        self.linear_min = 0.01
        self.linear_zeros = np.ones((1, 12))*self.linear_min
        self.linear_max = 0.0375
        self.linear_range = self.linear_max-self.linear_min

        self.reset()

    def reset(self):
        self.linear.move_joint_position(self.linear_zeros, 1.0)
        self.move_abs(self.theta1_mid, self.theta2_mid)
        time.sleep(0.1)

    def drift(self, pos):
        assert pos >= self.linear_min
        assert pos <= self.linear_max
        p = self.linear_zeros
        p[0, 3:7] = pos
        self.linear.move_joint_position(p, 1.0)
        time.sleep(0.01)
        # self.linear.wait_until_done_moving()

    def move_abs(self, pos1, pos2, err_thresh=0.1, verbose=False):
        if verbose:
            print(f"Raw val: {pos1:.3f},{pos2:.3f}")
        pos1 = np.clip(pos1, self.theta1_min, self.theta1_max)
        pos2 = np.clip(pos2, self.theta2_min, self.theta2_max)
        mean = (pos1+pos2)/2
        pos1 = np.clip(pos1, mean-self.theta_diff_max /
                       2, mean+self.theta_diff_max/2)
        pos2 = np.clip(pos2, mean-self.theta_diff_max /
                       2, mean+self.theta_diff_max/2)
        if verbose:
            print(f"Bounded: {pos1:.3f},{pos2:.3f}\n")

        self.servos.set_des_pos(self.servos.motor_id, [pos1, pos2])

        # Wait till done moving
        err1 = np.inf
        err2 = np.inf
        while err1 > err_thresh or err2 > err_thresh:
            curr = self.get_pos()
            err1 = np.abs(curr[0]-pos1)
            err2 = np.abs(curr[1]-pos2)
            time.sleep(0.001)

    def move_delta(self, delta1, delta2, verbose=False):
        curr = self.get_pos()
        # new_pos1 = curr1 + delta1
        # new_pos2 = curr2 + delta2

        self.move_abs(curr[0]+delta1, curr[1]+delta2, verbose=verbose)

    def get_pos(self):
        curr = self.servos.get_pos(self.servos.motor_id)
        return curr

    def primitive(self, id, mag=0.2*np.pi, verbose=False):

        primitives = [[-mag, -mag],
                      [-mag, 0.0],
                      [-mag, mag],
                      [0.0, -mag],
                      [0.0, 0.0],
                      [0.0, mag],
                      [mag, -mag],
                      [mag, 0.0],
                      [mag, mag]]

        self.move_delta(*primitives[id], verbose=verbose)

    def trajectory(self, primitive_list):
        for idx in primitive_list:
            self.primitive(idx)

    def test_motion(self):
        for j in range(3):
            for i in range(50):
                id = np.random.randint(0, 9)
                mag = np.random.random_sample()
                self.primitive(id, mag)
            self.drift(np.random.random_sample()*self.linear_range + self.linear_min)
            self.move_abs(self.theta1_mid, self.theta2_mid)
        self.reset()
    
    def __del__(self):
        print("FiveBar shutting down.")
        self.reset()


def main():
    robot = FiveBar()
    robot.test_motion()


if __name__ == "__main__":
    main()
