# 基于UDP通信的Openloong-dora工作流示例

基于dora框架的open-loong关节控制和机械臂控制实现。
关节控制和机械臂控制sdk部分来自[openloong仓库](https://github.com/loongOpen/loong_sim_sdk_release.git)
## 文件结构

```
openloong-dora-udp/
├── servers/
│   ├── loong_jnt_server.py      # 关节控制服务端
│   ├── loong_mani_server.py     # 机械臂控制服务端
│   └── sim_server.py            # 模拟服务端（参考实现）
├── workflow/
│   ├── loong_jnt_client.py      # 关节控制客户端（dora节点）
│   ├── loong_mani_client.py     # 机械臂控制客户端（dora节点）
│   ├── dataflow.yml             # 工作流配置
│   ├── workflow_orchestrator.py # 工作流编排器
│   └── sdk_demo.py              # SDK使用示例
├── sdk/
│   ├── loong_jnt_sdk/           # 关节控制SDK
│   └── loong_mani_sdk/          # 机械臂控制SDK
└── test_implementation.py       # 测试脚本
```


## 安装和运行

### 1. 环境准备
```bash
# 安装依赖
pip install numpy
```

### 2. 启动服务端
```bash
# 启动关节控制服务端（端口8081）
python servers/loong_jnt_server.py

# 启动机械臂控制服务端（端口8080）
python servers/loong_mani_server.py
```

### 3. 启动工作流
```bash
dora run workflow/dataflow.yml --uv
```


