import heapq
import socket
import time

import sys

class Node(object):
    def __init__(self, x, y, val):
        self.coor = (x, y)
        self.value = val
        self.calc_weight()
        self.visited = False
        self.get_new = 0
        if self.value != "L":
            self.passable = True
        else:
            self.passable = False

    def __repr__(self):
        return "x" + str(self.coor[0]) + ",y" + str(self.coor[1]) + ":" + self.value + " "

    def __repr_only_val__(self):
        return str(self.value + " ")

    def __lt__(self, other):
        return self.coor.__lt__(other.coor)

    def calc_weight(self):
        if self.value == "M":
            self.weight = 2
        elif self.value == "L":
            self.weight = 100
        else:
            self.weight = 1


def create_commands(path, start):
    prevx = start[0]
    prevy = start[1]
    commands = []
    for i in path:
        print(i, prevx, ",", prevy)
        if prevx != i[0]:
            if (i[0] - 1) % size_x == prevx:
                commands.append("right")
            else:
                commands.append("left")
        else:
            if (i[1] - 1) % size_y == prevy:
                commands.append("down")
            else:
                commands.append("up")
        prevx = i[0]
        prevy = i[1]
    return commands


def calc_possible_new_fields(val, coor, map):
    my_range = 0
    if "G" in val:
        my_range = 5
    elif "M" in val:
        my_range = 7
    elif "L" in val:
        my_range = 0
    else:
        my_range = 3

    fields_in_range = []

    for y in range(coor[1] - (my_range // 2), coor[1] + (my_range // 2 + 1)):
        for x in range(coor[0] - (my_range // 2), coor[0] + (my_range // 2 + 1)):
            coor_temp = (x % size_x, y % size_y)
            if coor_temp != coor:
                fields_in_range.append(coor_temp)

    # calculate whether those field are new fields or not
    for i in fields_in_range:
        for y in range(size_y):
            for x in range(size_x):
                temp = map[y][x]
                if type(temp) == Node:
                    if temp.coor == i:
                        for ii in range(len(fields_in_range)):
                            if fields_in_range[ii] == temp.coor:
                                fields_in_range[ii] = 0
                else:
                    pass

    fields_in_range = [x for x in fields_in_range if x != 0]

    return len(fields_in_range)


def reverse_command(prev_command):
    if prev_command == "up":
        return "down"
    elif prev_command == "down":
        return "up"
    elif prev_command == "left":
        return "right"
    elif prev_command == "right":
        return "left"

def from_id_width(id, width):
    return (id % width, id // width)


def draw_tile(graph, id, style, width):
    r = "."
    if 'number' in style and id in style['number']: r = "%d" % style['number'][id]
    if 'point_to' in style and style['point_to'].get(id, None) is not None:
        (x1, y1) = id
        (x2, y2) = style['point_to'][id]
        if x2 == x1 + 1: r = "\u2192"
        if x2 == x1 - 1: r = "\u2190"
        if y2 == y1 + 1: r = "\u2193"
        if y2 == y1 - 1: r = "\u2191"
    if 'start' in style and id == style['start']: r = "A"
    if 'goal' in style and id == style['goal']: r = "Z"
    if 'path' in style and id in style['path']: r = "@"
    if id in graph.walls: r = "#" * width
    return r

def draw_grid(graph, width=2, **style):
    for y in range(graph.height):
        for x in range(graph.width):
            print("%%-%ds" % width % draw_tile(graph, (x, y), style, width), end="")
        print()

class SquareGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = []

    def in_bounds(self, id):
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height

    def passable(self, id):
        return id not in self.walls

    def neighbors(self, id):
        (x, y) = id
        results = [(x + 1, y), (x, y - 1), (x - 1, y), (x, y + 1)]
        results2 = []
        for i in results:
            results2.append((i[0] % size_x, i[1] % size_y))
        # if (x + y) % 2 == 0: results.reverse() # aesthetics
        # results = filter(self.in_bounds, results)
        # results = filter(self.passable, results)
        return results2


class GridWithWeights(SquareGrid):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.weights = {}

    def cost(self, from_node, to_node):
        return self.weights.get(to_node, 1)

class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]

def reconstruct_path(came_from, start, goal):
    current = goal
    path = [current]
    while current != start:
        current = came_from[current]
        path.append(current)
    path.append(start)  # optional
    path.reverse()  # optional
    return path


def heuristic(goal, neigb):
    (x1, y1) = goal
    (x2, y2) = neigb

    # Ueber die Grenze x und y wenn Feldanzahl gerade
    x_abs = abs(x1 - x2)
    y_abs = abs(y1 - y2)
    if size_x % 2 == 0:
        if neigb[0] < size_x // 2 and goal[0] < size_x // 2:
            pass

        elif neigb[0] < size_x // 2 and not goal[0] < size_x // 2:
            x_temp = neigb[0] + (size_x - 1 - goal[0]) + 1
            x_abs = min(x_abs, x_temp)

        elif neigb[0] >= size_x // 2 and goal[0] >= size_x // 2:
            pass

        elif neigb[0] >= size_x // 2 and not goal[0] >= size_x // 2:
            x_temp = goal[0] + (size_x - 1 - neigb[0]) + 1
            x_abs = min(x_abs, x_temp)
    else:
        if neigb[0] < size_x // 2 and goal[0] < size_x // 2:
            pass

        elif neigb[0] < size_x // 2 and not goal[0] < size_x // 2:
            x_temp = neigb[0] + (size_x - 1 - goal[0]) + 1
            x_abs = min(x_abs, x_temp)


        elif neigb[0] > size_x // 2 and goal[0] > size_x // 2:
            pass

        elif neigb[0] > size_x // 2 and not goal[0] > size_x // 2:
            x_temp = goal[0] + (size_x - 1 - neigb[0]) + 1
            x_abs = min(x_abs, x_temp)

        else:
            pass

    if size_y % 2 == 0:
        if neigb[1] < size_y // 2 and goal[1] < size_y // 2:
            pass

        elif neigb[1] < size_y // 2 and not goal[1] < size_y // 2:
            y_temp = neigb[1] + (size_y - 1 - goal[1]) + 1
            y_abs = min(y_abs, y_temp)

        elif neigb[1] >= size_y // 2 and goal[1] >= size_y // 2:
            pass

        elif neigb[1] >= size_y // 2 and not goal[1] >= size_y // 2:
            y_temp = goal[1] + (size_y - 1 - neigb[1]) + 1
            y_abs = min(y_abs, y_temp)

    else:
        if neigb[1] < size_y // 2 and goal[1] < size_y // 2:
            pass

        elif neigb[1] < size_y // 2 and not goal[1] < size_y // 2:
            y_temp = neigb[1] + (size_y - 1 - goal[1]) + 1
            y_abs = min(y_abs, y_temp)

        elif neigb[1] > size_y // 2 and goal[1] > size_y // 2:
            pass

        elif neigb[1] > size_y // 2 and not goal[1] > size_y // 2:
            y_temp = goal[1] + (size_y - 1 - neigb[1]) + 1
            y_abs = min(y_abs, y_temp)

        else:
            pass

    return x_abs + y_abs


def a_star_search(graph, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()
        x = current[0] % size_x
        y = current[1] % size_y
        current = (x, y)

        if current == goal:
            break

        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current

    return came_from, cost_so_far

def main(argv):
    """ init-Method

            Method acts as the Constructor initiates all variables

            @:param argv: Arguments passed by the User
    """
    global ip, port, size_x, size_y
    global timeout
    timeout = 0.5
    if len(argv) == 0:
        raise ValueError("Please specify port as in >>python client-k1.py -p 5050 -s 10<<")
    # Set port globally
    try:
        ip = argv[1]
        port = int(argv[3])
        size_x = int(argv[5])
        size_y = int(argv[7])

    except Exception as e:
        raise ValueError("Invalid Arguments")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as clientsocket:
        try:
            clientsocket.connect((ip, port))
            name = "test"
            clientsocket.send(name.encode())
            data = clientsocket.recv(1024).decode()
            prev_command = None
            map = [[0 for x in range(size_x)] for y in range(size_y)]
            prev_x = 0
            prev_y = 0
            steps = 0
            graph = GridWithWeights(size_x, size_y)
            have_bomb = False
            while True:
                data = clientsocket.recv(1024).decode()
                if "You" in data or "Draw" in data:
                    print("Steps needed: ", steps)
                    sys.exit(0)
                    # bring in correct 2 dimensional form
                if len(data) % 3 == 0:
                    # it is forest or start point
                    temp_size = 3
				elif len(data) % 5 == 0:
                    temp_size = 5

                 elif len(data) % 7 == 0:
                        temp_size = 7

                    fields = [[0 for x in range(temp_size)] for y in range(temp_size)]
                    for y in range(temp_size):
                        temp = data[y * temp_size: (y * temp_size) + temp_size]
                        for x in range(0, temp_size):
                            print(x, "stelle")
                            print(temp_size)
                            val = temp[x]
                            fields[y][x] = Node(x, y, val)
                    for i in fields:
                        print(i.__repr__())
                    if steps == 0:
                        pass
                    else:
                        if prev_command == "up":
                            prev_y -= 1
                        elif prev_command == "down":
                            prev_y += 1
                        elif prev_command == "left":
                            prev_x -= 1
                        elif prev_command == "right":
                            prev_x += 1
                    prev_x = prev_x % size_x
                    prev_y = prev_y % size_y
                    for y in range(0, len(fields)):
                        for x in range(0, len(fields)):
                            node_temp = fields[y][x]
                            node_temp.coor = ((x - len(fields) // 2 + prev_x) % size_x, (y - len(fields) // 2 + prev_y) % size_y)
                            if "C" in node_temp.value and node_temp.coor != (0,0):
                                node_temp.value = "EC"
                                print("enemy castle found")
                            map[(y - len(fields) // 2 + prev_y) % size_x][(x - len(fields) // 2 + prev_x) % size_y] = node_temp
                    map[prev_y][prev_x].visited = True
                    for y in range(size_y):
                        for x in range(size_x):
                            node = map[y][x]
                            if type(node) == Node:
                                if not node.passable:
                                    graph.walls.append(node.coor)
                                graph.weights[node.coor] = node.weight
                    for i in map:
                        print(i)
                    bomb_node = None
                    queue = PriorityQueue()
                    for y in range(size_y):
                        for x in range(size_x):
                            node = map[y][x]
                            if type(node) == Node:
                                if "B" in node.value and have_bomb == False:
                                    queue.put(node, -1000000000)
                                    bomb_node = node.coor
                                elif "EC" in node.value and have_bomb == True:
                                    queue.put(node, -1000000000)
                                else:
                                    poss_fields = calc_possible_new_fields(node.value, node.coor, map)
                                    way_to_field = heuristic(node.coor, (prev_x, prev_y))
                                    queue.put(node, (poss_fields * -1) + way_to_field)
                                    print(poss_fields, "for field:", node)
                                    print("way to field:", way_to_field)
                                    print()
                    next_node = queue.get()
                    start = (prev_x, prev_y)
                    goal = next_node.coor
                    if start == bomb_node:
                        bomb_node = start
                        have_bomb = True
                        queue = PriorityQueue()
                        for y in range(size_y):
                            for x in range(size_x):
                                node = map[y][x]
                                if type(node) == Node:
                                    if "B" in node.value and have_bomb == False:
                                        queue.put(node, -1000000000)
                                        bomb_node = node.coor
                                    elif "EC" in node.value and have_bomb == True:
                                        queue.put(node, -1000000000)
                                    else:
                                        poss_fields = calc_possible_new_fields(node.value, node.coor, map)
                                        way_to_field = heuristic(node.coor, (prev_x, prev_y))
                                        queue.put(node, poss_fields * -1)
                        next_node = queue.get()
                        start = (prev_x, prev_y)
                        goal = next_node.coor
                    came_from, cost_so_far = a_star_search(graph, start, goal)
                    draw_grid(graph, width=3, point_to=came_from, start=start, goal=goal)
                    draw_grid(graph, width=3, number=cost_so_far, start=start, goal=(x, y))
                    path = reconstruct_path(came_from, start=start, goal=goal)[2:]
                    draw_grid(graph, width=3, path=path)
                    commands = create_commands(path, start)
                    clientsocket.send(commands[0].encode())
                    prev_command = commands[0]
                    time.sleep(timeout)
                    steps += 1
        except socket.error as serr:
            print(serr.strerror)
if __name__ == "__main__":
    main(sys.argv[1:])