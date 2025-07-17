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
    double linear_velocity_weight_;
    double angular_velocity_weight_;
    void LoongPlanner::initialize(std::string name, tf2_ros::Buffer* tf, costmap_2d::Costmap2DROS* costmap_ros)
    {
        ROS_WARN("loong_planner start!");
        tf_listener_ = new tf::TransformListener();
        costmap_ros_ = costmap_ros;
        ros::NodeHandle nh("~");
        nh.param("max_linear_velocity_x", max_linear_velocity_x, 0.3);  
        nh.param("max_linear_velocity_y", max_linear_velocity_y, 0.2);  
        nh.param("max_angular_velocity", max_angular_velocity_, 0.6);  
        nh.param("linear_velocity_weight", linear_velocity_weight_, 2.0);  
        nh.param("angular_velocity_weight", angular_velocity_weight_, 2.0); 
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

        //opencv绘制代价地图
        cv::Mat map_image(size_y, size_x, CV_8UC3, cv::Scalar(128,128,128));
        for(unsigned int y=0 ; y < size_y ; y++)
        {
            for(unsigned int x=0 ; x < size_y ; x++)
            {
                int map_index=y*size_x + x;
                unsigned char cost = map_data[map_index];
                cv::Vec3b& pixel = map_image.at<cv::Vec3b>(map_index);

                if(cost == 0)                           //可通行区域，灰色
                    pixel = cv::Vec3b(128,128,128);
                else if (cost == 254)                   //障碍物，黑色
                    pixel = cv::Vec3b(0,0,0);
                else if (cost == 253)                   //禁行区域，浅蓝
                    pixel = cv::Vec3b(255,255,0);
                else
                {
                    //根据灰度值显示从红色到蓝色的渐变
                    unsigned char blue = 255-cost;
                    unsigned char red = cost;
                    pixel = cv::Vec3d(blue, 0, red);
                }

            }
        }

        //在代价地图上遍历导航路径点
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
            //cv::circle(map_image, cv::Point(x,y), 0, cv::Scalar(255,0,255));
           
           //检测动态障碍物
           if(i >= target_index_ && i < target_index_ + 10)
           {
                cv::circle(map_image, cv::Point(x,y), 0, cv::Scalar(0,255,255));
                int map_index = y * size_x + x;
                unsigned char cost = map_data[map_index];
                if(cost >= 253)
                    return false;
           }
            
        }
        map_image.at<cv::Vec3b>(size_y/2, size_x/2) = cv::Vec3b(0,255,0);

        //翻转地图
        cv::Mat flipped_image(size_x, size_y, CV_8UC3, cv::Scalar(128, 128, 128));
        for(unsigned int y=0; y<size_y;++y)
        {
            for(unsigned int x=0; x<size_x; ++x)
            {
                cv::Vec3b& pixel = map_image.at<cv::Vec3b>(y,x);
                flipped_image.at<cv::Vec3b>((size_x -1 -x), (size_y -1 -y)) = pixel;
            }
        }
        map_image = flipped_image;
        // //显示代价地图
        // cv::namedWindow("CostMap");
        // cv::resize(map_image, map_image, cv::Size(size_y*5, size_x*5), 0, 0, cv::INTER_NEAREST);
        // cv::resizeWindow("CostMap",size_y*5, size_x*5);
        // cv::imshow("CostMap", map_image);


        int final_index = global_plan_.size()-1;
        geometry_msgs::PoseStamped pose_final;
        global_plan_[final_index].header.stamp = ros::Time(0);
        tf_listener_->transformPose("body_foot",global_plan_[final_index],pose_final);
        if(pose_adjusting_ == false)
        {
            double dx = pose_final.pose.position.x;
            double dy = pose_final.pose.position.y;
            double dist = std::sqrt(dx*dx + dy*dy);
            if(dist < 0.05)
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
                cmd_vel.angular.z = 0.3;  // 顺时针旋转
            } 
            else 
            {
                cmd_vel.angular.z = -0.3; // 逆时针旋转
            }
            // 如果差值小于阈值，认为到达目标朝向
            if (abs(delta_yaw) < 0.1)
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

            if(dist > 0.08)
            {
                target_pose = pose_base;
                target_index_ = i;
                ROS_WARN("选择第%d个路径点作为临时目标，距离=%.2f",target_index_,dist);
                break;
            }

            if(i == global_plan_.size()-1)
                target_pose = pose_base;

        }


        double linear_velocity_x = linear_velocity_weight_ * target_pose.pose.position.x;
        double angular_velocity = angular_velocity_weight_ * target_pose.pose.position.y;
        if (linear_velocity_x > max_linear_velocity_x)
            linear_velocity_x = max_linear_velocity_x;
        if (angular_velocity > max_angular_velocity_)
            angular_velocity = max_angular_velocity_;

        cmd_vel.linear.x = linear_velocity_x;
        cmd_vel.angular.z = angular_velocity;
        // cv::Mat plan_image(600,600,CV_8UC3,cv::Scalar(0,0,0));
        // for(int i=0;i<global_plan_.size();i++)
        // {
        //     geometry_msgs::PoseStamped pose_base;
        //     global_plan_[i].header.stamp = ros::Time(0);
        //     tf_listener_->transformPose("body_foot",global_plan_[i],pose_base);
        //     int cv_x = 300 - pose_base.pose.position.y*100;
        //     int cv_y = 300 - pose_base.pose.position.x*100;
        //     //cv::circle(plan_image, cv::Point(cv_x,cv_y),1, cv::Scalar(255,0,255));
        // }
        // cv::circle(plan_image, cv::Point(300, 300), 15, cv::Scalar(0,255,0));
        // cv::line(plan_image, cv::Point(65, 300), cv::Point(510, 300), cv::Scalar(0,255,0),1);
        // cv::line(plan_image, cv::Point(300, 45), cv::Point(300, 555), cv::Scalar(0,255,0),1);

        // cv::namedWindow("PLan");
        // cv::imshow("PLan",plan_image);
        // cv::waitKey(1);
        return true;
    }
    bool LoongPlanner::isGoalReached()
    {
        return goal_reached_;
    } 
} //namespace loong_planner


