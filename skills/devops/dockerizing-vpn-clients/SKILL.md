---
name: dockerizing-vpn-clients
description: Use when containerizing VPN clients into Docker, supporting both GUI (VNC) and CLI (Web management) modes with danted SOCKS5 proxy
---

# Dockerizing VPN Clients

将 VPN 客户端封装到 Docker 容器中，提供 SOCKS5 代理出口。支持两种模式：GUI 客户端使用 VNC，CLI 客户端使用 Web 管理界面。

## Decision Flow

```
VPN 客户端是否有 GUI？
├─ YES → 模式 A: VNC + Supervisor
│        ├─ xvfb 虚拟显示
│        ├─ x11vnc/tigervnc 远程访问
│        └─ 轻量桌面 (XFCE4/flwm)
│
└─ NO → 模式 B: Web 管理 + lighttpd
         ├─ lighttpd 提供 Web UI
         ├─ CGI 脚本封装 VPN 命令
         └─ 前端展示状态/控制连接
```

## Core Components

| 组件 | 作用 | 工具选择 |
|------|------|----------|
| VPN 客户端 | 建立 VPN 隧道，创建 tun0 | 原厂客户端 |
| 代理层 | SOCKS5 代理出口 | danted (端口 1080) |
| 管理层 | 用户交互界面 | VNC / lighttpd+CGI |
| 网络层 | NAT 转发 | iptables MASQUERADE |

## Implementation Steps

### 模式 A: GUI 客户端 (VNC)

1. **Dockerfile 基础设置**
   - 基础镜像: `debian:12-slim`
   - 安装: `xvfb`, `x11vnc`, `supervisor`, `xfce4`, `dante-server`
   - 设置环境变量: `DISPLAY=:0`, `VNC_PASSWORD`

2. **Supervisor 进程管理**
   ```ini
   [program:xvfb]
   command=Xvfb :0 -screen 0 1024x768x24
   priority=1
   
   [program:x11vnc]
   command=x11vnc -display :0 -forever -rfbport 5900 -rfbauth /root/.vnc/passwd
   priority=2
   
   [program:vpn]
   command=/opt/start.sh
   priority=3
   ```

3. **端口暴露**: 5900 (VNC), 1080 (SOCKS5)

### 模式 B: CLI 客户端 (Web 管理)

1. **Dockerfile 基础设置**
   - 基础镜像: `debian:12-slim`
   - 安装: `lighttpd`, `dante-server`, `curl`, `iproute2`, `iptables`
   - 复制 Web 资源到 `/var/www/html/` 和 `/var/www/cgi-bin/`

2. **lighttpd 配置**
   ```lighttpd
   server.modules = ("mod_indexfile", "mod_cgi", "mod_alias")
   server.port = 8080
   cgi.assign = ( ".cgi" => "" )
   $HTTP["url"] =~ "^/cgi-bin/" {
       alias.url = ( "/cgi-bin/" => "/var/www/cgi-bin/" )
   }
   ```

3. **CGI API 端点**
   - `?action=status` - 查询连接状态
   - `?action=connect` - 执行连接
   - `?action=disconnect` - 断开连接

4. **端口暴露**: 8080 (Web), 1080 (SOCKS5)

## Common Patterns

### 等待 tun0 后启动 danted

```bash
(while true; do
    sleep 5
    if [ -d /sys/class/net/tun0 ] && ! pgrep -x danted > /dev/null 2>&1; then
        su daemon -s /bin/sh -c "/usr/sbin/danted -f /run/danted.conf"
    fi
done) &
```

### 动态检测网络接口

```bash
externals=""
for iface in $({ ip -f inet -o addr; ip -f inet6 -o addr; } | sed -E 's/^[0-9]+: ([^ ]+) .*/\1/'); do
    externals="${externals}external: $iface\\n"
done
sed s/^#external-lines/"$externals"/ -i /run/danted.conf
```

### NAT 配置 (幂等)

```bash
update-alternatives --set iptables /usr/sbin/iptables-legacy 2>/dev/null || true
iptables -t nat -C POSTROUTING -o tun0 -j MASQUERADE 2>/dev/null || \
    iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE
```

### 安全规则

```bash
# 拒绝 tun0 侧主动连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i tun0 -p tcp -j DROP
```

### CGI JSON 响应

```bash
echo "Content-Type: application/json"
echo ""
echo '{"success": true, "data": {...}}'
```

## Templates Quick Reference

| 文件 | 用途 | 模式 |
|------|------|------|
| `Dockerfile.gui` | GUI 模式镜像 | GUI |
| `Dockerfile.cli` | CLI 模式镜像 | CLI |
| `supervisord.conf` | Supervisor 进程管理 | GUI |
| `start-gui.sh` | GUI 模式启动脚本 | GUI |
| `start.sh` | CLI 模式启动脚本 | CLI |
| `danted.conf` | SOCKS5 代理配置 | 通用 |
| `lighttpd.conf` | Web 服务器配置 | CLI |
| `api.cgi` | CGI API 脚本 | CLI |

所有模板位于 [templates/](templates/) 目录。

## Docker Run 示例

```bash
# GUI 模式
docker run -d --name vpn \
    --cap-add NET_ADMIN \
    --device /dev/net/tun \
    -p 5900:5900 \
    -p 1080:1080 \
    -v ./config:/opt/vpn/conf \
    vpn-client:gui

# CLI 模式
docker run -d --name vpn \
    --cap-add NET_ADMIN \
    --device /dev/net/tun \
    -p 8080:8080 \
    -p 1080:1080 \
    -v ./config:/opt/vpn/conf \
    vpn-client:cli
```

## Checklist

实现前检查：
- [ ] 确认 VPN 客户端类型 (GUI/CLI)
- [ ] 确认客户端支持的架构 (amd64/arm64)
- [ ] 获取 VPN 客户端安装包

实现后验证：
- [ ] 容器启动无错误
- [ ] VPN 可成功连接 (tun0 创建)
- [ ] danted 在 tun0 创建后自动启动
- [ ] SOCKS5 代理可用 (`curl --socks5 localhost:1080 ...`)
- [ ] 管理界面可访问 (VNC:5900 或 Web:8080)
- [ ] NAT 转发正常工作

## Anti-Patterns

| 错误做法 | 正确做法 |
|----------|----------|
| 在 tun0 创建前启动 danted | 后台循环检测 tun0 后启动 |
| 直接使用 iptables-nft | 切换到 iptables-legacy |
| 硬编码网络接口 | 动态检测所有接口 |
| 同步等待 VPN 连接 | 后台重试，不阻塞启动 |
