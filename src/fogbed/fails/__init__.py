from enum import Enum, auto
import time, threading

class SplitMethod(Enum):
    UP = auto()
    DOWN = auto()
    RANDOM = auto()


class SelectionMethod(Enum):
    SEQUENTIAL = auto()
    RANDOM = auto()


class Cycler:
    """ Defines a cycler used on fail implementations, where the slot represents the minimum
        time fraction of it """
    def __init__(self, slot_time: int):
        self.slot_time = slot_time
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.__set_interval)
        self.slot_number = 0
        self.running = False

    def action(self):
        """ Run every slot """
        self.slot_number += 1


    def __set_interval(self):
        """ Sets the thread interval """
        next_time = time.time() + self.slot_time

        while not self.stop_event.wait(next_time - time.time()):
            next_time += self.slot_time
            self.action()


    def is_alive(self):
        """ returns the cycler state """
        return self.running


    def start(self):
        """ Starts the cycler """
        self.thread.start()
        self.running = True


    def cancel(self):
        """ Stop the cycler """
        self.stop_event.set()
        self.running = False