from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement
from model import DeliveryModel
from agent import DeliveryBot, Sender, Receiver

# Define custom CSS for better styling
css = """
<style>
    .simulation-container {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        max-width: 1200px;
        margin: 0 auto;
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stats-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .stat-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        flex: 1;
        min-width: 200px;
        border-left: 4px solid #3498db;
    }
    
    .stat-card h3 {
        margin-top: 0;
        color: #2c3e50;
        font-size: 16px;
    }
    
    .stat-value {
        font-size: 24px;
        font-weight: bold;
        color: #3498db;
    }
    
    .stat-label {
        font-size: 14px;
        color: #7f8c8d;
    }
    
    .efficiency-meter {
        height: 8px;
        width: 100%;
        background-color: #ecf0f1;
        border-radius: 4px;
        margin-top: 8px;
        overflow: hidden;
    }
    
    .efficiency-fill {
        height: 100%;
        background: linear-gradient(90deg, #2ecc71, #3498db);
        border-radius: 4px;
        transition: width 0.5s ease;
    }
    
    .controls-container {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    .controls-title {
        color: #2c3e50;
        margin-top: 0;
        border-bottom: 1px solid #ecf0f1;
        padding-bottom: 10px;
    }
    
    .canvas-container {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
</style>
"""

def agent_portrayal(agent):
    portrayal = {}
    
    if isinstance(agent, DeliveryBot):
        # Different icons based on bot state
        if agent.pos == (grid_width // 2, grid_height // 2):
            portrayal["Shape"] = "assets/distribution.png"
            portrayal["scale"] = 0.9
        elif agent.has_package:
            portrayal["Shape"] = "assets/bot_loaded.png"
            portrayal["scale"] = 0.9
        else:
            portrayal["Shape"] = "assets/bot.png"
            portrayal["scale"] = 0.9
        
        portrayal["Layer"] = 2
        portrayal["text"] = f"{agent.unique_id}"
        portrayal["text_color"] = "White"
        
    elif isinstance(agent, Sender):
        portrayal["Shape"] = "assets/restaurant.png"
        portrayal["scale"] = 1.0
        portrayal["Layer"] = 0
        portrayal["text"] = f"S{agent.unique_id}"
        portrayal["text_color"] = "#2c3e50"
        
    elif isinstance(agent, Receiver):
        portrayal["Shape"] = "assets/house.png"
        portrayal["scale"] = 1.0
        portrayal["Layer"] = 1
        portrayal["text"] = f"R{agent.unique_id}"
        portrayal["text_color"] = "#2c3e50"
        
    return portrayal

# Increase grid size and adjust canvas size
grid_width = 20
grid_height = 20
canvas = CanvasGrid(agent_portrayal, grid_width, grid_height, 800, 800)

class DeliveryHeader(TextElement):
    def render(self, model):
        return f"""
        {css}
        <div class="simulation-container">
            <h2 style="text-align: center; color: #3498db;">Smart Delivery Simulation Dashboard</h2>
            <p style="text-align: center; color: #7f8c8d;">Real-time monitoring of autonomous delivery network</p>
        """

class DeliveryStats(TextElement):
    def render(self, model):
        # Calculate bot utilization
        active_bots = sum(1 for agent in model.schedule.agents if isinstance(agent, DeliveryBot) and agent.has_package)
        total_bots = sum(1 for agent in model.schedule.agents if isinstance(agent, DeliveryBot))
        utilization = (active_bots / max(1, total_bots)) * 100
        
        # Calculate efficiency if there are completed deliveries
        efficiency = 0
        avg_distance = 0
        if model.completed_deliveries > 0:
            avg_distance = model.total_distance_traveled / max(1, model.completed_deliveries)
            # Lower is better, so we invert the percentage (capped at 100%)
            theoretical_min = 10  # Assume a theoretical minimum average distance
            efficiency = min(100, max(0, 100 - (avg_distance - theoretical_min) * 2))
        
        return f"""
        <div class="stats-container">
            <div class="stat-card">
                <h3>📦 Deliveries</h3>
                <div class="stat-value">{model.completed_deliveries}</div>
                <div class="stat-label">Completed</div>
                <div class="stat-value" style="color: #e74c3c;">{model.pending_deliveries}</div>
                <div class="stat-label">Pending</div>
            </div>
            
            <div class="stat-card">
                <h3>🚚 Fleet Status</h3>
                <div class="stat-value">{active_bots}</div>
                <div class="stat-label">Active Bots</div>
                <div class="stat-value" style="color: #7f8c8d;">{total_bots - active_bots}</div>
                <div class="stat-label">Idle Bots</div>
            </div>
            
            <div class="stat-card">
                <h3>📏 Distance</h3>
                <div class="stat-value">{model.total_distance_traveled}</div>
                <div class="stat-label">Total Units</div>
                <div class="stat-value" style="font-size: 18px;">{round(avg_distance, 2) if model.completed_deliveries > 0 else 0}</div>
                <div class="stat-label">Avg. Per Delivery</div>
            </div>
            
            <div class="stat-card">
                <h3>⚡ Performance</h3>
                <div class="stat-value">{round(efficiency, 1)}%</div>
                <div class="stat-label">Routing Efficiency</div>
                <div class="efficiency-meter">
                    <div class="efficiency-fill" style="width: {efficiency}%;"></div>
                </div>
                <div class="stat-value" style="font-size: 18px; margin-top: 10px;">{round(utilization, 1)}%</div>
                <div class="stat-label">Bot Utilization</div>
                <div class="efficiency-meter">
                    <div class="efficiency-fill" style="width: {utilization}%;"></div>
                </div>
            </div>
        </div>
        """

class DeliveryFooter(TextElement):
    def render(self, model):
        return """
        </div>
        """

# Create header, stats and footer elements
header = DeliveryHeader()
stats = DeliveryStats()
footer = DeliveryFooter()

# Add all visualization elements to the server
server = ModularServer(
    DeliveryModel,
    [header, stats, canvas, footer],
    "Smart Delivery Simulation",
    {
        "width": grid_width,
        "height": grid_height,
        "num_bots": UserSettableParameter("slider", "Delivery Bots", 4, 1, 10, 1),
        "num_senders": UserSettableParameter("slider", "Senders", 3, 1, 10, 1),
        "num_receivers": UserSettableParameter("slider", "Receivers", 3, 1, 10, 1),
    }
)

# Set server port
server.port = 8525