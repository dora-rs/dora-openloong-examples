#include "loong_planner.h"
#include <pluginlib/class_list_macros.h>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <tf/tf.h>
#include <tf/transform_listener.h>
#include <tf/transform_datatypes.h>

PLUGINLIB_EXPORT_CLASS( loong_planner::LoongPlanner, nav_core::BaseLocalPlanner)

namespace loong_planner
{
    LoongPlanner::LoongPlanner()
    {
        setlocale(LC_ALL,"");
    }
    LoongPlanner::~LoongPlanner()
    {}

    tf::TransformListener* tf_listener_;
    costmap_2d::Costmap2DROS* costmap_ros_;


    double max_linear_velocity_x;
    double max_linear_velocity_y;
    double max_angular_velocity_;
    double linear_velocity_weight_x;
    double linear_velocity_weight_y;
    double angular_velocity_weight_;
    double path_follow;
    double final_dist;

    void LoongPlanner::initialize(std::string name, tf2_ros::Buffer* tf, costmap_2d::Costmap2DROS* costmap_ros)
    {
        ROS_WARN("loong_planner start!");
        tf_listener_ = new tf::TransformListener();
        costmap_ros_ = costmap_ros;
        ros::NodeHandle nh("~");
        nh.param("max_linear_velocity_x", max_linear_velocity_x, 0.3);  
        nh.param("max_linear_velocity_y", max_linear_velocity_y, 0.2);  
        nh.param("max_angular_velocity", max_angular_velocity_, 0.6);  
        nh.param("linear_velocity_weight_x", linear_velocity_weight_x, 1.0);  
        nh.param("linear_velocity_weight_y", linear_velocity_weight_y, 1.0);
        nh.param("angular_velocity_weight", angular_velocity_weight_, 1.0); 
        nh.param("path_follow", path_follow, 0.2); 
        nh.param("final_dist", final_dist, 0.2); 

    }


    std::vector<geometry_msgs::PoseStamped> global_plan_;
    int target_index_;
    bool pose_adjusting_;
    bool goal_reached_;
    bool LoongPlanner::setPlan(const std::vector<geometry_msgs::PoseStamped>& plan)
    {
        target_index_ = 0;
        global_plan_ = plan;
        pose_adjusting_ = false;
        goal_reached_ = false;
        return true;
    }

    bool LoongPlanner::computeVelocityCommands(geometry_msgs::Twist& cmd_vel)
    {
        costmap_2d::Costmap2D* costmap = costmap_ros_->getCostmap();
        unsigned char* map_data = costmap->getCharMap();
        unsigned int size_x = costmap->getSizeInCellsX();
        unsigned int size_y = costmap->getSizeInCellsY();
        for(int i=0;i<global_plan_.size();i++)
        {
            geometry_msgs::PoseStamped pose_odom;
            global_plan_[i].header.stamp = ros::Time(0);
            tf_listener_->transformPose("robot_foot_init",global_plan_[i],pose_odom);
            double odom_x = pose_odom.pose.position.x;
            double odom_y = pose_odom.pose.position.y;

            double origin_x = costmap->getOriginX();
            double origin_y = costmap->getOriginY();
            double local_x = odom_x - origin_x;
            double local_y = odom_y - origin_y;
            int x = local_x / costmap->getResolution();
            int y = local_y / costmap->getResolution();
           if(i >= target_index_ && i < target_index_ + 10)
           {
                int map_index = y * size_x + x;
                unsigned char cost = map_data[map_index];
                if(cost >= 253)
                    return false;
           }
            
        }


        int final_index = global_plan_.size()-1;
        geometry_msgs::PoseStamped pose_final;
        global_plan_[final_index].header.stamp = ros::Time(0);
        tf_listener_->transformPose("body_foot",global_plan_[final_index],pose_final);
        double dx = pose_final.pose.position.x;
        double dy = pose_final.pose.position.y;
        double dist = std::sqrt(dx*dx + dy*dy);
        if(pose_adjusting_ == false)
        {
            if(dist < final_dist)
                pose_adjusting_ = true;
        }

        if (pose_adjusting_ == true)
        {
            double final_yaw = tf::getYaw(pose_final.pose.orientation);
            ROS_WARN("调整最终姿态，final_yaw= %.2f", final_yaw);
            cmd_vel.linear.x = 0;
            // 计算当前姿态与目标姿态的差值
            double delta_yaw = final_yaw;           
            // 确保差值在 -π 到 π 范围内
            if (delta_yaw > M_PI) 
            {
                delta_yaw -= 2 * M_PI;  // 将差值限制在 -π 到 π 范围
            }
            else if (delta_yaw < -M_PI)
            {
                delta_yaw += 2 * M_PI;
            }
            // 根据差值来决定旋转方向，使用较小的角速度
            if (delta_yaw > 0) 
            {
                cmd_vel.angular.z = 0.6;  // 顺时针旋转
            } 
            else 
            {
                cmd_vel.angular.z = -0.6; // 逆时针旋转
            }
            // 如果差值小于阈值，认为到达目标朝向
            if (abs(delta_yaw) < 0.2)
            {
                
                    goal_reached_ = true;
                    ROS_WARN("到达终点！");
                    cmd_vel.linear.x = 0;
                    cmd_vel.angular.z = 0;
               
            }
            return true;
        }

        
        geometry_msgs::PoseStamped target_pose;
        for(int i=target_index_;i<global_plan_.size();i++)
        {
            geometry_msgs::PoseStamped pose_base;
            global_plan_[i].header.stamp = ros::Time(0);
            tf_listener_->transformPose("body_foot",global_plan_[i],pose_base);
            double dx = pose_base.pose.position.x;
            double dy = pose_base.pose.position.y;
            double dist = std::sqrt(dx*dx + dy*dy);

            if(dist > path_follow)
            {
                target_pose = pose_base;
                target_index_ = i;
                ROS_WARN("选择第%d个路径点作为临时目标，距离=%.2f",target_index_,dist);
                break;
            }

            if(i == global_plan_.size()-1)
                target_pose = pose_base;

        }


        double linear_velocity_x = linear_velocity_weight_x * target_pose.pose.position.x;
        double linear_velocity_y = linear_velocity_weight_y * target_pose.pose.position.y;
        double angular_velocity = angular_velocity_weight_ * target_pose.pose.position.y;

        if(std::abs(linear_velocity_x)>max_linear_velocity_x){
            if(linear_velocity_x<0){
                linear_velocity_x = -max_linear_velocity_x;
            }else{
                linear_velocity_x = max_linear_velocity_x;
            }
        }

        if(std::abs(linear_velocity_y)>max_linear_velocity_y){
            if(linear_velocity_y<0){
                linear_velocity_y = -max_linear_velocity_y;
            }else{
                linear_velocity_y = max_linear_velocity_y;
            }
        }

        if(std::abs(angular_velocity)>max_angular_velocity_){
            if(angular_velocity<0){
                angular_velocity = -max_angular_velocity_;
            }else{
                angular_velocity = max_angular_velocity_;
            }
        }


        if(linear_velocity_x<-0.4){
           linear_velocity_x = 0;
           angular_velocity = 0.6;
        }
        cmd_vel.linear.x = linear_velocity_x;
        cmd_vel.linear.y = linear_velocity_y;

        cmd_vel.angular.z = angular_velocity;
        return true;
    }
    bool LoongPlanner::isGoalReached()
    {
        return goal_reached_;
    } 
} //namespace loong_planner
