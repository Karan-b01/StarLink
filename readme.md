# 🚀 StarLink — Constellation Weaver

> A space-themed puzzle game where the algorithms **are** the gameplay.

StarLink is a Data Structures & Algorithms project built in Python and Pygame. The player acts as a *Constellation Weaver*: connect every star into a single network using the least possible energy, without creating cycles. Behind the scenes, Union-Find validates each move, a stack powers undo, and Kruskal's algorithm computes the optimal solution the player is scored against.

---

## Table of Contents

1. [Overview](#overview)
2. [How to Play](#how-to-play)
3. [DSA Concepts Used](#dsa-concepts-used)
4. [Complexity Analysis](#complexity-analysis)
5. [Features](#features)
6. [Sectors and Difficulty](#sectors-and-difficulty)
7. [Project Structure](#project-structure)
8. [Installation and Running](#installation-and-running)
9. [Testing](#testing)
10. [Development Roadmap](#development-roadmap)
11. [Team](#team)
12. [Limitations and Future Work](#limitations-and-future-work)
13. [Classroom Demo Walkthrough](#classroom-demo-walkthrough)

---

## Overview

| | |
|---|---|
| **Genre** | Puzzle / educational strategy |
| **Language** | Python 3.10+ |
| **Libraries** | Pygame, NumPy |
| **Core idea** | Build a Minimum Spanning Tree by hand and compare it with the optimal one |
| **Context** | Data Structures & Algorithms assignment |

**Design principle:** the DSA logic is not decoration added to a game. Each concept maps directly to a mechanic:

| Concept | Game mechanic |
|---|---|
| Graph | Stars and connections form the constellation |
| Union-Find | Cycle prevention |
| Kruskal's algorithm | The optimal strategy used for scoring and the solution replay |
| Stack | Undo / redo |

---

## How to Play

1. Each level shows a set of **stars** (vertices) and possible **connections** (weighted edges). The weight is the energy cost.
2. Select two stars to connect them. The energy cost is deducted from your meter.
3. If the connection would form a **cycle**, it is rejected and flagged in red.
4. Made a mistake? **Undo** your last connection.
5. When all stars are connected, your network cost is compared against the optimal MST and you earn up to five stars.
6. If no affordable route can join the remaining star groups, the sector ends with Retry and Next World options.

### Controls

| Input | Action |
|---|---|
| **Left click** Star A, then Star B | Build a connection between the two stars |
| **Z** | Undo the last connection (refunds energy) |
| **Y** | Redo the previously undone connection |
| **K** | Toggle the Kruskal solver to watch the algorithm evaluate edges step by step |
| **N** | Advance to the next world sector |
| **R** | Reset the current sector |
| **M** | Toggle sound effects |
| **P** | Toggle the ambient music loop |

The same actions are available on screen. All ten sectors are available from the Worlds picker, with Easy, Medium, and Hard challenges.

### Scoring

| Stars | Condition |
|---|---|
| ★★★★★ | Exact match with the optimal MST cost |
| ★★★★☆ | Up to 2 energy above optimal |
| ★★★☆☆ | 3–4 energy above optimal |
| ★★☆☆☆ | 5–6 energy above optimal |
| ★☆☆☆☆ | Completed with a larger cost difference |

---

## DSA Concepts Used

| Concept | Where it is used | File |
|---|---|---|
| Graph (weighted, undirected) | Level representation: stars as vertices, connections as edges | `dsa/graph.py` |
| Union-Find (path compression + union by rank) | Detects and prevents cycles on every move | `dsa/union_find.py` |
| Kruskal's algorithm | Computes the optimal MST cost and drives the step-by-step solver | `dsa/mst.py` |
| Sorting | Edges sorted by weight for Kruskal | `dsa/mst.py` |
| Prim's algorithm | Independent MST computation, cross-checked against Kruskal | `dsa/mst.py` |
| BFS | Verifies the final network is connected | `dsa/graph.py` |
| Stack (undo and redo) | Undo / redo history | `dsa/history_stack.py` |
| Shortest path (Dijkstra) | Independent shortest-path implementation for route analysis | `dsa/dijkstra.py` |
| Hash map (dictionary) | Fast star and level lookup; Union-Find parent and rank tables | across modules |

All core algorithms are implemented from scratch, without external graph libraries.

---

## Complexity Analysis

Let **V** be the number of stars and **E** the number of connections.

| Operation | Time | Space |
|---|---|---|
| Kruskal's MST | O(E log E) | O(V + E) |
| Prim's MST (binary heap) | O(E log V) | O(V + E) |
| BFS connectivity check | O(V + E) | O(V) |
| Union-Find `find` / `union` | Amortized O(α(V)), effectively constant | O(V) |
| Edge sorting | O(E log E) | O(E) |
| Stack push / pop (undo) | O(1) | O(moves) |
| Dijkstra (binary heap) | O((V + E) log V) | O(V) |

---

## Features

**Gameplay**
- Cycle-detection warning on invalid connections
- Energy meter with efficiency-based scoring
- Undo system backed by a stack
- Five-star rating compared against the true MST
- Retry and next-sector result screens when a network is completed or energy runs out
- Step-by-step **Kruskal solver replay** showing which edges are accepted or rejected, and why

**Visuals and audio**
- Procedurally drawn galaxy, drifting star layers, animated star coronas, orbital motes, and traveling link pulses
- Five-sector campaign with Easy, Medium, and Hard difficulty progression
- Procedurally synthesized ambient space music and separate sound effects (no audio files needed)

---

## Sectors and Difficulty

| Sector | Theme | Difficulty |
|---|---|---|
| 1 | Alpha Centauri | Easy: learn weighted links and cycle prevention |
| 2 | Orion Star Nursery | Easy: use Power and Energy stars |
| 3 | Cygnus Event Horizon | Medium: unstable links and a tighter budget |
| 4 | Pleiades Seven Sisters | Medium: more routes and special-star planning |
| 5 | Andromeda Great Spiral | Hard: larger network and unstable routes |

---
## 🛠️ Project Structure

```text
starlink/
├── dsa/                     # Pure DSA modules (headless execution)
│   ├── union_find.py        # DSU with Path Compression + Union by Rank
│   ├── mst.py               # Kruskal generator & Prim's min-heap MST
│   ├── graph.py             # BFS graph connectivity verifier
│   ├── history_stack.py     # Dual-stack Undo / Redo engine
│   └── dijkstra.py          # Shortest path priority queue algorithm
├── engine/                  # Game rules, level loading & audio
│   ├── game_state.py        # Rule validation & special star logic
│   ├── level_loader.py      # JSON level parser & procedural generator
│   └── sound_engine.py      # Procedural sound synthesis (NumPy)
├── visual/                  # Rendering components
│   ├── starfield.py         # 3-layer parallax starfield
│   ├── ui_hud.py            # Sector HUD, roster, algorithm inspector & controls
│   ├── celestial_renderer.py # Star coronas, orbital motes & laser corridors
│   ├── ui.py                # Reusable energy bar and UI widgets
│   └── solver_animator.py   # Step-by-step Kruskal visualizer
├── levels/                  # Curated world JSON data
│   ├── world1.json          # Solar System (Tutorial)
│   ├── world2.json          # Nebula (Energy & Power Stars)
│   ├── world3.json          # Black Hole (Unstable Stars & Tight Budget)
│   ├── world4.json          # Pleiades (Medium challenge)
│   └── world5.json          # Andromeda (Hard challenge)
├── test_dsa.py              # Automated test runner for graph algorithms
├── main.py                  # Pygame application loop & entry point
└── requirements.txt         # Project dependencies


**Architecture rule:** `dsa/` never imports Pygame. This keeps the algorithms independently testable and easy to explain.

---

## Installation and Running

**Requirements:** Python 3.10 or newer.

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/starlink-constellation-weaver.git
cd starlink-constellation-weaver
```

### 2. Set up a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv starlink_env
.\starlink_env\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv starlink_env
source starlink_env/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the game

```bash
python main.py
```

> If PowerShell blocks the activation script, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

---

## Testing

Run the test suite to verify the algorithms independently of the graphics loop:

```bash
python test_dsa.py
```

It executes five core validations and prints a pass confirmation for each:

1. Union-Find cycle detection
2. MST parity between Kruskal and Prim
3. BFS connectivity
4. Undo / redo stacks
5. Dijkstra shortest path

---

## Development Roadmap

- [x] **Sprint 1:** Core DSA engine and unit test suite
- [x] **Sprint 2:** Level data pipeline (JSON loader, special stars, procedural generator)
- [x] **Sprint 3:** Pygame game loop, animated galaxy, solver replay, and HUD
- [x] **Sprint 4:** Five-sector campaign, difficulty progression, result flow, and scoring
- [ ] **Submission prep:** Fill in team/course details and capture a short gameplay demo

*Tick off the boxes as you finish each sprint.*

---

## Team

| Name | Role |
|---|---|
| *Your name* | *e.g. Core DSA and game logic* |
| *Teammate name* | *e.g. Visuals and audio* |

**Course / Institution:** *add here*

---

## Limitations and Future Work

- Special stars (Energy, Power, Unstable) can be expanded with richer mechanics.
- A level editor and online leaderboard would be natural extensions.
- A hint system based on Prim's algorithm with a min-heap.

---

## Classroom Demo Walkthrough

1. Point out that stars are vertices and corridors are weighted edges.
2. Try to add a cycle and explain how Union-Find rejects it.
3. Run the Kruskal replay: edges are considered in increasing weight order and accepted only when they join separate components.
4. Use undo and redo to show how the action stack restores moves and energy.
5. Finish with a low-cost spanning tree and explain the five-star score against the computed MST baseline.
6. Visit a later sector to demonstrate Power, Energy, and Unstable star mechanics.

---

## License

*Add a license if you plan to publish the repository (for example MIT), or state that it is submitted for academic purposes.*
