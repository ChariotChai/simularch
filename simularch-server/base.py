from abc import abstractmethod, ABC
from typing import Optional, List, Dict, Tuple, Self, Callable

import simpy

type Time = int
type Scalar = int | float | None
type ScalarSignal = Tuple[Scalar, ...]  # ['tag', 1, 0.2]
type Signal = Tuple[Scalar | Signal]  # ['tag', 1, 0.2, ['subtag', 2]]
type SignalGroup = list[Signal]
type TimeSeries = list[Tuple[Time, SignalGroup]]
type Schema = list[type | Schema]


class Output(ABC):
    @abstractmethod
    def get_current_value(self) -> SignalGroup:
        pass

    @abstractmethod
    def schema(self) -> Schema:
        pass


class WiredInput:
    def __init__(self):
        self.wired_output: Optional[Output] = None

    def get_current_value(self) -> SignalGroup:
        if self.wired_output is not None:
            return self.wired_output.get_current_value()
        else:
            return []

    def bind(self, source: Output) -> Self:
        if self.wired_output is not None:
            raise Exception('source already bind')
        self.wired_output = source
        return self


class OutputRawValueCollector(WiredInput):
    def __init__(self, env: simpy.Environment):
        super().__init__()
        self.env = env
        self.raw_value = []
        self.env.process(self.__collect__())

    def __collect__(self):
        while True:
            self.raw_value.append(self.wired_output.get_current_value())
            yield self.env.timeout(delay=1)


type MonitorCollector = Callable[[SignalGroup], ScalarSignal]


class Monitor(WiredInput):
    def __init__(self, env: simpy.Environment, collector: MonitorCollector = None):
        super().__init__()
        self.env = env
        self.time_series = []
        self.value_series: List[ScalarSignal] = []
        self.checked = False

        if collector is None:
            self.collector = self.__default_collector
        else:
            self.collector = collector

        self.env.process(self.__collect__())

    def __default_collector(self, sg: SignalGroup) -> ScalarSignal:
        if len(sg) == 0:
            return (None,)
        if not self.checked:
            if len(sg) == 1:
                for s in sg[0]:
                    if isinstance(s, type(Scalar)):
                        raise Exception(f'unexpected type {type(s)}, must use custom collector')
                self.checked = True
            else:
                raise Exception(f'signal group contains more than 1 signal, must use custom collector')
        return sg[0]

    def bind(self, source: Output) -> Self:
        super().bind(source)
        return self

    def __collect__(self):
        while True:
            self.time_series.append(self.env.now)
            self.value_series.append(self.collector(self.get_current_value()))
            yield self.env.timeout(delay=1)

    def observation(self) -> Tuple[list[int], list[ScalarSignal]]:
        return self.time_series, self.value_series


class SeriesOutput(Output, ABC):
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


class Mux(Output):
    def __init__(self):
        self.wired_signals: Dict[str, SeriesOutput] = {}
        self.union_schema: Optional[Schema] = None

    def wire(self, id: str, signal: SeriesOutput):
        if self.wired_signals.__contains__(id):
            raise Exception(f'input {id} already exists')
        self.wired_signals[id] = signal
        self.union_schema = []
        for sig in self.wired_signals.values():
            self.union_schema += sig.schema()

    def get_current_value(self) -> Optional[List]:
        result = []
        for k, v in self.wired_signals.items():
            result += v.get_current_value()
        return result

    def schema(self) -> Schema:
        return self.union_schema


class Filter(Output, ABC):
    def __init__(self):
        super().__init__()
        self.input: WiredInput = WiredInput()

    def wire(self, signal: SeriesOutput) -> Self:
        self.input.bind(signal)
        return self


class Chain(Filter):
    def __init__(self):
        super().__init__()
        self.filter_chain: List[Filter] = []

    def append_filter(self, filter: Filter):
        if len(self.filter_chain) == 0:
            self.filter_chain.append(filter)
            return

        _prev_id, prev_filter = self.filter_chain[-1]
        if prev_filter.schema() != filter.schema():
            raise Exception(f'schema not match')

        self.filter_chain.append(filter)

    def get_current_value(self) -> Optional[List]:
        return self.filter_chain[-1].get_current_value()

    def schema(self) -> Schema:
        return self.filter_chain[-1].schema()


if __name__ == '__main__':
    s1: Schema = [int, str, float]
    s2: Schema = [str, int, float]
    s3: Schema = [str, float, float]

    print(f'{s1 == s2}')
    print(f'{s3 == s2}')
