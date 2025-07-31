from enum import Enum, auto
from fogbed.experiment import Experiment
from fogbed.fails import Cycler
from fogbed.fails.models import FailModel, FailMode
from fogbed.fails.utils import add_node, down_node_net, kill_node, up_node_net
from fogbed.node.container import Container
from fogbed.node.instance import VirtualInstance
from mininet.log import info
import random
from fractions import Fraction


class AvailabilityMode(Enum):
    CRASH = auto()
    DISCONNECT = auto()


class AvailabilityFail(FailModel):
    """ This fail maintains the availability of the network according to the informed value """
    def __init__(self, availability=0.5, slot_time=2.0, availability_mode=AvailabilityMode.CRASH):
        self.availability = availability
        self.slot_time = slot_time
        self.availability_mode = availability_mode
        super().__init__(FailMode.AVAILABILITY)


class InstanceAvailabilityCycler(Cycler):
    """ This cycler extends the Cycler to implement the availability failure in virtual instances """
    def __init__(self, slot_time: int, availability_mode: AvailabilityMode, experiment: Experiment, vi: VirtualInstance, availability: float):
        self.availability_mode = availability_mode
        self.experiment = experiment
        self.vi = vi
        self.availability = availability
        self._all_containers = self.vi.containers.copy()
        self.cycle_size = 1
        self.cycle_part = 0
        self.cycle_slot = 0
        self.average = 0
        self.cur_containers_names = list(self._all_containers.keys())
        super().__init__(slot_time)


    def _update_average(self):
        """ Updates the current average for the vi availability """
        amount = len(self.cur_containers_names)
        self.average = ((self.average * (self.slot_number)) + (amount / len(self._all_containers))) / (self.slot_number + 1)
        info(f'\n*** Availability average updated for {self.vi.label}: ' + str(self.average))


    def _stop_action(self, container_name: str):
        """ Handles the stop according to the Availability Mode """
        if (self.availability_mode == AvailabilityMode.CRASH):
            kill_node(self.experiment, container_name)
        elif (self.availability_mode == AvailabilityMode.DISCONNECT):
            container = self._all_containers[container_name]
            down_node_net(container)


    def _start_action(self, container_name: str):
        """ Handles the start according to the Availability Mode """
        if (self.availability_mode == AvailabilityMode.CRASH):
            params = self._all_containers[container_name].params
            container = Container(container_name, params=params)
            add_node(self.experiment, container, self.vi)
        elif (self.availability_mode == AvailabilityMode.DISCONNECT):
            container = self._all_containers[container_name]
            up_node_net(container)

    
    def _update_current_names(self, down_names: list):
        """ Updates the current container names according to the Availability Mode """
        if (self.availability_mode == AvailabilityMode.CRASH):
            self.cur_containers_names = list(self.vi.containers.keys())
        elif (self.availability_mode == AvailabilityMode.DISCONNECT):
            all_container_names = list(self._all_containers.keys())
            self.cur_containers_names = [x for x in all_container_names if x not in set(down_names)]


    def _calcule_stop_amount(self):
        """ Calculates how many nodes will stop in the current cycle_slot """
        if (self.cycle_slot >= self.cycle_size):
            self.cycle_slot = 0

        if (self.cycle_size > 1):
            if (self.cycle_slot < self.cycle_size - self.cycle_part):
                self.cycle_slot += 1
                return self.cycle_amount
            elif (self.cycle_slot < self.cycle_size):
                self.cycle_slot += 1
                return self.cycle_amount + 1
        else:
            return self.cycle_amount


    def _calculate_cycle_size(self):
        """ Calculates the cycle size """
        all_containers_amount = len(self._all_containers)
        division_factor = round(all_containers_amount * (1 - self.availability), 1)
        integer_part = int(division_factor) 
        decimal_part = int((division_factor % 1)* 10) 

        if (decimal_part > 0):
            simplified_parts = Fraction(10, decimal_part)
            self.cycle_size = simplified_parts.numerator
            self.cycle_part = simplified_parts.denominator
            self.cycle_amount = integer_part
        else: 
            self.cycle_amount = int(division_factor)


    def action(self):
        """ Run every slot """
        all_containers_names = list(self._all_containers.keys())
        all_containers_amount = len(self._all_containers)
        stop_amount = self._calcule_stop_amount()
        down_sorted_idxs = random.sample(range(0, all_containers_amount), stop_amount)  # type: ignore
        down_sorted_names = [all_containers_names[down_sorted_idxs[i]] for i, x in enumerate(down_sorted_idxs)]
        to_stop = []
        
        for container_name in self.cur_containers_names:
            ''' Discover which containers will stop '''
            if (container_name in down_sorted_names):
                to_stop.append(container_name)
        
        for container_name in to_stop:
            ''' Stop containers '''
            self._stop_action(container_name)

        if (self.slot_number > 0):
            to_start = []

            for container_name in all_containers_names:
                ''' Discover which containers will start '''
                if (container_name not in down_sorted_names and container_name not in self.cur_containers_names):
                    to_start.append(container_name)
                    
            for container_name in to_start:
                ''' Start containers '''
                self._start_action(container_name)
                
        self._update_current_names(down_sorted_names)
        self._update_average()
        super().action()


    def start(self):
        """ Starts the cycler """
        self._calculate_cycle_size()
        self.action()
        super().start()


class NodeAvailabilityCycler(Cycler):
    """ This cycler extends the Cycler to implement the availability failure on individual nodes """
    def __init__(self, slot_time: int, availability_mode: AvailabilityMode, experiment: Experiment, vi: VirtualInstance, node: Container, availability: float):
        self.availability_mode = availability_mode
        self.experiment = experiment
        self.vi = vi
        self.node = node
        self.availability = availability
        self.cycle_size = 1
        self.cycle_part = 0
        self.cycle_slot = 0
        self.average = 0
        self.is_node_on = True
        super().__init__(slot_time)


    def _update_average(self):
        """ Updates the current average for the node availability """
        amount = 1 if self.is_node_on else 0
        self.average = ((self.average * (self.slot_number)) + amount) / (self.slot_number + 1)
        info(f'\n*** Availability average updated for {self.node.name}: ' + str(self.average))


    def _stop_action(self):
        """ Handles the stop according to the Availability Mode """
        if (self.availability_mode == AvailabilityMode.CRASH):
            kill_node(self.experiment, self.node.name)
        elif (self.availability_mode == AvailabilityMode.DISCONNECT):
            down_node_net(self.node)

        self.is_node_on = False


    def _start_action(self):
        """ Handles the start according to the Availability Mode """
        if (self.availability_mode == AvailabilityMode.CRASH):
            params = self.node.params
            container = Container(self.node.name, params=params)
            add_node(self.experiment, container, self.vi)
        elif (self.availability_mode == AvailabilityMode.DISCONNECT):
            up_node_net(self.node)

        self.is_node_on = True


    def _should_be_on(self):
        """ Discover if the node should be on or off on the current slot """
        if (self.cycle_slot >= self.cycle_size):
            self.cycle_slot = 0

        if (self.cycle_slot < self.cycle_part):
            self.cycle_slot += 1
            return True 
        
        if (self.cycle_slot < self.cycle_size):
            self.cycle_slot += 1
            return False
        
        return False
        

    def action(self):
        """ Run every slot """
        if (self._should_be_on()):
            if (not self.is_node_on):
                self._start_action()
        else:
            if (self.is_node_on):
                self._stop_action()

        self._update_average()
        super().action()


    def _calculate_cycle_size(self):
        """ Calculates the cycle size """
        division_factor = int(10 * self.availability)
        simplified_parts = Fraction(10, division_factor)
        self.cycle_size = simplified_parts.numerator
        self.cycle_part = simplified_parts.denominator


    def start(self):
        """ Starts the cycler """
        self._calculate_cycle_size()
        self.action()
        super().start()