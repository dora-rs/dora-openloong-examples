#!/usr/bin/env bash
set -euo pipefail

# OpenLoong 仿真 + SDK + Dora 一键启动脚本
# 整合 tools 文件夹中的启动脚本，根据参数确定启动 mani 还是 loco

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"
TOOLS_DIR="$ROOT_DIR/loong_sim_sdk_release/tools"
BIN_DIR="$ROOT_DIR/loong_sim_sdk_release/bin"
LOG_DIR="$ROOT_DIR/loong_sim_sdk_release/log"
WORKFLOW_DIR="$ROOT_DIR/workflow"

# 默认配置
MODE="both"  # both, mani, loco
ARCH=""
PIDS=()

# 检测架构
detect_arch() {
    if [ "$(arch)" = "x86_64" ]; then
        ARCH="x64"
    else
        ARCH="a64"
    fi
    echo "检测到架构: $ARCH"
}

# 创建日志目录并清理旧日志
setup_logs() {
    if [ ! -e "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
    else
        echo "清理旧日志文件（保留最近20个）..."
        cd "$LOG_DIR"
        files=$(ls -lt | tail -n +21 | awk '{print $9}')
        for file in $files; do
            sudo rm -f "$file" 2>/dev/null || true
        done
    fi
    echo "=========="
}

# 启动后台进程
start_bg() {
    local name="$1"
    local log_file="$LOG_DIR/${name}.log"
    echo "[启动] $name (日志: $log_file)"
    "$@" >"$log_file" 2>&1 &
    local pid=$!
    PIDS+=("$pid")
    echo "PID: $pid"
}

# 启动仿真器
start_sim() {
    echo "[启动] 仿真器..."
    cd "$BIN_DIR"
    ./loong_share_sim_$ARCH &
    local pid=$!
    PIDS+=("$pid")
    echo "仿真器 PID: $pid"
}

# 启动驱动
start_driver() {
    echo "[启动] 驱动..."
    cd "$BIN_DIR"
    sudo ./loong_driver_$ARCH | sudo tee "$LOG_DIR/terminal_driver.txt" &
    local pid=$!
    PIDS+=("$pid")
    echo "驱动 PID: $pid"
}

# 启动接口
start_interface() {
    echo "[启动] 接口..."
    cd "$BIN_DIR"
    sudo ./loong_interface_$ARCH | sudo tee "$LOG_DIR/terminal_interface.txt" &
    local pid=$!
    PIDS+=("$pid")
    echo "接口 PID: $pid"
}

# 启动运动控制
start_locomotion() {
    echo "[启动] 运动控制..."
    cd "$BIN_DIR"
    sudo ./loong_locomotion_$ARCH | sudo tee "$LOG_DIR/terminal_loco.txt" &
    local pid=$!
    PIDS+=("$pid")
    echo "运动控制 PID: $pid"
}

# 启动操作控制
start_manipulation() {
    echo "[启动] 操作控制..."
    cd "$BIN_DIR"
    sudo ./loong_manipulation_$ARCH | sudo tee "$LOG_DIR/terminal_mani.txt" &
    local pid=$!
    PIDS+=("$pid")
    echo "操作控制 PID: $pid"
}

# 清理函数
cleanup() {
    echo -e "\n[清理] 停止后台进程..."
    for pid in "${PIDS[@]:-}"; do
        if kill -0 "$pid" >/dev/null 2>&1; then
            echo "停止进程 $pid"
            kill "$pid" >/dev/null 2>&1 || true
        fi
    done
    
    # 等待进程结束
    sleep 1
    
    # 强制终止仍在运行的进程
    for pid in "${PIDS[@]:-}"; do
        if kill -0 "$pid" >/dev/null 2>&1; then
            echo "强制停止进程 $pid"
            kill -9 "$pid" >/dev/null 2>&1 || true
        fi
    done
    
    echo "清理完成"
}

# 显示使用说明
usage() {
    echo "OpenLoong 仿真 + SDK + Dora 一键启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --mani     仅启动操作控制 (manipulation)"
    echo "  --loco     仅启动运动控制 (locomotion)"
    echo "  --both     启动运动控制和操作控制 (默认)"
    echo "  -h, --help 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 启动所有组件"
    echo "  $0 --mani         # 仅启动操作控制"
    echo "  $0 --loco         # 仅启动运动控制"
    echo "  $0 --both         # 启动运动控制和操作控制"
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --mani)
                MODE="mani"
                shift
                ;;
            --loco)
                MODE="loco"
                shift
                ;;
            --both)
                MODE="both"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "未知参数: $1" >&2
                usage
                exit 1
                ;;
        esac
    done
}

# 检查依赖
check_dependencies() {
    local missing=()
    
    if ! command -v dora >/dev/null 2>&1; then
        missing+=("dora")
    fi
    
    if ! command -v sudo >/dev/null 2>&1; then
        missing+=("sudo")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "缺少必需的命令: ${missing[*]}" >&2
        exit 1
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "OpenLoong 仿真 + SDK + Dora 一键启动脚本"
    echo "=========================================="
    
    # 解析参数
    parse_args "$@"
    
    # 检查依赖
    check_dependencies
    
    # 检测架构
    detect_arch
    
    # 设置日志
    setup_logs
    
    # 设置清理陷阱
    trap cleanup EXIT INT TERM
    
    echo "启动模式: $MODE"
    echo ""
    
    # 启动核心组件
    echo "1. 启动仿真器..."
    start_sim
    sleep 2
    
    echo "2. 启动驱动..."
    start_driver
    sleep 2
    
    echo "3. 启动接口..."
    start_interface
    sleep 2
    
    # 根据模式启动相应组件
    case "$MODE" in
        "mani")
            echo "4. 启动操作控制..."
            start_manipulation
            ;;
        "loco")
            echo "4. 启动运动控制..."
            start_locomotion
            ;;
        "both")
            echo "4. 启动运动控制..."
            start_locomotion
            sleep 1
            echo "5. 启动操作控制..."
            start_manipulation
            ;;
    esac
    
    echo ""
    echo "等待 SDK 进程初始化..."
    sleep 3
    
    echo "=========================================="
    echo "SDK 组件启动完成"
    echo "按 Ctrl-C 停止所有进程"
    echo "=========================================="
    
    # 保持脚本运行，等待用户中断
    while true; do
        sleep 1
    done
}

# 运行主函数
main "$@"


