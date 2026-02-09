---
name: surge-configuration
description: Surge proxy utility configuration assistance covering profile authoring, troubleshooting, optimization, and best practices. Handles rules, policies, Smart groups, Ponte, Gateway mode, DNS, MITM, detached profiles, and proxy providers. Use when editing Surge .conf/.dconf files, troubleshooting Surge network issues, optimizing Surge setups, or when the user mentions Surge configuration.
---

# Surge Configuration Assistant

## Documentation Priority

When answering Surge questions, always follow this source priority:

1. **Release Log** (appcast): Most up-to-date, overrides others on conflicts
   - `https://nssurge.com/mac/latest/appcast-signed-beta.xml`
2. **Surge Manual** (authoritative reference): Exact option definitions
   - `https://manual.nssurge.com/` | LLM: `https://manual.nssurge.com/llms.txt`
3. **Surge Knowledge Base** (guides & FAQs): Tutorials, troubleshooting, best practices
   - `https://kb.nssurge.com/surge-knowledge-base/zh` | LLM: `https://kb.nssurge.com/llms.txt`

**Always use Context7 MCP tools** to fetch latest docs when generating config or setup steps.

## Profile Structure

Surge config is INI format with `[Section]` segments:

```ini
[General]        # Global settings (key = value)
[Ponte]          # Surge Ponte private network
[Proxy]          # Proxy server definitions
[Proxy Group]    # Policy groups (select, smart, fallback, url-test, subnet, load-balance)
[Rule]           # Traffic routing rules (ORDER MATTERS)
[Host]           # Local DNS mapping
[URL Rewrite]    # URL rewrite rules
[Header Rewrite] # Header modification
[Map Local]      # Mock local responses
[SSID Setting]   # Per-network settings
[MITM]           # HTTPS decryption config
[WireGuard xxx]  # WireGuard interface definitions
```

### Detached Profile (Config Separation)

Use `#!include` to split config into modules:

```ini
[Proxy]
#!include config/proxy-cloud.dconf, config/proxy-home.dconf

[Rule]
#!include config/vpn.dconf, surge.conf
```

- `#!include` cannot be mixed with regular content: If a section uses `#!include`, it can only contain `#!include` directives (and comments), and cannot contain regular rule/definition lines at the same time. If additional content needs to be added, it should be placed in the referenced dconf file.
- Referenced file MUST contain corresponding `[Section]` declaration
- Suffix convention: `.conf` for complete configs, `.dconf` for partial segments
- One level of include only (no nested includes)
- Multiple includes in one section → section becomes read-only in UI
- Can include managed profile URLs directly (Linked Profile, Mac 6.0+)

## Key Policy Groups

### Smart Group (Recommended over url-test/fallback)

```ini
Proxy = smart, ProxyA, ProxyB, ProxyC, interval=600, timeout=5
```

- Real-time dynamic optimization with per-site tuning
- Adaptive retry: failover mid-connection without user noticing
- Weight tuning: `policy-priority="Premium:0.9;SG:1.3"` (<1 = higher priority)
- Cannot use other groups as sub-policies
- Cannot handle geo-lock detection
- Snell reuse conflict resolved in Mac 6.0+

### Subnet Group

```ini
VPN跳板 = subnet, default = Home, "SSID:MyWiFi" = DIRECT, "ROUTER:192.168.2.1" = DIRECT
```

Auto-switch based on network environment. Match types: `SSID:`, `BSSID:`, `ROUTER:`, `TYPE:` (CELLULAR/WIFI/WIRED), `DEVICE-NAME:`.

### Fallback / URL-Test

```ini
可用切换 = fallback, ProxyA, ProxyB, interval=600, timeout=5
自动测速 = url-test, ProxyA, ProxyB, interval=600, tolerance=100, timeout=5
```

- `tolerance` (url-test only, default 100ms): prevents unnecessary switching
- `evaluate-before-use=true`: block requests until first test completes
- Error classification (A-E) determines auto-retest triggers

## Rule Writing Best Practices

Rules are matched top-to-bottom. First match wins.

```ini
[Rule]
# Domain rules first (no DNS needed)
DOMAIN-SUFFIX,google.com,Proxy
DOMAIN,specific.example.com,DIRECT

# Then IP rules (trigger DNS resolution)
IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
GEOIP,CN,DIRECT

# Final catch-all
FINAL,Proxy,dns-failed
```

### Key principles:
1. **Put non-DNS rules before DNS-triggering rules** to avoid unnecessary resolution
2. **Add `no-resolve`** to IP rules when possible to skip DNS
3. **Use `dns-failed`** on FINAL with proxy policy to handle DNS failures gracefully
4. **Use `extended-matching`** for rules that should also match via SNI/Host sniffing

### Accessing home network from outside:

```ini
# Only route home network when NOT at home
AND,((NOT,((SUBNET,ROUTER:192.168.2.1))), (IP-CIDR,192.168.2.0/24,no-resolve)),Home
```

## DNS Configuration

### General DNS setup:

```ini
[General]
dns-server = 223.5.5.5, 114.114.114.114           # Traditional DNS
encrypted-dns-server = tls://223.5.5.5             # DoT/DoH
hijack-dns = 8.8.8.8:53, 8.8.4.4:53               # Hijack hardcoded DNS
always-real-ip = *.srv.nintendo.net, *.stun.playstation.net  # Preserve NAT type
```

### DNS resolution flow:
- Surge triggers local DNS only for: IP-type rules (without `no-resolve`), proxy server hostname, DIRECT policy
- With proxy policy, DNS resolves on proxy server side (optimal)
- `use-local-host-item-for-proxy = true`: use local Host mapping for proxy connections

### Per-network DNS (SSID Setting):

```ini
[SSID Setting]
SSID:HomeWiFi dns-server="192.168.2.1", encrypted-dns-server="off"
```

## Gateway Mode (Mac as Router)

### Two modes:
1. **Enhanced Mode (Surge VIF)**: Also handles local device traffic
2. **Surge VM Gateway** (Mac 6.0+): Better performance, Layer 2, but conflicts with VM bridging

### Client setup:
- Gateway: Surge Mac's IP (or VM Gateway IP)
- DNS: `198.18.0.2` (IPv4) / `fd00:6152::2` (IPv6)

### DHCP auto-config:
- Disable router's DHCP first
- Surge Mac must use wired connection + static IP
- IPv6 RA Override for complete IPv6 takeover

### Performance notes:
- P2P apps can overwhelm Surge (works at L7, not L3)
- VM UDP Fast Path: auto-activates for UDP-heavy clients (≥10/1s or ≥30/10s)
- PS Portal workaround: `IP-CIDR,<PS5-IP>/32,REJECT-DROP,pre-matching,no-resolve`

## Surge Ponte (Private Network)

### Server setup (Mac):
```ini
[Ponte]
server-proxy-name = ProxyForNAT  # or omit for direct NAT traversal
```

### Client usage:
```ini
[Ponte]
server-proxy-name = "🏡 Home"     # As Ponte server
# OR
client-proxy-name = Home           # As Ponte client only
```

### Access patterns:
- Domain: `ponte-name.sgponte` (e.g., `mymacmini.sgponte:8080`)
- Policy: `DEVICE:PONTE-NAME` as proxy to use that device as gateway
- Rule: `IP-CIDR,192.168.30.0/24,DEVICE:MyMacMini`

### Requirements:
- Same iCloud account across devices
- Full Cone NAT (A-type) for direct traversal, or use proxy for NAT traversal
- Mac 6.0+: Multiple channels, IPv6 direct, auto-select fastest

## REJECT Policies

| Policy | Behavior |
|--------|----------|
| `REJECT` | Return error page (HTTP) or close connection |
| `REJECT-TINYGIF` | Return 1px GIF (for web ad blocking) |
| `REJECT-DROP` | Silent drop (prevents retry storms) |
| `REJECT-NO-DROP` | Same as REJECT but never auto-upgrades to DROP |

Auto-upgrade: 10+ REJECTs in 30s → automatically becomes REJECT-DROP.

## MITM Configuration

```ini
[MITM]
skip-server-cert-verify = true
tcp-connection = true
h2 = true                    # Enable HTTP/2 for MITM
hostname = *.example.com     # Domains to decrypt
hostname-disabled = ...      # Temporarily disabled domains
```

- SSL Pinning apps (Apple, Facebook, Instagram, X) cannot be MITM'd
- iOS 15+: UA not visible in CONNECT requests without MITM

## Proxy Provider Integration

### Three modes:
1. **Managed profile**: Full config from provider (read-only)
2. **Linked profile**: Track `[Proxy]` + `[Proxy Group]` from managed, edit rest locally
3. **External policy group** (recommended for advanced users):

```ini
Provider = select, policy-path=https://airport.com/surge.conf, hidden=true
US-Nodes = smart, include-other-group=Provider, policy-regex-filter=US|美国
```

### Multi-provider fusion:

```ini
Awesome = select, policy-path=https://a.com/surge.conf, hidden=true, external-policy-name-prefix=A-
Fantastic = select, policy-path=https://b.com/surge.conf, hidden=true, external-policy-name-prefix=B-
All-US = smart, include-other-group="Awesome,Fantastic", policy-regex-filter=US|美国
```

### Relay (chain proxy):

```ini
Provider = select, policy-path=https://provider.com/surge.conf, external-policy-modifier="underlying-proxy=JumpProxy"
```

## Snell v5 Protocol

- Dynamic Record Sizing: better latency under packet loss
- QUIC Proxy Mode: UDP-over-UDP for QUIC traffic (avoids TCP-over-UDP issues)
- Shadow TLS v3 support
- Server download: check KB release notes

```ini
Proxy = snell, server.com, 8443, psk=xxx, version=5, reuse=true, tfo=true, shadow-tls-password=xxx, shadow-tls-sni=www.microsoft.com, shadow-tls-version=3
```

## Troubleshooting Quick Reference

| Symptom | Check |
|---------|-------|
| Request not in Dashboard | Takeover issue: check system proxy (`scutil --proxy`) or enhanced mode (`ping apple.com` → `198.18.x.x`) |
| Request appears but fails | Forwarding issue: check Notes tab for error (Connection refused/timeout/No DNS) |
| Only IPs, no domains | DNS not pointing to `198.18.0.2`; or encrypted DNS bypassing Fake IP |
| High battery on iOS | Normal: all network traffic counted under Surge; actual extra <2%/24h |
| QUIC blocked | Expected: TCP proxy + QUIC = double retransmission; use Snell v5 QUIC mode if needed |
| NAT type degraded | Configure `always-real-ip` for STUN domains |
| "Network quality poor" | Check DNS servers (avoid 8.8.8.8 in mainland China) |

## Additional Resources

- For complete option reference, fetch: `https://manual.nssurge.com/llms.txt`
- For KB guides and FAQs, fetch: `https://kb.nssurge.com/llms.txt`
- For latest changes, fetch: `https://nssurge.com/mac/latest/appcast-signed-beta.xml`
