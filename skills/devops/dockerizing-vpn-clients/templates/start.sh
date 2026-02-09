#!/bin/bash
# VPN Client Container 启动脚本模板
# 适用于 CLI 模式 (Web 管理)
set -e

echo "=== VPN Client Container Starting ==="

# ============================================================
# 配置变量 - 根据实际 VPN 客户端修改
# ============================================================

# VPN 客户端命令路径 (支持多路径查找)
VPN_CMD_PATHS=(
    "/opt/vpn/vpnclient"
    "/usr/local/bin/vpnclient"
    "/usr/bin/vpnclient"
)

# VPN 客户端命令
# - connect: 连接命令
# - disconnect: 断开命令  
# - status: 状态查询命令
VPN_CONNECT_CMD="quickconnect"
VPN_DISCONNECT_CMD="disconnect"
VPN_STATUS_CMD="showinfo"

# ============================================================
# 环境变量
# ============================================================

# 自动连接 (设置为 0 禁用)
AUTO_CONNECT="${AUTO_CONNECT:-1}"
# 自动连接重试间隔 (秒)
CONNECT_RETRY_INTERVAL="${CONNECT_RETRY_INTERVAL:-10}"

# ============================================================
# 查找 VPN 客户端
# ============================================================

find_vpn_cmd() {
    # 优先从环境变量
    if [ -n "${VPN_CMD}" ] && [ -x "${VPN_CMD}" ]; then
        echo "${VPN_CMD}"
        return
    fi
    
    # 从 PATH 查找
    local cmd
    cmd="$(command -v vpnclient 2>/dev/null || true)"
    if [ -n "${cmd}" ]; then
        echo "${cmd}"
        return
    fi
    
    # 遍历常见路径
    for p in "${VPN_CMD_PATHS[@]}"; do
        if [ -x "${p}" ]; then
            echo "${p}"
            return
        fi
    done
}

VPN_CMD="$(find_vpn_cmd)"

# ============================================================
# 自动连接 (后台)
# ============================================================

if [ "${AUTO_CONNECT}" != "0" ]; then
    (
        echo "[$(date)] Auto connect enabled (retry interval: ${CONNECT_RETRY_INTERVAL}s)"
        
        while true; do
            # 检查是否已连接
            if [ -d /sys/class/net/tun0 ]; then
                echo "[$(date)] VPN already connected"
                exit 0
            fi
            
            if [ -z "${VPN_CMD}" ] || [ ! -x "${VPN_CMD}" ]; then
                echo "[$(date)] VPN client not found"
            else
                echo "[$(date)] Running: ${VPN_CMD} ${VPN_CONNECT_CMD}"
                "${VPN_CMD}" ${VPN_CONNECT_CMD} 2>&1 || true
            fi
            
            sleep "${CONNECT_RETRY_INTERVAL}"
        done
    ) &
else
    echo "[$(date)] Auto connect disabled (AUTO_CONNECT=0)"
fi

# ============================================================
# 配置 danted SOCKS5 代理
# ============================================================

cp /etc/danted.conf.sample /run/danted.conf

# 动态添加网络接口
externals=""
for iface in $({ ip -f inet -o addr; ip -f inet6 -o addr; } | sed -E 's/^[0-9]+: ([^ ]+) .*/\1/'); do
    externals="${externals}external: $iface\\n"
done
sed s/^#external-lines/"$externals"/ -i /run/danted.conf

# ============================================================
# 后台监控 tun 设备并启动 danted
# ============================================================

(while true; do
    sleep 5
    # 检查 tun0 是否存在且 danted 未在运行
    if [ -d /sys/class/net/tun0 ] && ! pgrep -x danted > /dev/null 2>&1; then
        chmod a+w /tmp
        echo "[$(date)] Starting danted on port 1080..."
        su daemon -s /bin/sh -c "/usr/sbin/danted -f /run/danted.conf"
        sleep 1
        if pgrep -x danted > /dev/null 2>&1; then
            echo "[$(date)] danted started successfully"
        else
            echo "[$(date)] Failed to start danted"
        fi
    fi
done) &

# ============================================================
# 配置 iptables
# ============================================================

# 使用 iptables-legacy 确保兼容性
update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true

# 配置 NAT 转发 (当 tun0 存在时)
(while true; do
    sleep 5
    if [ -d /sys/class/net/tun0 ]; then
        # 幂等添加 MASQUERADE 规则
        iptables -t nat -C POSTROUTING -o tun0 -j MASQUERADE 2>/dev/null || \
            iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE
        
        # 安全规则：拒绝 tun0 侧主动连接
        iptables -C INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || \
            iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
        iptables -C INPUT -i tun0 -p tcp -j DROP 2>/dev/null || \
            iptables -A INPUT -i tun0 -p tcp -j DROP
        
        break
    fi
done) &

# ============================================================
# 启动 Web 管理页面 (CLI 模式)
# ============================================================

mkdir -p /var/log/lighttpd
echo "[$(date)] Starting Web Management UI on port 8080..."
lighttpd -f /etc/lighttpd/lighttpd.conf

echo "[$(date)] Container ready."
echo "[$(date)] - Web Management UI: http://localhost:8080"
echo "[$(date)] - SOCKS5 proxy: localhost:1080 (available after VPN connection)"

# ============================================================
# 保持容器运行
# ============================================================

tail -f /dev/null
