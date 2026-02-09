#!/bin/bash
# VPN 管理 API - CGI 脚本模板
# 支持的操作: status, connect, disconnect, debug
#
# 使用方法:
# - GET /cgi-bin/api.cgi?action=status
# - GET /cgi-bin/api.cgi?action=connect
# - GET /cgi-bin/api.cgi?action=disconnect
# - GET /cgi-bin/api.cgi?action=debug

# ============================================================
# 配置 - 根据实际 VPN 客户端修改
# ============================================================

# VPN 客户端可能的路径
VPN_CMD_PATHS=(
    "/opt/vpn/vpnclient"
    "/usr/local/bin/vpnclient"
    "/usr/bin/vpnclient"
)

# VPN 命令
VPN_CONNECT_CMD="quickconnect"
VPN_DISCONNECT_CMD="disconnect"
VPN_STATUS_CMD="showinfo"

# ============================================================
# 输出 JSON 响应头
# ============================================================

echo "Content-Type: application/json"
echo ""

# ============================================================
# 解析 action 参数
# ============================================================

ACTION=""
if [ -n "$QUERY_STRING" ]; then
    ACTION=$(echo "$QUERY_STRING" | sed -n 's/.*action=\([^&]*\).*/\1/p')
fi

# ============================================================
# 查找 VPN 客户端
# ============================================================

VPN_CMD=""
for p in "${VPN_CMD_PATHS[@]}"; do
    if [ -x "$p" ]; then
        VPN_CMD="$p"
        break
    fi
done

if [ -z "$VPN_CMD" ]; then
    echo '{"success":false,"error":"VPN 客户端未找到"}'
    exit 0
fi

# ============================================================
# 工具函数
# ============================================================

# 检查 tun0 接口是否存在
check_tun0() {
    [ -d /sys/class/net/tun0 ]
}

# 检查 SOCKS5 代理状态
check_socks5() {
    pgrep -x danted > /dev/null 2>&1
}

# JSON 转义函数
json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\t/\\t/g' | tr -d '\r'
}

# 获取 tun0 路由表
get_tun0_routes() {
    local routes=""
    while IFS= read -r line; do
        route=$(echo "$line" | awk '{print $1}')
        if [ -n "$route" ] && [ "$route" != "default" ]; then
            if [ -n "$routes" ]; then
                routes="$routes,"
            fi
            routes="$routes\"$route\""
        fi
    done <<< "$(ip route show dev tun0 2>/dev/null)"
    echo "$routes"
}

# ============================================================
# 解析 VPN 状态输出为 JSON
# 注意: 此函数需要根据实际 VPN 客户端输出格式修改
# ============================================================

parse_vpn_info() {
    local output="$1"
    local socks5_status="false"
    
    if check_socks5; then
        socks5_status="true"
    fi
    
    # TODO: 根据实际 VPN 客户端输出格式解析
    # 以下是示例解析逻辑
    local login_user server_ip private_ip
    
    login_user=$(echo "$output" | grep -i "Login User" | sed 's/.*Login User[[:space:]]*:[[:space:]]*//' | tr -d '\r')
    server_ip=$(echo "$output" | grep -i "Server" | sed 's/.*Server[[:space:]]*:[[:space:]]*//' | tr -d '\r')
    private_ip=$(echo "$output" | grep -i "Private IP" | sed 's/.*Private IP[[:space:]]*:[[:space:]]*//' | tr -d '\r')
    
    # 获取路由表
    local targets
    targets=$(get_tun0_routes)
    
    printf '{"connected":true,"socks5":%s,"info":{"loginUser":"%s","serverIp":"%s","privateIp":"%s","targets":[%s]}}' \
        "$socks5_status" \
        "$(json_escape "$login_user")" \
        "$(json_escape "$server_ip")" \
        "$(json_escape "$private_ip")" \
        "$targets"
}

# ============================================================
# 处理不同的 action
# ============================================================

case "$ACTION" in
    status)
        socks5_status="false"
        if check_socks5; then
            socks5_status="true"
        fi
        
        if check_tun0; then
            # VPN 已连接，获取详细信息
            cd "$(dirname "$VPN_CMD")" 2>/dev/null || true
            info_output=$("$VPN_CMD" ${VPN_STATUS_CMD} 2>&1)
            
            if [ -n "$info_output" ]; then
                parse_vpn_info "$info_output"
            else
                printf '{"connected":true,"socks5":%s,"info":null}' "$socks5_status"
            fi
        else
            printf '{"connected":false,"socks5":%s}' "$socks5_status"
        fi
        ;;
    
    connect)
        # 执行连接
        cd "$(dirname "$VPN_CMD")" 2>/dev/null || true
        output=$("$VPN_CMD" ${VPN_CONNECT_CMD} 2>&1)
        exit_code=$?
        
        # 等待连接建立
        sleep 2
        
        if check_tun0; then
            echo '{"success":true,"message":"连接成功"}'
        else
            echo '{"success":true,"message":"连接命令已执行，请等待连接建立"}'
        fi
        ;;
    
    disconnect)
        # 执行断开连接
        cd "$(dirname "$VPN_CMD")" 2>/dev/null || true
        output=$("$VPN_CMD" ${VPN_DISCONNECT_CMD} 2>&1)
        
        sleep 1
        
        if ! check_tun0; then
            echo '{"success":true,"message":"已断开连接"}'
        else
            echo '{"success":false,"error":"断开连接失败"}'
        fi
        ;;
    
    debug)
        # 调试模式：返回原始信息
        cd "$(dirname "$VPN_CMD")" 2>/dev/null || true
        info_output=$("$VPN_CMD" ${VPN_STATUS_CMD} 2>&1)
        tun_exists="false"
        if check_tun0; then
            tun_exists="true"
        fi
        escaped_output=$(json_escape "$info_output")
        printf '{"vpn_cmd":"%s","tun0_exists":%s,"raw_output":"%s"}' "$VPN_CMD" "$tun_exists" "$escaped_output"
        ;;
    
    *)
        echo '{"success":false,"error":"无效的操作，支持: status, connect, disconnect, debug"}'
        ;;
esac
