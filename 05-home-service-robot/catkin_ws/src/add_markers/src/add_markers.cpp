#include <ros/ros.h>
#include <visualization_msgs/Marker.h>
#include <geometry_msgs/PoseWithCovarianceStamped.h>
#include <cmath>
#include <cstdio>
#include <string>

// Publishes the object to deliver as a cube marker in RViz.
//  mode "timed": pickup zone, 5 s, hidden, 5 s, drop-off zone.
//  mode "pose":  visible at the pickup zone, hidden when the robot reaches it,
//                shown at the drop-off zone when the robot reaches that one.
class AddMarkers
{
public:
  AddMarkers() : state_(AT_PICKUP)
  {
    ros::NodeHandle nh;
    ros::NodeHandle pnh("~");
    nh.param("/zones/pickup_x", pickup_x_, 1.0);
    nh.param("/zones/pickup_y", pickup_y_, -1.5);
    nh.param("/zones/dropoff_x", dropoff_x_, -6.0);
    nh.param("/zones/dropoff_y", dropoff_y_, 0.0);
    nh.param("/zones/tolerance", tolerance_, 0.3);
    nh.param("/zones/wait_time", pause_, 5.0);
    pnh.param<std::string>("mode", mode_, "pose");

    // Latched, so a late RViz still receives the current marker
    pub_ = nh.advertise<visualization_msgs::Marker>("visualization_marker", 1, true);
    if (mode_ == "pose") {
      sub_ = nh.subscribe("amcl_pose", 1, &AddMarkers::poseCallback, this);
    }
  }

  void run()
  {
    waitForRviz();
    show(pickup_x_, pickup_y_);
    ROS_INFO("Marker shown at the pickup zone (%.2f, %.2f)", pickup_x_, pickup_y_);

    if (mode_ == "timed") {
      ros::WallDuration(pause_).sleep();
      hide();
      ROS_INFO("Marker hidden");
      ros::WallDuration(pause_).sleep();
      show(dropoff_x_, dropoff_y_);
      ROS_INFO("Marker shown at the drop-off zone (%.2f, %.2f)", dropoff_x_, dropoff_y_);
    }
    ros::spin();
  }

private:
  enum State { AT_PICKUP, CARRYING, DELIVERED };

  void waitForRviz()
  {
    ros::WallTime start = ros::WallTime::now();
    while (ros::ok() && pub_.getNumSubscribers() < 1 && (ros::WallTime::now() - start).toSec() < 30.0) {
      ROS_INFO_THROTTLE(5, "Waiting for a subscriber to visualization_marker (RViz)");
      ros::WallDuration(0.5).sleep();
    }
  }

  void show(double x, double y)
  {
    visualization_msgs::Marker marker;
    marker.header.frame_id = "map";
    marker.header.stamp = ros::Time::now();
    marker.ns = "home_service";
    marker.id = 0;
    marker.type = visualization_msgs::Marker::CUBE;
    marker.action = visualization_msgs::Marker::ADD;
    marker.pose.position.x = x;
    marker.pose.position.y = y;
    marker.pose.position.z = 0.15;
    marker.pose.orientation.w = 1.0;
    marker.scale.x = marker.scale.y = marker.scale.z = 0.3;
    marker.color.r = 0.1;
    marker.color.g = 0.3;
    marker.color.b = 1.0;
    marker.color.a = 1.0;
    marker.lifetime = ros::Duration();
    pub_.publish(marker);
  }

  void hide()
  {
    visualization_msgs::Marker marker;
    marker.header.frame_id = "map";
    marker.header.stamp = ros::Time::now();
    marker.ns = "home_service";
    marker.id = 0;
    marker.action = visualization_msgs::Marker::DELETE;
    pub_.publish(marker);
  }

  void poseCallback(const geometry_msgs::PoseWithCovarianceStamped::ConstPtr& msg)
  {
    double x = msg->pose.pose.position.x;
    double y = msg->pose.pose.position.y;

    if (state_ == AT_PICKUP && std::hypot(x - pickup_x_, y - pickup_y_) < tolerance_) {
      hide();
      state_ = CARRYING;
      ROS_INFO("The robot reached the pickup zone: marker hidden");
    } else if (state_ == CARRYING && std::hypot(x - dropoff_x_, y - dropoff_y_) < tolerance_) {
      show(dropoff_x_, dropoff_y_);
      state_ = DELIVERED;
      ROS_INFO("The robot reached the drop-off zone: marker shown");
    }
  }

  ros::Publisher pub_;
  ros::Subscriber sub_;
  std::string mode_;
  State state_;
  double pickup_x_, pickup_y_, dropoff_x_, dropoff_y_, tolerance_, pause_;
};

int main(int argc, char** argv)
{
  setvbuf(stdout, NULL, _IONBF, 0);  // messages appear immediately, also when the output goes to a file
  ros::init(argc, argv, "add_markers");
  AddMarkers node;
  node.run();
  return 0;
}
