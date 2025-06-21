#ifndef LOONG_PLANNER_H_
#define LOONG_PLANNER_H_

#include <ros/ros.h>
#include <nav_core/base_local_planner.h>

namespace loong_planner
{
    class LoongPlanner : public nav_core::BaseLocalPlanner
    {
        public:
            LoongPlanner();
            ~LoongPlanner();

            void initialize(std::string name, tf2_ros::Buffer* tf, costmap_2d::Costmap2DROS* costmap_ros);  //初始化函数，话题订阅与发布，参数读取
            bool setPlan(const std::vector<geometry_msgs::PoseStamped>& plan); //接受来自全局规划器的全局导航路线的函数
            bool computeVelocityCommands(geometry_msgs::Twist& cmd_vel);   //计算速度
            bool isGoalReached();  //提交导航结果  
    };
} // namespace loong_planner

#endif  // LOONG_PLANNER_H_
