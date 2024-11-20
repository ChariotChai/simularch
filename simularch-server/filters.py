from typing import Optional, List, Callable, Dict

import simpy
from matplotlib import pyplot as plt
from simpy import Environment

from base import Filter, Schema, Monitor, Signal
from signals import IntervalPulseSignal


class SimpleUnionFilter(Filter):
    def __init__(self, env: simpy.Environment):
        super().__init__()
        self.env = env
        self.union_schema: Schema = None

    def wire(self, id: str, signal: Signal):
        super().wire(id, signal)
        self.union_schema = []
        for sig in self.wired_signals.values():
            self.union_schema += sig.schema()

    def get_value(self) -> Optional[List]:
        result = []
        for k, v in self.wired_signals.items():
            result += v.get_value()
        return result

    def schema(self) -> Schema:
        return self.union_schema


class FixedDelayFilter(SimpleUnionFilter):
    def __init__(self, env: simpy.Environment, delay: int):
        super().__init__(env)
        if delay <= 0:
            raise Exception(f'delay should be larger than 0, now set as {delay}')
        self.cached_queue = [None] * delay
        self.env.process(self.refresh())

    def refresh(self):
        while True:
            self.cached_queue.append(super().get_value())
            self.cached_queue.pop(0)
            yield self.env.timeout(delay=1)

    def get_value(self) -> Optional[List]:
        c = self.cached_queue[0]
        if c is None:
            return [None] * len(self.schema())
        else:
            return c


class CustomDelayFilter(Filter):
    def __init__(self, env: Environment, delay_calculator: Callable[[Dict[str, List]], int]):
        super().__init__()



    def get_value(self) -> Optional[List]:
        pass

    def schema(self) -> Schema:
        pass


if __name__ == '__main__':
    env = simpy.Environment()
    sig = IntervalPulseSignal(env, 10)

    monitor_sig = Monitor(env)
    monitor_sig.bind(sig)

    fix_delay_filter = FixedDelayFilter(env, delay=10)
    fix_delay_filter.wire('pulse', sig)

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
