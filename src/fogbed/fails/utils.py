import math
import random
from fogbed.experiment import Experiment
from fogbed.fails import SplitMethod, SelectionMethod
from fogbed.node.container import Container
from threading import Timer

from fogbed.node.instance import VirtualInstance

def calculate_split(value: int, factor: float, split_method: SplitMethod):
    """ Calculate a number of items to split based on a factor and a split method
        value: total amount of something
        factor: a number that will be mutiplied by the value to get the split amount
        split_method: how the split will be done
        returns: the split amount """
    if split_method == SplitMethod.RANDOM:
        return random.Random.randint(0, int)
    elif split_method == SplitMethod.DOWN:
        return math.floor(value * factor)

    return math.ceil(value * factor)


def kill_node(experiment: Experiment, node_name: str):
    """ Kills a node from experiment
        experiment: experiment to kill a node
        node_name: name of the node to be killed """
    experiment.remove_docker(node_name)


def add_node(experiment: Experiment, node: Container, vi: VirtualInstance):
    """ Adds a new node in the experiment
        experiment: experiment to add a node
        node: node to be added
        vi: virtual instance to add a node """
    experiment.add_docker(node, vi)


def kill_node_on_time(experiment: Experiment, node: Container, life_time: int):
    """ Kills a node after the time passed by the life_time argument
        experiment: experiment to kill a node
        node_name: name of the node to be killed
        lime_time: time in seconds waited before the kill action
        returns: timer thread """
    def action():
        kill_node(experiment, node.name)
    
    timer = Timer(life_time, action, [])
    return timer


def kill_nodes_on_time(experiment: Experiment, vi: VirtualInstance, fail_rate: float, life_time: int, split_method: SplitMethod, selection_method: SelectionMethod):
    """ Kills several nodes after the time passed by the life_time argument, the amount of
        nodes to be killed is determined by the fail_rate and the split_method and the nodes
        will be selected by the selection_method
        experiment: experiment to kill a node
        vi: virtual instance to kill a node
        node_name: name of the node to be killed
        fail_rate: rate that determines what percentage of nodes will be killed
        lime_time: time waited before the kill action
        split_method: how the split will be done
        selection_method: how the nodes to be killed will be selected """
    def action():
        all_nodes = list(vi.containers.keys())
        vi_len = len(vi.containers)
        stop_amount = calculate_split(vi_len, fail_rate, split_method)

        if(selection_method == SelectionMethod.SEQUENTIAL):
            for idx, node_name in enumerate(all_nodes):
                if (idx < stop_amount):
                    kill_node(experiment, node_name)
                else:
                    break
        else:
            idx_to_remove = random.sample(range(0, vi_len), stop_amount)
            next_idx = idx_to_remove.pop(0)

            for idx, node_name in enumerate(all_nodes):
                if (idx == next_idx):
                    kill_node(experiment, node_name)

                    if (len(idx_to_remove) == 0):
                        break

                    next_idx = idx_to_remove.pop(0)
                    
    timer = Timer(life_time, action, [])
    return timer


def down_node_net(node: Container):
    """ Downs the node net
        node: node to be disconnected """
    node.cmd('ifconfig ' + node.name + '-eth0 down')
    node.cmd('ifconfig eth0 down')


def down_node_net_on_time(node: Container, life_time: int):
    """ Downs the node net after time
        node: node to be disconnected 
        life_time: time waited before the down action"""
    def action():
        down_node_net(node)
    
    timer = Timer(life_time, action, [])
    return timer


def down_nodes_net_on_time(vi: VirtualInstance, fail_rate: float, life_time: int, split_method: SplitMethod, selection_method: SelectionMethod):
    """ Down several nodes after the time passed by the life_time argument, the amount of
        nodes to be disconnected is determined by the fail_rate and the split_method and the nodes
        will be selected by the selection_method
        vi: virtual instance to down a node
        node_name: name of the node to be disconnected
        fail_rate: rate that determines what percentage of nodes will be disconnected
        lime_time: time waited before the down action
        split_method: how the split will be done
        selection_method: how the nodes to be disconnected will be selected """
    def action():
        all_nodes = list(vi.containers.keys())
        vi_len = len(vi.containers)
        stop_amount = calculate_split(vi_len, fail_rate, split_method)

        if(selection_method == SelectionMethod.SEQUENTIAL):
            for idx, node_name in enumerate(all_nodes):
                if (idx < stop_amount):
                    down_node_net(vi.containers[node_name])
                else:
                    break
        else:
            idx_to_remove = random.sample(range(0, vi_len), stop_amount)
            next_idx = idx_to_remove.pop(0)
            
            for idx, node_name in enumerate(all_nodes):
                if (idx == next_idx):
                    down_node_net(vi.containers[node_name])

                    if (len(idx_to_remove) == 0):
                        break

                    next_idx = idx_to_remove.pop(0)
                    
    timer = Timer(life_time, action, [])
    return timer


def up_node_net(node: Container):
    """ Ups the node net
        node: node to be reconnected """
    node.cmd('ifconfig ' + node.name + '-eth0 up')
    node.cmd('ifconfig eth0 up')


def up_node_net_on_time(node: Container, life_time: int):
    """ Ups the node net after time
        node: node to be reconnected 
        life_time: time waited before the up action"""
    def action():
        up_node_net(node)
    
    timer = Timer(life_time, action, [])
    return timer