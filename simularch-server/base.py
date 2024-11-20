from abc import abstractmethod, ABC
from typing import Optional, List, Dict, Tuple

import simpy

from common import transpose_2d

type Schema = Optional[List[type]]


class Output:
    @abstractmethod
    def get_value(self) -> Optional[List]:
        pass

    @abstractmethod
    def schema(self) -> Schema:
        return [int, str]


class WiredInput:
    def __init__(self):
        self.wired_output: Optional[Output] = None

    def get_value(self) -> Optional[List]:
        if self.wired_output is not None:
            return self.wired_output.get_value()
        else:
            return None

    def bind(self, source: Output):
        if self.wired_output is not None:
            raise Exception('source already bind')
        self.wired_output = source


class Monitor(WiredInput):
    def __init__(self, env: simpy.Environment):
        super().__init__()
        self.env = env
        self.time_series = []
        self.value_series = []
        self.dimension = None
        self.env.process(self.__collect__())

    def bind(self, source: Output):
        super().bind(source)
        self.dimension = len(source.schema())

    def __collect__(self):
        while True:
            self.time_series.append(self.env.now)
            self.value_series.append(self.get_value())
            yield self.env.timeout(delay=1)

    def observation(self):
        return self.time_series, transpose_2d(self.value_series)


class Signal(Output, ABC):
    def __init__(self, env: simpy.Environment):
        super().__init__()
        self.env = env
        self.env.process(self.signal_process())

    def signal_process(self):
        while True:
            yield self.env.timeout(delay=1)
            self.update()

    @abstractmethod
    def update(self):
        pass


class Filter(Output, ABC):

    def __init__(self):
        self.wired_signals: Dict[str, Signal] = {}

    def wire(self, id: str, signal: Signal):
        if self.wired_signals.__contains__(id):
            raise Exception(f'input {id} already exists')
        self.wired_signals[id] = signal


type NamedFilter = Tuple[str, Filter]


class Chain(Filter):
    def __init__(self):
        super().__init__()
        self.filter_chain: List[NamedFilter] = []

    def append_filter(self, id: str, filter: Filter):
        if len(self.filter_chain) == 0:
            self.filter_chain.append((id, filter))
            return

        if id in set(map(lambda x: x[0], self.filter_chain)):
            raise Exception(f'filter {id} already exists')

        _prev_id, prev_filter = self.filter_chain[-1]
        if prev_filter.schema() != filter.schema():
            raise Exception(f'schema not match')

        self.filter_chain.append((id, filter))

    def get_value(self) -> Optional[List]:
        return self.filter_chain[-1][1].get_value()

    def schema(self) -> Schema:
        return self.filter_chain[-1][1].schema()


if __name__ == '__main__':
    s1: Schema = [int, str, float]
    s2: Schema = [str, int, float]
    s3: Schema = [str, float, float]

    print(f'{s1 == s2}')
    print(f'{s3 == s2}')