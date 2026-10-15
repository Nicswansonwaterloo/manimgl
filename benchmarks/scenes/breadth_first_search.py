from manimlib import *
from benchmarks.support.algorithms import breadth_first_events


class BreadthFirstSearchGraph(Scene):
    """15s: real FIFO traversal of 336 nodes, live queue, 690 deforming edges and shortest path."""
    default_camera_config = dict(background_color="#101C2B")

    def construct(self):
        rows, cols = 14, 24
        homes = np.array([[(col / (cols - 1) - 0.5) * 8.99 - 1.2,
                           (row / (rows - 1) - 0.5) * 5.1, 0]
                          for row in range(rows) for col in range(cols)])
        pairs = [(r * cols + c, r * cols + c + 1) for r in range(rows) for c in range(cols - 1)]
        pairs += [(r * cols + c, (r + 1) * cols + c) for r in range(rows - 1) for c in range(cols)]
        pairs += [(r * cols + c, (r + 1) * cols + c + 1)
                  for r in range(0, rows - 1, 2) for c in range(0, cols - 1, 3)]
        adjacency = [[] for _ in homes]
        edge_index = {}
        for index, (a, b) in enumerate(pairs):
            adjacency[a].append(b)
            adjacency[b].append(a)
            edge_index[min(a, b), max(a, b)] = index
        start, goal = (rows // 2 - 1) * cols, (rows // 2) * cols + cols - 1
        events, parents, distances = breadth_first_events(adjacency, start)
        edges = VGroup(*[Line(homes[a], homes[b], stroke_color=GREY_D, stroke_width=1)
                         for a, b in pairs])
        nodes = VGroup(*[Dot(point, radius=0.035, fill_color=GREY_B) for point in homes])
        title = Text(f"BREADTH-FIRST SEARCH · {len(homes)} nodes", font="sans-serif", font_size=26).to_edge(UP)
        panel_title = Text("FIFO frontier", font="sans-serif", font_size=24).move_to([5.2, 2.5, 0])
        queue_digits = VGroup(*[Integer(0, font_size=19, color=TEAL).move_to([5.2, 1.9 - i * 0.3, 0])
                               for i in range(10)])
        visited_label = Text("Visited", font="sans-serif", font_size=20).move_to([5.2, -1.6, 0])
        visited = Integer(0, font_size=28).move_to([5.2, -2.1, 0])
        halo = GlowDot(homes[start], radius=0.11, color=YELLOW)
        graph = VGroup(edges, nodes)
        self.add(title, panel_title, queue_digits, visited_label, visited)
        self.play(FadeIn(graph), run_time=1.5)
        progress = ValueTracker(0)
        state = dict(last=-1, active=None)
        positions = homes.copy()
        palette = color_gradient([BLUE, TEAL, GREEN, GOLD], int(distances.max()) + 1)

        def update_layout(_, dt):
            positions[:, 0] = homes[:, 0] + 0.035 * np.sin(2 * self.time + homes[:, 1] * 2)
            positions[:, 1] = homes[:, 1] + 0.035 * np.cos(self.time + homes[:, 0] * 2)
            for node, position in zip(nodes, positions):
                node.move_to(position)
            for edge, (a, b) in zip(edges, pairs):
                edge.put_start_and_end_on(positions[a], positions[b])
            current = min(int(progress.get_value()), len(events) - 1)
            for event_index in range(state["last"] + 1, current + 1):
                node, discovered, queue = events[event_index]
                if state["active"] is not None:
                    previous = state["active"]
                    nodes[previous].set_color(palette[distances[previous]])
                for neighbor in discovered:
                    nodes[neighbor].set_color(TEAL)
                    index = edge_index[min(node, neighbor), max(node, neighbor)]
                    edges[index].set_stroke(TEAL_E, 1.7)
                nodes[node].set_color(YELLOW)
                for i, digit in enumerate(queue_digits):
                    digit.set_value(queue[i] if i < len(queue) else 0)
                    digit.set_opacity(1 if i < len(queue) else 0.15)
                visited.set_value(event_index + 1)
                state.update(last=event_index, active=node)
            halo.move_to(positions[events[current][0]])

        controller = Mobject().add_updater(update_layout)
        self.add(controller, halo)
        self.play(progress.animate.set_value(len(events) - 1), run_time=11, rate_func=linear)
        route = [goal]
        while route[-1] != start:
            route.append(int(parents[route[-1]]))
        route.reverse()
        route_progress = ValueTracker(0)
        route_line = VMobject(stroke_color=YELLOW, stroke_width=5)

        def update_route(m):
            index = min(route_progress.get_value(), len(route) - 1.000001)
            whole = int(index)
            tip = interpolate(positions[route[whole]], positions[route[whole + 1]], index - whole)
            m.set_points_as_corners([*positions[route[:whole + 1]], tip])
            halo.move_to(tip)

        route_line.add_updater(update_route)
        self.add(route_line)
        self.play(route_progress.animate.set_value(len(route) - 1), run_time=2.5, rate_func=linear)
