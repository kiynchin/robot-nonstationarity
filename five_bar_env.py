from five_bar import FiveBar
from realsense_camera import RealsenseCamera
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np


class FiveBarEnv(gym.Env):
    def __init__(self):
        self.camera = RealsenseCamera(visualize=False, viewport=[311, 173, 237, 150])
        self.camera.start()
        self.hardware = FiveBar()
        self.action_space = spaces.Discrete(9)
        self.observation_space = spaces.Box(
            low=np.array([0, 0, -np.pi, -2*np.pi]),
            high=np.array([2*np.pi, 2*np.pi, np.pi, 2*np.pi]),
            dtype=np.float64
        )
        self.stationaryid = self.hardware.stationaryid

    def try_recover(self, keypoints):
        return [-1] * (self.observation_space.shape[0] - 2)

    def _get_obs(self):
        x_servo = self.hardware.get_pos()
        success, x_pndlm = self.camera.feed.get()

        if success:
            state = [*x_servo, *x_pndlm]
        else:
            state = [*x_servo, *self.try_recover(x_pndlm)]
        return np.array(state)

    def step(self, u):
        self.hardware.primitive(u)
        state = self._get_obs()
        reward = self.reward(state)
        return state, reward, False, {}

    def drift(self, pos):
        self.hardware.drift(pos)

    def reward(self, state):
        return (np.abs(state[2]) - np.pi)**2

    def reset(self):
        self.hardware.reset()
        return self._get_obs()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def __del__(self):
        self.hardware.reset()
        self.camera.__del__()
