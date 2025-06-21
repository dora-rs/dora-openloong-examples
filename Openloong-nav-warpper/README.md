# LoongPlanner

> LoongPlanner 是一个面向 ROS 的自定义 local planner 插件，具备路径跟随、平滑速度控制和目标点微调等功能，适用于人形/全向移动机器人。

---

## 功能特性

- **路径跟随**：自适应选择局部目标点，平滑跟踪全局路径。
- **速度平滑**：内置一阶滤波器，有效消除加速度突变，运动更柔和。
- **终点微调**：靠近目标点时自动切换为精细位置和朝向调整。
- **障碍避让**：结合 costmap 检查，遇到高代价区域自动停止。
- **参数化配置**：所有控制参数均可通过 ROS 参数动态配置。
- **全向底盘支持**：支持 x/y/角速度控制。

---

## 依赖

- ROS（推荐 Melodic/Noetic）
- `costmap_2d`
- `nav_core`
- `tf`
- `geometry_msgs`
- OpenCV（调试可选）
- C++11 及以上

---

## 快速上手

1. **克隆仓库**到工作空间 `src` 目录下：

    ```bash
    cd ~/catkin_ws/src
    git clone https://github.com/yourname/loong_planner.git
    ```

2. **编译工程**：

    ```bash
    cd ~/catkin_ws
    catkin_make
    source devel/setup.bash
    ```

3. **配置 Navigation Stack**  
   在 `move_base` 启动文件或参数 YAML 中添加：

    ```yaml
    base_local_planner: "loong_planner/LoongPlanner"
    ```

    参数示例（loong_planner.yaml）：

    ```yaml
    loong_planner:
      max_linear_velocity_x: 0.3
      max_linear_velocity_y: 0.2
      max_angular_velocity: 0.6
      linear_velocity_weight_x: 1.0
      linear_velocity_weight_y: 1.0
      angular_velocity_weight: 1.0
      path_follow: 0.2
      final_dist: 0.2
      velocity_smoothing_alpha: 0.4   # 越小越平滑，建议 0.2~0.5
    ```

4. **启动 move_base** 并验证运行效果。

---

## 主要参数说明

| 参数名                     | 默认值 | 说明                               |
|----------------------------|--------|------------------------------------|
| max_linear_velocity_x      | 0.3    | 最大 X 方向线速度 (m/s)            |
| max_linear_velocity_y      | 0.2    | 最大 Y 方向线速度 (m/s)            |
| max_angular_velocity       | 0.6    | 最大角速度 (rad/s)                 |
| linear_velocity_weight_x   | 1.0    | X 方向速度权重                     |
| linear_velocity_weight_y   | 1.0    | Y 方向速度权重                     |
| angular_velocity_weight    | 1.0    | 角速度权重                         |
| path_follow                | 0.2    | 路径点选择的前视距离 (m)           |
| final_dist                 | 0.2    | 进入终点微调的距离阈值 (m)         |
| velocity_smoothing_alpha   | 0.4    | 速度平滑系数，越小越平滑 (0~1)     |

**速度平滑公式：**
cmd_vel = alpha * 当前速度 + (1 - alpha) * 上一次速度

- alpha 越小，控制越平滑但反应越慢，一般推荐 0.3~0.5。

---

## 注意事项

- 建议用于全向机器人或支持 xy 运动的底盘。
- `global_plan`、`costmap` 的 frame_id 需匹配（如 `robot_foot_init`, `body_foot`）。
- 遇到 costmap 障碍（cost≥253）会立即停止输出速度，保障安全。

---


