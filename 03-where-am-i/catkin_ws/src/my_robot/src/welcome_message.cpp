#include <gazebo/gazebo.hh>

namespace gazebo
{
  class WelcomeMessage : public WorldPlugin
  {
  public:
    WelcomeMessage() : WorldPlugin()
    {
      printf("Welcome to Alessio's World!\n");
    }

    void Load(physics::WorldPtr _world, sdf::ElementPtr _sdf)
    {
    }
  };

  GZ_REGISTER_WORLD_PLUGIN(WelcomeMessage)
}
