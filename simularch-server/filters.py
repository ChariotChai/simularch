from typing import Callable, Dict

import simpy
from matplotlib import pyplot as plt
from simpy import Environment

from base import Filter, Schema, Monitor, SignalGroup, Time, ScalarSignal
from signals import IntervalPulseSeriesOutput

type SignalDelayCalculator = Callable[[SignalGroup], Time]


class CustomDelayFilter(Filter):
    def __init__(self, env: Environment, delay_calculator: SignalDelayCalculator):
        super().__init__()
        self.env = env
        self.delay_calculator: SignalDelayCalculator = delay_calculator
        self.pending: Dict[int, SignalGroup] = {}
        self.env.process(self.refresh())

    def get_current_value(self) -> SignalGroup:
        if self.pending.__contains__(self.env.now):
            return self.pending[self.env.now]
        return []

    def schema(self) -> Schema:
        return [self.input.wired_output.schema()]

    def refresh(self):
        while True:
            current_value = self.input.get_current_value()
            delay = self.delay_calculator(current_value)
            expect_time = delay + self.env.now
            if self.pending.__contains__(expect_time):
                self.pending[expect_time] += current_value
            else:
                self.pending[expect_time] = [] + current_value
            expired_set = set()
            for k in self.pending.keys():
                if k < self.env.now:
                    expired_set.add(k)
            for k in expired_set:
                self.pending.pop(k)
            yield self.env.timeout(delay=1)


class FixedDelayFilter(CustomDelayFilter):
    def __init__(self, env: simpy.Environment, delay: int):
        super().__init__(env, lambda sg: delay)


if __name__ == '__main__':
    env = simpy.Environment()
    sig = IntervalPulseSeriesOutput(env, 10)

    monitor_sig = Monitor(env)
    monitor_sig.bind(sig)

    fix_delay_filter = FixedDelayFilter(env, delay=10)
    fix_delay_filter.wire(sig)


    def cumulate_collector(sg: SignalGroup) -> ScalarSignal:
        cnt = 0
        for i in sg:
            cnt += i[0]
        return [cnt]


    monitor_delay = Monitor(env, cumulate_collector)
    monitor_delay.bind(fix_delay_filter)


    class TmpDelayer:
        def __init__(self):
            self.start = 1

        def __call__(self, sg: SignalGroup) -> Time:
            if sg[0][0] > 0:
                self.start += 2
            return self.start

    td = TmpDelayer()
    cust_delay_filter = CustomDelayFilter(env, td).wire(sig)

    monitor_cust = Monitor(env, cumulate_collector).bind(cust_delay_filter)

    env.run(until=100)
    t0, v0 = monitor_sig.observation()
    t1, v1 = monitor_delay.observation()

    print(v0)
    print(v1)

    plt.plot(t0, v0, color='red')
    # plt.plot(t1, v1, color='blue')
    plt.plot(monitor_cust.observation()[0], monitor_cust.observation()[1], color='green')
    plt.show()
