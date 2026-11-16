#!/usr/bin/env bash
# Compila i plugin (se servono) e avvia Gazebo Classic con MyWorld.world.
# Usa ros_env tramite micromamba se gazebo non e' nel PATH. Ricorda: elimina build/ prima di consegnare.
cd "$(dirname "$(readlink -f "$0")")"
RUN=()
command -v gazebo >/dev/null 2>&1 || RUN=("$HOME/.local/bin/micromamba" run -n ros_env)
if [ ! -f build/libwelcome_message.so ]; then
  mkdir -p build && (cd build && "${RUN[@]}" cmake .. && "${RUN[@]}" make) || exit 1
fi
export GAZEBO_MODEL_PATH="$PWD/model:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_PLUGIN_PATH="$PWD/build:${GAZEBO_PLUGIN_PATH:-}"
export IGN_IP="${IGN_IP:-127.0.0.1}"   # evita gli avvisi "Error advertising topic ... discovery service" della GUI
exec "${RUN[@]}" gazebo --verbose world/MyWorld.world "$@"
