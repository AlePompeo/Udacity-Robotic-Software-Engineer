#include <ros/ros.h>
#include <move_base_msgs/MoveBaseAction.h>
#include <actionlib/client/simple_action_client.h>
#include <cmath>
#include <cstdio>

typedef actionlib::SimpleActionClient<move_base_msgs::MoveBaseAction> MoveBaseClient;

// Sends a goal in the map frame and waits until move_base has finished it
static bool goTo(MoveBaseClient& ac, double x, double y, double yaw)
{
  move_base_msgs::MoveBaseGoal goal;
  goal.target_pose.header.frame_id = "map";
  goal.target_pose.header.stamp = ros::Time::now();
  goal.target_pose.pose.position.x = x;
  goal.target_pose.pose.position.y = y;
  goal.target_pose.pose.orientation.z = std::sin(yaw / 2.0);
  goal.target_pose.pose.orientation.w = std::cos(yaw / 2.0);

  ac.sendGoal(goal);
  ac.waitForResult();
  return ac.getState() == actionlib::SimpleClientGoalState::SUCCEEDED;
}

int main(int argc, char** argv)
{
  setvbuf(stdout, NULL, _IONBF, 0);  // messages appear immediately, also when the output goes to a file
  ros::init(argc, argv, "pick_objects");
  ros::NodeHandle nh;

  double pickup_x, pickup_y, pickup_yaw, dropoff_x, dropoff_y, dropoff_yaw, wait_time;
  nh.param("/zones/pickup_x", pickup_x, 1.0);
  nh.param("/zones/pickup_y", pickup_y, -1.5);
  nh.param("/zones/pickup_yaw", pickup_yaw, 0.0);
  nh.param("/zones/dropoff_x", dropoff_x, -6.0);
  nh.param("/zones/dropoff_y", dropoff_y, 0.0);
  nh.param("/zones/dropoff_yaw", dropoff_yaw, 0.0);
  nh.param("/zones/wait_time", wait_time, 5.0);

  MoveBaseClient ac("move_base", true);
  while (!ac.waitForServer(ros::Duration(5.0))) {
    ROS_INFO("Waiting for the move_base action server to come up");
  }

  ROS_INFO("Going to the pickup zone (%.2f, %.2f)", pickup_x, pickup_y);
  if (!goTo(ac, pickup_x, pickup_y, pickup_yaw)) {
    ROS_ERROR("The robot failed to reach the pickup zone");
    return 1;
  }
  ROS_INFO("Reached the pickup zone");

  ROS_INFO("Picking up the object: waiting %.0f seconds", wait_time);
  ros::WallDuration(wait_time).sleep();

  ROS_INFO("Going to the drop-off zone (%.2f, %.2f)", dropoff_x, dropoff_y);
  if (!goTo(ac, dropoff_x, dropoff_y, dropoff_yaw)) {
    ROS_ERROR("The robot failed to reach the drop-off zone");
    return 1;
  }
  ROS_INFO("Reached the drop-off zone: object delivered");

  return 0;
}
