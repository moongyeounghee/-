import os
import shutil

# This script moves unnecessary files and scripts into an '_archive' directory
# to leave only the core deployment files required by Streamlit App.

workspace_dir = '.'
archive_dir = os.path.join(workspace_dir, '_archive')

# Exclude list: What NOT to move (Deployment Whitelist)
keep_files = {
    'app.py',
    'requirements.txt',
    'dynamic_poi_env.py',
    'firebase_sync.py',
    'rl_engine.py',
    'departure_congestion_api.py',
    'departure_flight_api.py',
    'arrival_flight_api.py',
    'parking_api.py',
    'bus_api.py',
    'taxi_api.py',
    'railroad_api.py',
    'facilities_api.py',
    'opensky_api.py',
    'shuttle_bus_api.py',
    'dynamic_env_data.pkl',
    'dynamic_q_table.pkl',
    'q_table.pkl',
    'dummy_congestion.json',
    'dummy_flight.json',
    'facilities.json',
    'facilities_cache.json',
    'share_codes.json',
    'cleanup_workspace.py', # keep the cleanup script itself
}

keep_dirs = {
    '.git',
    '.streamlit',
    '__pycache__',
    '_archive'
}

if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

moved_count = 0
for item in os.listdir(workspace_dir):
    item_path = os.path.join(workspace_dir, item)
    
    # Don't touch required dirs
    if os.path.isdir(item_path):
        if item in keep_dirs:
            continue
        # If it's a directory not in keep_dirs, move it (e.g. 정리본2)
        try:
            shutil.move(item_path, os.path.join(archive_dir, item))
            moved_count += 1
            print(f"Moved directory: {item}")
        except Exception as e:
            print(f"Could not move {item}: {e}")
            
    # Move files not in keep_files list
    if os.path.isfile(item_path):
        # Exclude hidden files like .gitignore
        if item.startswith('.'):
            continue
            
        if item not in keep_files:
            try:
                shutil.move(item_path, os.path.join(archive_dir, item))
                moved_count += 1
                print(f"Moved file: {item}")
            except Exception as e:
                print(f"Could not move {item}: {e}")

print(f"Cleanup complete! Moved {moved_count} items to _archive.")
