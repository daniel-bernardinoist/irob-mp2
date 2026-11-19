#!/usr/bin/env python3
"""Publish the known Gazebo spawn pose to AMCL during the Task 2a demo."""

import math
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile


class InitialPosePublisher(Node):
    def __init__(self) -> None:
        super().__init__('task2a_initial_pose_publisher')
        self._x = float(self.declare_parameter('x', -0.59).value)
        self._y = float(self.declare_parameter('y', 3.83).value)
        self._yaw = float(self.declare_parameter('yaw', 0.0).value)
        qos = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self._publisher = self.create_publisher(
            PoseWithCovarianceStamped, '/initialpose', qos
        )
        self._amcl_pose_subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self._handle_amcl_pose,
            10,
        )
        self._localized = False
        self._pose_log_emitted = False

    def _handle_amcl_pose(self, _message: PoseWithCovarianceStamped) -> None:
        self._localized = True

    def publish_initial_pose(self) -> None:
        now = self.get_clock().now()
        offset = Duration(seconds=0.1)
        stamp = now - offset if now.nanoseconds > offset.nanoseconds else now

        message = PoseWithCovarianceStamped()
        message.header.stamp = stamp.to_msg()
        message.header.frame_id = 'map'
        message.pose.pose.position.x = self._x
        message.pose.pose.position.y = self._y
        message.pose.pose.orientation.z = math.sin(self._yaw / 2.0)
        message.pose.pose.orientation.w = math.cos(self._yaw / 2.0)
        message.pose.covariance[0] = 0.25
        message.pose.covariance[7] = 0.25
        message.pose.covariance[35] = 0.1
        self._publisher.publish(message)
        if not self._pose_log_emitted:
            self.get_logger().info(
                'Publishing the known map-frame spawn pose to AMCL.'
            )
            self._pose_log_emitted = True


def main(args=None) -> None:
    rclpy.init(args=args)
    node = InitialPosePublisher()
    deadline = time.monotonic() + 60.0
    try:
        while rclpy.ok() and not node._localized and time.monotonic() < deadline:
            node.publish_initial_pose()
            rclpy.spin_once(node, timeout_sec=0.5)
        if node._localized:
            node.get_logger().info('Initial pose published; ready to send waypoints.')
        else:
            raise RuntimeError(
                'AMCL did not publish /amcl_pose after initial-pose updates within 60 seconds.'
            )
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
