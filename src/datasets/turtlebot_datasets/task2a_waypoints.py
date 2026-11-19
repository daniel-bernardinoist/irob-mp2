#!/usr/bin/env python3
"""Simple Nav2 waypoint-navigation demo for Mini-Project 2, Task 2a.

The script sends a sequence of four goals to the Nav2 ``/navigate_to_pose``
action server. Each goal is expressed in the ``map`` frame and is intended to
represent the four waypoints from the project specification.

Usage:
    ros2 run turtlebot_datasets task2a_waypoints

    # custom waypoint list (x, y, yaw_radians)
    ros2 run turtlebot_datasets task2a_waypoints -- --waypoints \
        "1.0,1.0,0.0; 2.5,1.0,1.57; 2.5,2.5,3.14; 1.0,2.5,-1.57"

The default values are example coordinates in the map frame and should be
replaced with the actual pose estimates from the lab map.
"""

from __future__ import annotations

import argparse
import math
from typing import Iterable

import rclpy
from action_msgs.msg import GoalStatus
from builtin_interfaces.msg import Time
from geometry_msgs.msg import Point, PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray


# Provisional clockwise loop in the clear central area of the uploaded lab map.
# Confirm the locations and starting pose in RViz/Foxglove before running on a robot.
DEFAULT_WAYPOINTS = [
    (2.0, 3.0, 0.0),
    (4.5, 0.0, 0.0),
    (4.5, 3.0, 0.0),
    (0.0, 1.0, 0.0),
    #(-0.59, 3.83, 0.0),
    #(3.01, 3.83, 0.0),
    #(2.61, -0.77, 0.0),
    #(-0.99, -0.77, 0.0),
]

WAYPOINT_COLORS = [
    (1.0, 0.25, 0.2),
    (0.2, 0.85, 0.3),
    (0.2, 0.55, 1.0),
    (1.0, 0.25, 0.85),
]


def quaternion_from_yaw(yaw: float) -> Quaternion:
    return Quaternion(
        x=0.0,
        y=0.0,
        z=math.sin(yaw / 2.0),
        w=math.cos(yaw / 2.0),
    )


def parse_waypoints(raw_waypoints: str | None) -> list[tuple[float, float, float]]:
    if raw_waypoints is None:
        return DEFAULT_WAYPOINTS

    waypoints: list[tuple[float, float, float]] = []
    for token in raw_waypoints.split(';'):
        token = token.strip()
        if not token:
            continue
        values = [part.strip() for part in token.split(',')]
        if len(values) != 3:
            raise ValueError(
                f"Each waypoint must have exactly three values: x,y,yaw. Got '{token}'"
            )
        x, y, yaw = values
        waypoints.append((float(x), float(y), float(yaw)))
    return waypoints


def make_pose(x: float, y: float, yaw: float, stamp: Time) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = stamp
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    pose.pose.orientation = quaternion_from_yaw(yaw)
    return pose


class WaypointNavigator(Node):
    def __init__(self, waypoints: Iterable[tuple[float, float, float]]) -> None:
        super().__init__('task2a_waypoint_navigator')
        self._client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._waypoints = list(waypoints)
        self._marker_publisher = self.create_publisher(
            MarkerArray, '/task2a/waypoints', 10
        )
        self._marker_timer = self.create_timer(1.0, self._publish_waypoint_markers)

    def _publish_waypoint_markers(self) -> None:
        now = self.get_clock().now().to_msg()
        markers = MarkerArray()

        route = Marker()
        route.header.frame_id = 'map'
        route.header.stamp = now
        route.ns = 'task2a_waypoint_route'
        route.id = 0
        route.type = Marker.LINE_STRIP
        route.action = Marker.ADD
        route.pose.orientation.w = 1.0
        route.scale.x = 0.04
        route.color.r = 1.0
        route.color.g = 1.0
        route.color.b = 1.0
        route.color.a = 0.8
        for x, y, _ in self._waypoints:
            route.points.append(Point(x=x, y=y, z=0.04))
        markers.markers.append(route)

        for index, (x, y, yaw) in enumerate(self._waypoints, start=1):
            red, green, blue = WAYPOINT_COLORS[(index - 1) % len(WAYPOINT_COLORS)]

            sphere = Marker()
            sphere.header.frame_id = 'map'
            sphere.header.stamp = now
            sphere.ns = 'task2a_waypoint_points'
            sphere.id = index
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x = x
            sphere.pose.position.y = y
            sphere.pose.position.z = 0.12
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = sphere.scale.y = sphere.scale.z = 0.3
            sphere.color.r = red
            sphere.color.g = green
            sphere.color.b = blue
            sphere.color.a = 1.0
            markers.markers.append(sphere)

            label = Marker()
            label.header.frame_id = 'map'
            label.header.stamp = now
            label.ns = 'task2a_waypoint_labels'
            label.id = index
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD
            label.pose.position.x = x
            label.pose.position.y = y
            label.pose.position.z = 0.55
            label.pose.orientation.w = 1.0
            label.scale.z = 0.3
            label.color.r = 1.0
            label.color.g = 1.0
            label.color.b = 1.0
            label.color.a = 1.0
            label.text = f'W{index}'
            markers.markers.append(label)

            arrow = Marker()
            arrow.header.frame_id = 'map'
            arrow.header.stamp = now
            arrow.ns = 'task2a_waypoint_headings'
            arrow.id = index
            arrow.type = Marker.ARROW
            arrow.action = Marker.ADD
            arrow.pose.position.x = x
            arrow.pose.position.y = y
            arrow.pose.position.z = 0.08
            arrow.pose.orientation = quaternion_from_yaw(yaw)
            arrow.scale.x = 0.65
            arrow.scale.y = 0.08
            arrow.scale.z = 0.16
            arrow.color.r = red
            arrow.color.g = green
            arrow.color.b = blue
            arrow.color.a = 1.0
            markers.markers.append(arrow)

        self._marker_publisher.publish(markers)

    def run(self, visualize_only: bool = False) -> None:
        if not self._waypoints:
            raise ValueError('At least one waypoint is required.')

        self._publish_waypoint_markers()
        self.get_logger().info(
            'Publishing labeled waypoint markers on /task2a/waypoints in the map frame.'
        )
        if visualize_only:
            self.get_logger().info(
                'Visualization-only mode: no navigation goals will be sent.'
            )
            return

        if not self._client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('Action server /navigate_to_pose is not available.')
            raise RuntimeError('Nav2 NavigateToPose action server is not running.')

        for index, (x, y, yaw) in enumerate(self._waypoints, start=1):
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = make_pose(x, y, yaw, self.get_clock().now().to_msg())
            self.get_logger().info(
                f'Sending waypoint {index}/{len(self._waypoints)}: '
                f'x={x:.3f} y={y:.3f} yaw={yaw:.3f} rad'
            )

            send_goal_future = self._client.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(self, send_goal_future)
            goal_handle = send_goal_future.result()
            if goal_handle is None:
                raise RuntimeError(f'No goal response received for waypoint {index}.')
            if not goal_handle.accepted:
                raise RuntimeError(f'Waypoint {index} was rejected by Nav2.')

            result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, result_future)
            result = result_future.result()
            if result is None:
                raise RuntimeError(f'No result received for waypoint {index}.')
            if result.status == GoalStatus.STATUS_SUCCEEDED:
                self.get_logger().info(f'Waypoint {index} reached successfully.')
            else:
                self.get_logger().warn(
                    f'Waypoint {index} ended with status {result.status}; '
                    'stopping the sequence.'
                )
                return

        self.get_logger().info('Finished visiting all waypoints.')
        self.get_logger().info(
            'Keeping waypoint markers visible. Press Ctrl-C to stop this node.'
        )


def main(args: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description='Nav2 waypoint demo for Task 2a.')
    parser.add_argument(
        '--waypoints',
        type=str,
        default=None,
        help='Semicolon-separated list of x,y,yaw values in the map frame. Example: "1,1,0; 2,1,1.57"',
    )
    parser.add_argument(
        '--visualize-only',
        action='store_true',
        help='Publish waypoint markers without sending navigation goals.',
    )
    parsed = parser.parse_args(args)

    try:
        waypoints = parse_waypoints(parsed.waypoints)
    except ValueError as exc:
        parser.error(str(exc))

    rclpy.init(args=args)
    try:
        navigator = WaypointNavigator(waypoints)
        navigator.run(visualize_only=parsed.visualize_only)
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        if 'navigator' in locals():
            navigator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
