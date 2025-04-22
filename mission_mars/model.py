from mesa import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from agent import DeliveryBot, Sender, Receiver
import random

class DeliveryModel(Model):
    def __init__(self, width=20, height=20, num_bots=3, num_senders=2, num_receivers=2):  # Updated default grid size
        self.width = width
        self.height = height
        self.num_bots = num_bots
        self.num_senders = num_senders
        self.num_receivers = num_receivers

        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.running = True  # Required by Mesa for visualization

        self.total_deliveries = 0  # Delivery counter
        self.completed_deliveries = 0  # Track completed deliveries
        self.pending_deliveries = num_senders  # Initially, all senders have pending deliveries

        self.senders = []
        self.receivers = []

        self.current_id = 0  # Initialize current_id for unique agent IDs

        self.total_distance_traveled = 0  # Track total distance traveled by all bots
        self.center_pos = (self.width // 2, self.height // 2)  # Center position

        # Place receivers (e.g., houses) at random positions
        for _ in range(self.num_receivers):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            receiver = Receiver(self.next_id(), self)
            receiver.static = True  # Mark as static
            self.grid.place_agent(receiver, (x, y))
            self.receivers.append(receiver)

        # Place senders (e.g., restaurants) at random positions
        for i in range(self.num_senders):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            linked_receiver = self.receivers[i % len(self.receivers)]  # Map to receivers
            sender = Sender(self.next_id(), self, linked_receiver)
            sender.static = True  # Mark as static
            self.grid.place_agent(sender, (x, y))
            self.senders.append(sender)

        # Place all delivery bots at the center of the grid
        for _ in range(self.num_bots):
            bot = DeliveryBot(self.next_id(), self)
            self.grid.place_agent(bot, self.center_pos)
            self.schedule.add(bot)

        # Keep the center occupied with a placeholder agent
        self.center_placeholder = Receiver(self.next_id(), self)
        self.grid.place_agent(self.center_placeholder, self.center_pos)

    def step(self):
        # Ensure static agents are not moved
        for sender in self.senders:
            self.grid.place_agent(sender, sender.pos)
        for receiver in self.receivers:
            self.grid.place_agent(receiver, receiver.pos)

        self.schedule.step()
        # Update delivery statistics
        self.completed_deliveries = self.total_deliveries
        self.pending_deliveries = sum(1 for sender in self.senders if sender.assigned or not sender.assigned)
        # Calculate average distance traveled
        self.average_distance_traveled = (
            self.total_distance_traveled / self.num_bots if self.num_bots > 0 else 0
        )
