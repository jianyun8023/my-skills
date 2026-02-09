#!/bin/bash
# VPN Client Container 启动脚本模板
# 适用于 GUI 模式 (VNC + Supervisor)
set -x

# ============================================================
# 配置变量 - 根据实际 VPN 客户端修改
# ============================================================

# VPN 客户端路径 (根据架构选择)
# TODO: 根据实际客户端修改
VPN_CLIENT_AMD64="/opt/vpn/vpnclient"
VPN_CLIENT_ARM64="/opt/vpn/vpnclient-arm64"

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

[ -n "$NODANTED" ] || (while true; do
    sleep 5
    # 检查 tun0 是否存在且 danted 未在运行
    if [ -d /sys/class/net/tun0 ] && ! pgrep -x danted > /dev/null 2>&1; then
        chmod a+w /tmp
        echo "Starting danted on port 1080..."
        su daemon -s /usr/sbin/danted -f /run/danted.conf
        sleep 1
        if pgrep -x danted > /dev/null 2>&1; then
            echo "danted started successfully"
        else
            echo "Failed to start danted"
        fi
    fi
done) &

# ============================================================
# 配置 iptables
# ============================================================

# 使用 iptables-legacy 确保兼容性
update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy 2>/dev/null || true

# NAT 转发
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

# 安全规则：拒绝 tun0 侧主动连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i tun0 -p tcp -j DROP

# ============================================================
# 启动 VPN 相关服务 (如果需要)
# ============================================================

# TODO: 根据实际 VPN 客户端修改
# 例如: /etc/init.d/vpnservice restart

# ============================================================
# 启动 VPN 客户端 GUI
# ============================================================

echo "Architecture: $ARCH"
case "$ARCH" in
    arm64)
        if [ -x "$VPN_CLIENT_ARM64" ]; then
            exec "$VPN_CLIENT_ARM64"
        else
            echo "ARM64 VPN client not found: $VPN_CLIENT_ARM64"
            exit 1
        fi
        ;;
    amd64|*)
        if [ -x "$VPN_CLIENT_AMD64" ]; then
            exec "$VPN_CLIENT_AMD64"
        else
            echo "AMD64 VPN client not found: $VPN_CLIENT_AMD64"
            exit 1
        fi
        ;;
esac
