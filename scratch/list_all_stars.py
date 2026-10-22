import sys
sys.path.insert(0, r"c:\Users\karan\starlink")
import json, glob
from theme import map_star_coordinates
from engine.level_loader import load_level_from_json

for path in sorted(glob.glob("levels/*.json")):
    data = load_level_from_json(path)
    stars = data['stars']
    print(f"\n--- {data['name']} ({path}) ---")
    for s in stars:
        mx, my = map_star_coordinates(s.x, s.y, stars)
        print(f"  ID {s.id}: '{s.name}' mapped to ({mx}, {my})")

