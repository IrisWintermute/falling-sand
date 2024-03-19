import random
import os
import time

class Node:
    def __init__(self, x, y, ntype):
        self.type_densities = {
            'air' : 3, 
            'steam' : 2, 
            'water' : 8,
            'ice' : 6,
            'sand' : 16,
            'molten_sand' : 18,
            'plutonium' : 40,
            'heatsink' : -40
        }
        self.flux_factors = {
            'steam' : 3, 
            'water' : 0,
            'sand' : -3,
            'molten_sand' : 0,
            'ice' : -4,
            'plutonium' : -10,
            'heatsink' : -10

        }
        self.transition_temps = {
            'water' : {'ceil' : (100, 4, 'steam'), 'floor' : (0, 8.0/6.0, 'ice')},
            'ice' : {'ceil' : (0, 6.0/8.0, 'water')},
            'steam' : {'floor' : (100, 1.0/4.0, 'water')},
            'sand' : {'ceil' : (400, 16.0/18.0, 'molten_sand')},
            'molten_sand' : {'floor' : (400, 18.0/16.0, 'sand')}
        }
        self.conductances = {
            'water' : 0.5,
            'ice' : 0.2,
            'steam' : 0.7,
            'sand' : 0.6,
            'molten_sand' : 0.9,
            'plutonium' : 1.0,
            'heatsink' : 1.0

        }

        self.x = x
        self.y = y
        self.adjacents = {}
        self.set_type(ntype)

    def get_adjacent_dirs(self):
        return [adj for adj in self.adjacents.keys()]

    def get_adjacents(self):
        return [adj for adj in self.adjacents.values()]

    def get_adj(self, direction):
        return self.adjacents.get(direction, EdgeNode())

    def add_adj(self, ref, direction):
        self.adjacents[direction] = ref

    def get_type(self):
        return self.type

    def set_type(self, ntype, pressure = 1, temperature = 20):
        self.t_ceil = self.transition_temps.get(ntype, {}).get('ceil', 'x')
        self.t_floor = self.transition_temps.get(ntype, {}).get('floor', 'x')
        self.conduct = self.conductances.get(ntype, 1)
        self.p = pressure
        self.temp = temperature
        self.type = ntype
        self.density = self.type_densities.get(ntype, 1)
        self.ff = self.flux_factors.get(ntype, 0)

    def get_coords(self):
        return self.y, self.x

    def get_ff(self):
        return self.ff

    def get_rho(self):
        return self.density
    
    def get_t(self):
        return self.temp
    
    def get_c(self):
        return self.conduct
    
    def get_p(self):
        return self.p if self.p != 0 else 0.001
    
    def inc_p(self, increment):
        self.p += increment
    
    def inc_t(self, increment):
        self.temp += increment

        # evaporation/boiling
        if self.t_ceil != 'x' and self.temp > self.t_ceil[0]:
            (_, p_factor, new_type) = self.t_ceil
            self.set_type(new_type, p_factor * self.p, self.temp)

        # condensation/freezing 
        #TODO: fix error where evaporation and condensation produce unwanted behaviour
        if self.t_floor != 'x' and self.temp < self.t_floor[0]:
            (_, p_factor, new_type) = self.t_floor
            self.set_type(new_type, p_factor * self.p, self.temp)

        
    
    def __str__(self):
        return f"Node at ({self.y},{self.x})."
    
    def get_rand_int(self, a, b):
        val = int(str(self.x * self.y)[-1])
        val = val if val < b else b
        return int(random.randint(a, b) * val / b) 
    
class EdgeNode:
    def get_type(self):
        return 'sim_edge'

class Grid:
    def __init__(self, x, y, condition):
        self.x = x
        self.y = y
        self.initcond = condition
        # build empty grid
        self.nodes = [[Node(j, i, 'air') for j in range(x)] for i in range(y)]
        self.interconnect()
        self.populate()
    
    def interconnect(self):
        # pass adjacent references to each node
        print("Interconnecting grid...")
        for i in range(self.y):
            for j in range(self.x):
                node = self[i][j]
                for x, y, d in adjacent_coords(j, i, self.x, self.y):
                    try:
                        adj_ref = self[y][x]
                        node.add_adj(adj_ref, d)
                    except IndexError:
                        print(f"x: {x}, y: {y}")
    
    def populate(self):
        # populate grid with Node objects
        print("Populating grid...")
        for (i, j, t) in self.initcond:
            self[i][j].set_type(t)

    def update_grid(self, utype):

        non_update_types = ['barrier', 'air']
        # utype defines the update function update_grid should pass nodes to
        func_hash = {
            'movement' : node_movement_update,
            'temp' : node_temperature_update,
            'pressure' : node_pressure_update
        }
        updated_nodes = {}
        temp = 0
        dir = random.random()
        for i in range(self.y):
            for j in range(self.x):
                # average of 50% of frames, horizonatal update direction is reversed
                # this is done to prevent asymmetry caused by uniform update direction
                if dir > 0.5:
                    j = self.x - j - 1
                # check node has not already been updated and can be updated
                temp += self[i][j].get_t()
                if updated_nodes.get((i, j)) or self[i][j].type in non_update_types:
                    continue

                node = self[i][j]
                updated_coords = func_hash[utype](node)
                # update updated_nodes with new node coords if update took place
                # otherwise update updated_nodes with current node coords
                if updated_coords:
                    if type(updated_coords) == list:
                        for coord in updated_coords: updated_nodes[coord] = True
                    else:
                        updated_nodes[updated_coords] = True
                else:
                    updated_nodes[(node.y, node.x)] = True
        if utype == 'temp': print(temp / (self.x * self.y))

    def draw(self):
        clear()
        char_hash = {
            'air' : ' ',
            'barrier' : '%',
            'water' : '+',
            'ice' : 'H',
            'sand' : '&',
            'steam' : '~',
            'plutonium' : 'X',
            'molten_sand' : 'M',
            'heatsink' : '5'
        }
        rows_print = []
        for i in range(self.y):
            row_print = []
            for j in range(self.x):
                node_type = self[i][j].get_type()
                row_print.append(char_hash[node_type])
            rows_print.append(row_print)
        rows_print = rows_print[::-1]
        for row in rows_print:
            row_str = ' '.join(row)
            print(row_str)

    def __getitem__(self, key):
        return self.nodes[key]


def clear():
    os.system('cls')

def node_temperature_update(curr_node):
    # air and barriers do not conduct heat
    curr_t = curr_node.get_t()
    curr_c = curr_node.get_c()
    adjs = [adj for adj in curr_node.get_adjacents() if adj.get_type() not in ['barrier', 'air']]
    out = [curr_node.get_coords()]
    for adj in adjs:
        adj_t = adj.get_t()
        adj_c = adj.get_c()
        delta_t = (curr_t - adj_t) * curr_c * adj_c / (len(adjs) + 1)
        adj.inc_t(delta_t)
        curr_node.inc_t(-delta_t)
        out.append(adj.get_coords())
    if curr_node.get_type() == 'plutonium': curr_node.inc_t(300)
    if curr_node.get_type() == 'heatsink': curr_node.inc_t(0)
    return out

def node_pressure_update(curr_node):
    # pressure is only exchanged between air and nodes of same type
    curr_type = curr_node.get_type()
    curr_p = curr_node.get_p()
    curr_t = curr_node.get_t()
    if curr_p == 1: return None
    # if curr_p < 1, merge into adjs with p < 1
    if curr_p < 1:
        adjs = [adj for adj in curr_node.get_adjacents() if adj.get_type() == curr_type and adj.get_p() < 1]  
        if not adjs: return None
        out = []
        delta_p = curr_p / len(adjs)
        delta_t = curr_t / len(adjs)
        for adj in adjs:
            adj.inc_p(delta_p)
            adj.inc_t(delta_t)
            out.append(adj.get_coords())
        curr_node.set_type('air')
        return out
    
    # curr_p must be > 1

    # divide into adjacent air nodes
    adjs = [adj for adj in curr_node.get_adjacents() if adj.get_type() == 'air']
    if adjs:
        out = [curr_node.get_coords()]
        delta_p = curr_p / (len(adjs) + 1)
        delta_t = curr_t / (len(adjs) + 1)
        for adj in adjs:
            adj.set_type(curr_type, delta_p, delta_t)
            curr_node.inc_p(-delta_p)
            curr_node.inc_p(-delta_t)
            out.append(adj.get_coords())
        return out
    
    # transact pressure to adjacent nodes of same type
    adjs = [adj for adj in curr_node.get_adjacents() if adj.get_type() == curr_type and curr_p > adj.get_p()]
    if adjs:
        out = [curr_node.get_coords()]
        for adj in adjs:
            adj_p = adj.get_p()
            adj_t = adj.get_t()
            delta_p = (curr_p - adj_p) / (len(adjs) + 1)
            delta_t = (curr_t - adj_t) / (len(adjs) + 1)
            adj.inc_p(delta_p)
            adj.inc_t(delta_t)
            curr_node.inc_p(-delta_p)
            curr_node.inc_t(-delta_t)
            out.append(adj.get_coords())
        return out
    
    return None

def node_movement_update(curr_node):
    # ['u', 'r', 'd', 'l', 'ur', 'dr', 'dl', 'ul']
    directions = curr_node.get_adjacent_dirs()
    # mutable copy has indices removed, original list is used to reference indices
    directions_mut = directions.copy()
    adj_occlusions = []
    # identify which (if any) diagonal adjacents are occluded by cardinal adjacents w/ impassible types

    for dir in directions:
        adj_type = curr_node.get_adj(dir).get_type()
        if adj_type == curr_node.get_type():
            directions_mut.remove(dir)
        if adj_type == 'barrier': # barrier type is impassible
            directions_mut.remove(dir)
            if len(dir) == 1:
                adj_occlusions.extend(diag_dir for diag_dir in directions if dir != diag_dir and dir in diag_dir)

    for dir in directions_mut:
        if len(dir) == 1: continue
        adj_type = curr_node.get_adj(dir).get_type()
        if adj_occlusions.count(dir) == 2:
            directions_mut.remove(dir)

    if not directions_mut: return None
    # at this stage, directions defines the superset of valid movements
    # now, the function must identify the behaviours of curr_node accori=ding to its type
    # and which direction to move in according to its neighbors
    # RULE: node A cannot displace node B if A.get_density() < B.get_density(), unless displacement direction is pro-gravity
        # e.g: gas moves up through sand, stone sinks in water, pumice floats on water, stone floats on molten lead
        # if (A.rho - B.rho) * (A.y - B.y) + A.flux_factor > 0 then A can move, otherwise A cannot
        # flux_factor is a type-specific constant that defines how likely the node is to move in non-conservative directions
    '''
        XXX    XXX    XXX    4X4    454
        XCX    XCX    3C3    3C3    3C3
        X1X    212    212    212    212
    '''
    direction_hash = {
        'd' : 4,
        'dr' : 2,
        'dl' : 2,
        'r' : 0.2,
        'l' : 0.2,
        'ur' : -2,
        'ul' : -2,
        'u' : -4, 
    }
    directions_weighted = []
    for dir in directions_mut:
        target_node = curr_node.get_adj(dir)
        movement_weight = (curr_node.get_rho() - target_node.get_rho()) * direction_hash[dir] + curr_node.get_ff()
        if movement_weight > 0:
            directions_weighted.append((dir, movement_weight))
    
    if not directions_weighted: return None
    # at this point, all remaining directions are valid possible movements for the node

    decided_direction = ('', 0)
    for (dir, weight) in directions_weighted:
        if weight > decided_direction[1]:
            decided_direction = (dir, weight)
        elif weight == decided_direction[1] and random.random() > 0.5:
            decided_direction = (dir, weight)

    # perform type transaction with adjacent at decided_direction[0]
    if decided_direction[0]:
        decided_node = curr_node.get_adj(decided_direction[0])
        curr_type = curr_node.get_type()
        curr_node.set_type(decided_node.get_type())
        decided_node.set_type(curr_type)
        return decided_node.get_coords()
    else:
        return None

def adjacent_coords(x, y, x_limit, y_limit):
    # up, right, down, left, up-right, down-right, down-left, up-left
    adjacents = [(x, y+1, 'u'), (x+1, y, 'r'), (x, y-1, 'd'), (x-1, y, 'l'), (x+1, y+1, 'ur'), (x+1, y-1, 'dr'), (x-1, y-1, 'dl'), (x-1, y+1, 'ul')]
    # early return for no-edges case
    if (0 < y) and (y < (y_limit - 1)) and (0 < x) and (x < (x_limit - 1)):
        return adjacents
    # slower for-loop check for edges and corners
    adjacents_corners = []
    for (x_a, y_a, _) in adjacents:
        # remove invalid adjacents
        if ((0 <= y_a) and (y_a <= (y_limit - 1)) and (0 <= x_a) and (x_a <= (x_limit - 1))):
            adjacents_corners.append((x_a, y_a, _))
    return adjacents_corners

def generate_coords(y_l, y_m, x_l, x_m, ntype, density):
    if y_l > y_m or x_l > x_m:
        raise ValueError
    area = (y_m - y_l + 1) * (x_m - x_l + 1)
    coord_count = int(area * density)
    set_out = set()
    try:
        while len(set_out) < coord_count:
            set_out.add((random.randint(y_l, y_m), random.randint(x_l, x_m), ntype))
        print(len(set_out))
    except ValueError:
        print("Error: coordinate arguments are not valid.")
    else:
        return set_out

def main():
    launch_time = time.time()
    # PROGRAMMING SPACE
    x = 50
    y = 20
    duration = 1500 # number of frames

    #barrier_coords = [(int(j/4) + 11, j + 10, 'barrier') for j in range(int(x * 0.6)) if j % 8 != 0]
    #barrier_coords += [(y - j - 26, j + 20, 'barrier') for j in range(int(x * 0.4)) if j != 18]
    sand_coords = generate_coords(1, y - 16, 5, x - 4, 'sand', 0.7)
    water_coords = generate_coords(10, y - 6, 6, x - 1, 'steam', 1.0)
    plutonium_coords = generate_coords(0, 0, 0, x - 1, 'plutonium', 1.0)
    heatsink_coords = generate_coords(y - 1, y - 1, 0, x - 1, 'heatsink', 1.0)
    initial_coords = water_coords.union(plutonium_coords).union(heatsink_coords).union(sand_coords)
    # END PROGRAMMING SPACE

    print("Building grid...")
    node_grid = Grid(x, y, initial_coords)
    print("Grid ready.")

    user_input = input("Enter 'start' to begin program: ")
    if user_input == 'start':
        average_frame_time = [0]
        timeframe = 0
        while True:
            start = time.time() - launch_time

            node_grid.draw()
            node_grid.update_grid('temp')
            node_grid.update_grid('pressure')
            node_grid.update_grid('movement')
            end = time.time() - launch_time
            delta_time = end - start
            average_frame_time.append(delta_time)
            timeframe += 1
            if timeframe >= duration:
                break

        print(f"Frames executed: {len(average_frame_time) - 1}")
        average_frame_time = sum(average_frame_time)/len(average_frame_time)
        print(f"Average frame time: {average_frame_time}")

if __name__ == '__main__':
    main()

