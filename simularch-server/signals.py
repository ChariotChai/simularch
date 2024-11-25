import numpy as np
import simpy
from matplotlib import pyplot as plt

from base import SeriesOutput, Schema, Monitor, SignalGroup, OutputRawValueCollector


class IntervalPulseSeriesOutput(SeriesOutput):
    """
    e.g.
    [
        [[0]], # t0
        [[0]], # t1
        [[1]], # t2
        ...
    ]
    only 1 signal in the signal group
    only 1 scalar in the signal
    """

    def __init__(self, env: simpy.Environment, interval: int):
        super().__init__(env)
        self.env = env
        self.interval = interval

    def update(self):
        pass

    def schema(self) -> Schema:
        return [int]

    def get_current_value(self) -> SignalGroup:
        if self.env.now % self.interval == 0:
            return [(1,)]
        else:
            return [(0,)]


class PoissonSeriesOutput(SeriesOutput):
    """
    e.g for lam=[3, 10]
    [
        [[2, 8]],
        [[4, 15]],
        [[3, 17]]
    ]
    only 1 signal in the signal group
    len(lam) scalars in the signal
    """

    def __init__(self, env: simpy.Environment, lam: float | int | list[float | int], size: int):
        super().__init__(env)
        if isinstance(lam, list):
            self.dim = len(lam)
        else:
            self.dim = 1
        self.series: list[tuple[int]] = np.random.poisson(lam=lam, size=(size, self.dim)).tolist()
        self.idx = 0

    def update(self):
        self.idx += 1

    def get_current_value(self) -> SignalGroup:
        if len(self.series) > self.idx:
            return [tuple(self.series[self.idx])]
        else:
            return [tuple([None] * self.dim)]

    def schema(self) -> Schema:
        return [float] * self.dim


if __name__ == '__main__':
    env = simpy.Environment()
    # signal = IntervalPulseSeriesOutput(env, interval=5)
    signal = PoissonSeriesOutput(env, lam=[3, 10], size=100)
    print(f'signal schema: {signal.schema()}')

    monitor = Monitor(env).bind(signal)

    rc = OutputRawValueCollector(env).bind(signal)

    env.run(until=120)

    t, v = monitor.observation()
    print(v)
    print(rc.raw_value)
    plt.plot(t, v)
    plt.show()
