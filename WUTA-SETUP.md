# WUTA CARLA 0.9.16 本机资源说明

本分支提供 CARLA 0.9.16 源码、本地 Chrono 脚本、FSAC 场景资源及锥桶 STEP。UE4 引擎、CARLA 官方内容包、第三方构建依赖、运行日志和编译结果需另行准备。上游构建说明见 [Docs](Docs/)；本机脚本使用及测试边界见 [架构文档](ARCHITECTURE.md) 和 [Chrono 快速说明](Build/CHRONO-QUICKSTART.md)。

## 本机约定

脚本目前包含绝对路径，默认 CARLA 位于 `/home/wuta/carla`，UE4.26 位于 `/home/wuta/UnrealEngine_4.26`，Conda 初始化脚本位于 `/home/wuta/miniforge3/etc/profile.d/conda.sh`，环境名称为 `carla`。迁移到其他机器时，先检查 `Build/` 下脚本中的路径、GPU Vulkan 配置和所需 Python/系统依赖，再执行构建或资源操作。

`Build/convert-cone.py` 的 CAD 输入为 `/home/wuta/下载/黄色小锥桶.STEP`。仓库根目录保存了同名 STEP；重新生成时应调整脚本中的输入路径，或将文件复制到该输入路径。

## 官方内容包

本机 `Build/prepare-content.sh` 使用版本号 `20250912_2171890`，从脚本指定的 CARLA 资源服务器下载 `Content.tar.gz` 并解压至 `Unreal/CarlaUE4/Content/Carla`。该包约 21 GB，未纳入 Git；UE4 引擎本身也不包含在仓库中。脚本会检查已有目标目录并拒绝覆盖。执行前请检查路径、磁盘空间、网络及版本，并阅读脚本的下载和解压逻辑。

## 本地构建与运行

准备好引擎、内容和依赖后，[Build/build-chrono.sh](Build/build-chrono.sh) 执行带 Chrono 支持的本机源码构建。启动 FSAC 地图：

```bash
env UE4_ROOT=/home/wuta/UnrealEngine_4.26 \
    CARLA_UE4_ROOT=/home/wuta/carla \
    bash /home/wuta/carla/Build/run-fsac.sh
```

这会启动世界；具体车辆是否使用 Chrono 由客户端配置。`Build/chrono-smoke.py` 是独立短测入口，会修改世界同步设置、创建车辆和碰撞传感器，并在结束时尝试恢复。该脚本把结果写到 `Build/config-logs/`；全新克隆首次运行前需创建该目录。历史日志不随仓库提供，需要重新运行以获得本机证据。

WUTA ROS 2/FSD 工程是外部项目，需另行准备和启动；本仓库不包含其完整闭环或 RViz 配置。启动成功和短时移动不能替代完整赛道测试。
