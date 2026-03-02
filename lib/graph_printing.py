import plotille
from datetime import datetime


def print_graph(y_data: list[float], date_from: datetime = None, date_to: datetime = None, height: int = 12, width: int = 120):
    """
    Print a console graph using plotille with exact points and lines.
    
    Args:
        y_data: List of Y values to plot
        date_from: Start date for the data range
        date_to: End date for the data range
        height: Height of the graph in lines
        width: Width of the graph in characters
    """
    if not y_data or len(y_data) == 0:
        print("No data to plot")
        return
    
    if date_from and date_to:
        print(f"Period: {date_from.strftime('%Y-%m-%d')} → {date_to.strftime('%Y-%m-%d')}")
    
    fig = plotille.Figure()
    fig.width = width
    fig.height = height
    fig.color_mode = 'byte'
    
    x_values = list(range(len(y_data)))
    fig.plot(x_values, y_data, lc=25, interp=None, marker='●')
    
    print(fig.show(legend=False))
    print(f"Min: {min(y_data):.4f}, Max: {max(y_data):.4f}, Count: {len(y_data)}\n")
