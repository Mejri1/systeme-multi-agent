from mesa import Agent
import random
from collections import deque
import heapq  # Required for A* priority queue

class DeliveryBot(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.has_package = False
        self.current_sender = None
        self.current_receiver = None
        self.busy = False
        self.path = []  # Stores calculated path
        self.distance_traveled = 0  # Track distance traveled by this bot

    def step(self):
        if not self.busy:
            self.find_assignment()
            
        if self.busy:
            if not self.has_package:
                self.handle_package_pickup()
            else:
                self.handle_delivery()

    def find_assignment(self):
        sender = self.find_unassigned_sender()
        if sender:
            self.current_sender = sender
            self.current_receiver = sender.receiver
            sender.assigned = True
            self.busy = True
            self.path = self.a_star_pathfinding(self.current_sender.pos)
            print(f"📦 Bot {self.unique_id} assigned to {sender.unique_id}")

    def handle_package_pickup(self):
        if self.pos == self.current_sender.pos:
            self.has_package = True
            self.path = self.a_star_pathfinding(self.current_receiver.pos)
            print(f"🚚 Bot {self.unique_id} picked up package")
        else:
            self.follow_path()

    def handle_delivery(self):
        if self.pos == self.current_receiver.pos:
            self.complete_delivery()
        else:
            self.follow_path()

    def complete_delivery(self):
        self.has_package = False
        self.busy = False
        self.current_sender.assigned = False
        self.model.total_deliveries += 1
        print(f"✅ Bot {self.unique_id} delivered (Total: {self.model.total_deliveries})")
        self.current_sender = None
        self.current_receiver = None
        self.path = []

    def find_unassigned_sender(self):
        available = [s for s in self.model.senders if not s.assigned]
        return random.choice(available) if available else None

    def a_star_pathfinding(self, target_pos):
        """A* pathfinding with obstacle avoidance"""
        def heuristic(a, b):
            # Manhattan distance heuristic
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        start = self.pos
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, target_pos)}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == target_pos:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # Reverse path

            for neighbor in self.model.grid.get_neighborhood(current, moore=True, include_center=False):
                if not self.model.grid.is_cell_empty(neighbor) and neighbor != target_pos:
                    continue

                tentative_g_score = g_score[current] + 1  # Assume uniform cost
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, target_pos)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # No path found

    def follow_path(self):
        if self.path:
            next_pos = self.path[0]
            if self.model.grid.is_cell_empty(next_pos) or next_pos in [self.current_receiver.pos, self.current_sender.pos]:
                self.model.grid.move_agent(self, next_pos)
                self.path = self.path[1:]
                # Update distance traveled
                self.distance_traveled += 1
                self.model.total_distance_traveled += 1
        else:
            # Recalculate path if stuck
            target = self.current_receiver.pos if self.has_package else self.current_sender.pos
            self.path = self.a_star_pathfinding(target)
            if not self.path:
                print(f"⚠️ Bot {self.unique_id} can't find path!")

# Sender and Receiver classes remain unchanged
class Sender(Agent):
    def __init__(self, unique_id, model, receiver):
        super().__init__(unique_id, model)
        self.receiver = receiver
        self.assigned = False
        self.static = False  # Default to non-static unless explicitly set

class Receiver(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.static = False  # Default to non-static unless explicitly set