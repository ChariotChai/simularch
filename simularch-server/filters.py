from typing import Optional, List, Callable, Dict

import simpy
from matplotlib import pyplot as plt
from simpy import Environment

from base import Filter, Schema, Monitor, Signal
from signals import IntervalPulseSignal


class FixedDelayFilter(Filter):
    def __init__(self, env: simpy.Environment, delay: int):
        super().__init__()
        if delay <= 0:
            raise Exception(f'delay should be larger than 0, now set as {delay}')
        self.env = env
        self.cached_queue = [None] * delay
        self.env.process(self.refresh())

    def refresh(self):
        while True:
            self.cached_queue.append(self.input.get_value())
            self.cached_queue.pop(0)
            yield self.env.timeout(delay=1)

    def get_value(self) -> Optional[List]:
        c = self.cached_queue[0]
        if c is None:
            return [None] * len(self.schema())
        else:
            return c

    def schema(self) -> Schema:
        return self.input.wired_output.schema()


class CustomDelayFilter(Filter):
    def __init__(self, env: Environment, delay_calculator: Callable[[Signal], int]):
        super().__init__()
        self.env = env

    def get_value(self) -> Optional[List]:
        pass

    def schema(self) -> Schema:
        return self.input.wired_output.schema()


if __name__ == '__main__':
    env = simpy.Environment()
    sig = IntervalPulseSignal(env, 10)

    monitor_sig = Monitor(env)
    monitor_sig.bind(sig)

    fix_delay_filter = FixedDelayFilter(env, delay=10)
    fix_delay_filter.wire(sig)

    monitor_delay = Monitor(env)
    monitor_delay.bind(fix_delay_filter)

    env.run(until=100)
    t0, v0 = monitor_sig.observation()
    t1, v1 = monitor_delay.observation()

    print(v0)
    print(v1)

    plt.plot(t0, v0[0], color='red')
    plt.plot(t1, v1[0], color='blue')
    plt.show()
