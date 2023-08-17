import random
import io
import pyrtl
import os
import fnmatch

import blifparser.blifparser as blifparser

# Set the recursion limit to be higher
import sys
sys.setrecursionlimit(10000)

# Find all the .blif files in the benchmarks directory
files = []
curr_file_dir = os.path.dirname(__file__)
for root, dirnames, filenames in os.walk(curr_file_dir + '/../../ariths-gen/'):
    for filename in fnmatch.filter(filenames, '*.blif'):
        files.append(os.path.join(root, filename))

for file in files:
    ##############################
    # 1. blifparser
    filepath = os.path.abspath(file)
    print(filepath)
    parser = blifparser.BlifParser(filepath)

    # generate the graph and memorize some statistics
    graph_data = parser.get_graph()

    # retrive networkx graph: can be used to export it as an image or customize it
    nx_graph = graph_data.nx_graph

    print("number of edges: ", nx_graph.number_of_edges())
    print("number of nodes: ", nx_graph.number_of_nodes())

    """
    1. number of items of time and area => Time & Area 면 OK
    2. connectivity (input 개수, output 개수) => OK
    3. input/output 개수의 비율 => OK
    4. circuit들의 traffic (busyness)
    5. 총 connection 수 (point-to-point connections) => OK?
    6. critical path와 critical path에서 필요한 hop의 수 measure/count => OK
    7. regression
    """

    ##############################

    # 2. pyrtl
    pyrtl.reset_working_block()

    print("File: " + file)
    f = open(file, 'r')
    blif = f.read()

    pyrtl.input_from_blif(blif)    # Importing from blif file
    print("done loading " + file)

    # Synthesis
    pyrtl.synthesize()

    # Optimization
    pyrtl.optimize()

    inputs = pyrtl.working_block().wirevector_subset(pyrtl.Input)
    outputs = pyrtl.working_block().wirevector_subset(pyrtl.Output)
    print("Inputs: ", len(inputs))
    print("Outputs: ", len(outputs))
    # for inp in inputs:
    #     print(inp)

    # Timing analysis
    timing = pyrtl.TimingAnalysis()
    timing.print_max_length()

    # We are also able to print out the critical paths as well as get them
    # back as an array.
    critical_path_info = timing.critical_path(print_cp=False)
    line_indent = " " * 2
    #  print the critical path
    for cp_num, cp in enumerate(critical_path_info):
        print("Critical path", cp_num, ":", "from ",
              cp[0], ", hop count: ", len(cp[1]))

    # --- Part 2: Area Analysis --------------------------------------------------

    # PyRTL also provides estimates for the area that would be used up if the
    # circuit was printed as an ASIC.

    logic_area, mem_area = pyrtl.area_estimation(tech_in_nm=65)
    est_area = logic_area + mem_area
    print("Estimated Area of block", est_area, "sq mm")
    print()

    break
