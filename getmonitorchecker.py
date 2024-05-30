from screeninfo import get_monitors

def get_monitor_info():
    
    monitors_info = []
    monitors = get_monitors()
    
    for i, monitor in enumerate(monitors):
        monitor_info = {
            "id": i,
            "name": monitor.name,
            "x": monitor.x,
            "y": monitor.y,
            "width": monitor.width,
            "height": monitor.height
        }
        monitors_info.append(monitor_info)
    
    return monitors_info

monitor_details = get_monitor_info()
for monitor in monitor_details:
    print(monitor)




# def debug_get_monitors():
#     try:
#         monitors = get_monitors()
#         if not monitors:
#             print("No monitors found.")
#             return
        
#         for i, monitor in enumerate(monitors):
#             print(f"Monitor {i}:")
#             print(f"  Name: {monitor.name}")

#             print(f"  X: {monitor.x}")
#             print(f"  Y: {monitor.y}")

#             print(f"  Width: {monitor.width}")
#             print(f"  Height: {monitor.height}")

#     except Exception as e:
#         print(f"Error detecting monitors: {e}")

# debug_get_monitors()