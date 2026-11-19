# ROS 2 workspace snapshot

This repository contains the ROS 2 workspace files for the robotics mini-project.
The `turtlebot_datasets` package is in `src/datasets`, and `2a_commands.txt`
contains the project commands.

## Build

From the repository root, in a ROS 2 environment:

```bash
colcon build --packages-select turtlebot_datasets
source install/setup.bash
```

Small map files are included. The large rosbag databases and archive are omitted
from this public repository; download them when needed with:

```bash
bash src/datasets/scripts/download_dataset.sh
```

Generated `build/`, `install/`, and `log/` directories are not tracked.
