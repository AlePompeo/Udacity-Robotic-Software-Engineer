#include "ros/ros.h"
#include "ball_chaser/DriveToTarget.h"
#include <sensor_msgs/Image.h>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <string>
#include <vector>

ros::ServiceClient client;

// Parameter ~target_color: "any" chases the colors accepted by is_supported_color(), "white" only pure white
bool detect_any_color = true;

// A ball resting on the floor, seen by a level camera at height camera_height, has its lowest point below the
// horizon by (camera_height / ball_diameter) times its apparent diameter, at any distance.
// This tells a ball from plants, wall patches seen through doors and other round things.
double ball_diameter = 0.2;     // meters
double camera_height = 0.15;    // meters
double ground_tolerance = 0.4;  // accepted relative error on that ratio

// Colors chased when target_color is "any". The disabled ones look like parts of the world (floor, walls,
// furniture, other robots) and made the robot chase things that are not balls, or are not picked up reliably.
//   enabled : white, red, green, blue, cyan / light blue, purple, magenta
//   disabled: black and dark colors, grey, orange, brown, yellow (hue between 10 and 80 degrees)
bool is_supported_color(double r, double g, double b)
{
    const double max_c = std::max(r, std::max(g, b));
    const double min_c = std::min(r, std::min(g, b));
    const double value = max_c / 255.0;
    const double saturation = (max_c > 0.0) ? (max_c - min_c) / max_c : 0.0;

    if (value >= 0.9 && saturation <= 0.15)
        return true;                          // white
    if (value < 0.25 || saturation < 0.3)
        return false;                         // black, dark colors and grey

    const double d = max_c - min_c;
    double hue;                               // degrees, 0..360
    if (max_c == r)
        hue = 60.0 * std::fmod((g - b) / d, 6.0);
    else if (max_c == g)
        hue = 60.0 * ((b - r) / d + 2.0);
    else
        hue = 60.0 * ((r - g) / d + 4.0);
    if (hue < 0.0)
        hue += 360.0;

    return !(hue >= 10.0 && hue < 80.0);
}

void drive_robot(float lin_x, float ang_z)
{
    ball_chaser::DriveToTarget srv;
    srv.request.linear_x = lin_x;
    srv.request.angular_z = ang_z;

    if (!client.call(srv))
        ROS_ERROR("Failed to call service command_robot");
}

// Pure white pixels (R = G = B = 255); returns the mean column of all of them
bool find_white_ball(const sensor_msgs::Image& img, double& column)
{
    const int white_pixel = 255;
    long white_count = 0;
    long column_sum = 0;

    // Pixels are stored row by row, 3 bytes (R, G, B) each; step is the row length in bytes
    for (unsigned int i = 0; i + 2 < img.data.size(); i += 3) {
        if (img.data[i] == white_pixel && img.data[i + 1] == white_pixel && img.data[i + 2] == white_pixel) {
            column_sum += (i % img.step) / 3;
            white_count++;
        }
    }

    if (white_count == 0)
        return false;

    column = static_cast<double>(column_sum) / white_count;
    return true;
}

// A ball is a compact, round region of smoothly changing color with a sharp edge. The image is sampled on a coarse
// grid and neighbouring samples of similar color are grouped into regions (a shaded sphere stays in one piece,
// its edge against the background splits it). A region is accepted as a ball if it has the size, shape, color and
// floor contact of one. Returns the mean column of the biggest (closest) ball.
bool find_ball_any_color(const sensor_msgs::Image& img, double& column)
{
    const int cell = 4;                            // sampling step in pixels
    const int tolerance = 24;                      // max |dR|+|dG|+|dB| between neighbouring samples of a region
    const int min_samples = 10;                    // about a ball seen from 6 m
    const int small_region_samples = 40;           // below this, the shape is too coarse for the strict checks
    const double min_aspect = 0.7, max_aspect = 1.4;
    const double min_fill = 0.68, max_fill = 0.86;  // a disc fills pi/4 = 0.785 of its bounding box
    const double max_profile_error = 0.12;         // row widths against a disc, relative to the diameter

    if (img.width == 0 || img.height == 0 || img.step < img.width)
        return false;
    const int gw = img.width / cell;
    const int gh = img.height / cell;
    const int bpp = img.step / img.width;          // bytes per pixel
    if (gw < 8 || gh < 8 || bpp < 1)
        return false;
    const int channels = std::min(static_cast<int>(bpp), 3);

    std::vector<unsigned char> color(static_cast<size_t>(gw) * gh * 3);
    for (int y = 0; y < gh; y++) {
        for (int x = 0; x < gw; x++) {
            const size_t offset = static_cast<size_t>(y * cell + cell / 2) * img.step + static_cast<size_t>(x * cell + cell / 2) * bpp;
            if (offset + channels > img.data.size())
                return false;
            for (int c = 0; c < 3; c++)
                color[(static_cast<size_t>(y) * gw + x) * 3 + c] = img.data[offset + std::min(c, channels - 1)];
        }
    }

    // Flood fill: every sample gets the id of its region
    struct Region { int count; int min_x, max_x, min_y, max_y; double sum_x; };
    std::vector<int> label(static_cast<size_t>(gw) * gh, -1);
    std::vector<Region> regions;
    std::vector<int> stack;

    for (int start = 0; start < gw * gh; start++) {
        if (label[start] >= 0)
            continue;

        const int id = static_cast<int>(regions.size());
        Region r = { 0, gw, -1, gh, -1, 0.0 };
        label[start] = id;
        stack.clear();
        stack.push_back(start);

        while (!stack.empty()) {
            const int current = stack.back();
            stack.pop_back();
            const int cx = current % gw;
            const int cy = current / gw;
            r.count++;
            r.sum_x += cx;
            r.min_x = std::min(r.min_x, cx);
            r.max_x = std::max(r.max_x, cx);
            r.min_y = std::min(r.min_y, cy);
            r.max_y = std::max(r.max_y, cy);

            const int dx[4] = { 1, -1, 0, 0 };
            const int dy[4] = { 0, 0, 1, -1 };
            for (int k = 0; k < 4; k++) {
                const int nx = cx + dx[k];
                const int ny = cy + dy[k];
                if (nx < 0 || ny < 0 || nx >= gw || ny >= gh)
                    continue;
                const int next = ny * gw + nx;
                if (label[next] >= 0)
                    continue;
                const unsigned char* p = &color[static_cast<size_t>(current) * 3];
                const unsigned char* q = &color[static_cast<size_t>(next) * 3];
                if (std::abs(p[0] - q[0]) + std::abs(p[1] - q[1]) + std::abs(p[2] - q[2]) <= tolerance) {
                    label[next] = id;
                    stack.push_back(next);
                }
            }
        }
        regions.push_back(r);
    }

    int best_count = 0;
    double best_column = 0.0;

    for (size_t id = 0; id < regions.size(); id++) {
        const Region& r = regions[id];

        // Size; a region touching the border is a wall, the floor or a cut object
        if (r.count < min_samples || r.count > gw * gh / 4)
            continue;
        if (r.min_x == 0 || r.min_y == 0 || r.max_x == gw - 1 || r.max_y == gh - 1)
            continue;

        // Bounding box and fill ratio of a disc (looser for small regions)
        const bool small_region = r.count < small_region_samples;
        const double w = r.max_x - r.min_x + 1;
        const double h = r.max_y - r.min_y + 1;
        const double aspect = w / h;
        const double fill = r.count / (w * h);
        const double lo_fill = small_region ? 0.6 : min_fill;
        const double hi_fill = small_region ? 0.92 : max_fill;
        const double lo_aspect = small_region ? 0.6 : min_aspect;
        const double hi_aspect = small_region ? 1.7 : max_aspect;
        if (aspect < lo_aspect || aspect > hi_aspect || fill < lo_fill || fill > hi_fill)
            continue;

        // Floor contact: lowest row below the horizon (image center row), over the apparent diameter
        const double diameter_px = (w + h) / 2.0 * cell;
        const double below_horizon_px = (r.max_y + 1) * cell - img.height / 2.0;
        const double expected_ratio = camera_height / ball_diameter;
        const double ratio = below_horizon_px / diameter_px;
        if (std::abs(ratio - expected_ratio) > ground_tolerance * expected_ratio)
            continue;

        // Every row must have the width of a disc (rejects boxes with rounded corners and irregular patches)
        const double radius = (w + h) / 4.0;
        const double center_y = (r.min_y + r.max_y) / 2.0;
        double deviation = 0.0;
        for (int y = r.min_y; y <= r.max_y; y++) {
            int row_width = 0;
            for (int x = r.min_x; x <= r.max_x; x++)
                if (label[static_cast<size_t>(y) * gw + x] == static_cast<int>(id))
                    row_width++;
            const double t = std::min(1.0, std::abs(y - center_y) / radius);
            deviation += std::abs(row_width - 2.0 * radius * std::sqrt(1.0 - t * t));
        }
        if (!small_region && deviation / (h * 2.0 * radius) > max_profile_error)
            continue;

        // Mean color of the region
        double sum_r = 0.0, sum_g = 0.0, sum_b = 0.0;
        for (int y = r.min_y; y <= r.max_y; y++) {
            for (int x = r.min_x; x <= r.max_x; x++) {
                if (label[static_cast<size_t>(y) * gw + x] != static_cast<int>(id))
                    continue;
                const unsigned char* c = &color[(static_cast<size_t>(y) * gw + x) * 3];
                sum_r += c[0];
                sum_g += c[1];
                sum_b += c[2];
            }
        }
        if (!is_supported_color(sum_r / r.count, sum_g / r.count, sum_b / r.count))
            continue;

        if (r.count > best_count) {
            best_count = r.count;
            best_column = (r.sum_x / r.count) * cell + cell / 2.0;
        }
    }

    if (best_count == 0)
        return false;

    column = best_column;
    return true;
}

// Splits the image in three vertical bands: ball on the left turns left, in the middle drives forward,
// on the right turns right. No ball stops the robot.
void process_image_callback(const sensor_msgs::Image img)
{
    static int last_state = -1;

    double column = 0.0;
    const bool found = detect_any_color ? find_ball_any_color(img, column) : find_white_ball(img, column);

    float lin_x = 0.0, ang_z = 0.0;
    int state = 0;                            // 0 = no ball, 1 = left, 2 = middle, 3 = right
    if (found) {
        const double third = img.width / 3.0;
        if (column < third) {
            state = 1;
            ang_z = 0.5;
        } else if (column > 2.0 * third) {
            state = 3;
            ang_z = -0.5;
        } else {
            state = 2;
            lin_x = 0.5;
        }
    }

    if (state != last_state) {
        static const char* names[] = { "no ball: stop", "ball on the left: turn left", "ball in the middle: drive forward", "ball on the right: turn right" };
        ROS_INFO("%s", names[state]);
        last_state = state;
    }

    drive_robot(lin_x, ang_z);
}

int main(int argc, char** argv)
{
    ros::init(argc, argv, "process_image");
    ros::NodeHandle n;

    ros::NodeHandle private_n("~");
    std::string target_color;
    private_n.param<std::string>("target_color", target_color, "any");
    detect_any_color = (target_color != "white");
    private_n.param<double>("ball_diameter", ball_diameter, 0.2);
    private_n.param<double>("camera_height", camera_height, 0.15);
    private_n.param<double>("ground_tolerance", ground_tolerance, 0.4);
    ROS_INFO("Chasing balls of color: %s", detect_any_color ? "any" : "white");

    client = n.serviceClient<ball_chaser::DriveToTarget>("/ball_chaser/command_robot");
    ros::Subscriber sub1 = n.subscribe("/camera/rgb/image_raw", 10, process_image_callback);

    ros::spin();

    return 0;
}
