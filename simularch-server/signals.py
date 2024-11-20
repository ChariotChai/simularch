from typing import Optional, List

import numpy as np
import simpy
from matplotlib import pyplot as plt

from base import Signal, Schema, Monitor


class IntervalPulseSignal(Signal):

    def __init__(self, env: simpy.Environment, interval: int):
        super().__init__(env)
        self.env = env
        self.interval = interval

    def update(self):
        pass

    def schema(self) -> Schema:
        return [int]

    def get_value(self) -> Optional[List]:
        if self.env.now % self.interval == 0:
            return [1]
        else:
            return [0]


class PoissonSignal(Signal):

    def __init__(self, env: simpy.Environment, lam: float|int|List[float|int], size: int):
        super().__init__(env)
        if lam is not List:
            self.dim = 1
        else:
            self.dim = len(lam)
        self.series = np.random.poisson(lam=lam, size=(size, self.dim)).tolist()
        self.idx = 0

    def update(self):
        self.idx += 1

    def get_value(self) -> Optional[List]:
        if len(self.series) > self.idx:
            return self.series[self.idx]
        else:
            return [None] * self.dim

    def schema(self) -> Schema:
        return [float] * self.dim


if __name__ == '__main__':
    env = simpy.Environment()
    signal = PoissonSignal(env, lam=3, size=100)
    monitor = Monitor(env)
    monitor.bind(signal)

    env.run(until=120)

    t, v = monitor.observation()
    print(v)
    plt.plot(t, v[0])
    plt.show()
