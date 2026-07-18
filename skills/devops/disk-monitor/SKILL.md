---
name: disk-monitor
description: Use when the user asks to check disk status, report on hard disk health, temperature, or SMART data, or when performing routine server maintenance.
---

# Disk Monitor

## Overview

This skill provides tools and guidelines for checking the health status of hard drives across the infrastructure using SMART data. It generates human-readable reports and helps identify disks that need replacement or monitoring.

## When to Use

- User asks about server disk health, temperature, or SMART data.
- Performing routine server maintenance checks.
- Investigating system performance issues that might be caused by failing disks.

## 不适用

- 需要修盘、分区、格式化或替换磁盘的具体运维操作
- 没有网络访问 Scrutiny API、也没有本地 SMART 数据来源的环境
- 只想看磁盘容量占用，而不是健康度、温度、寿命或历史趋势

## Checking Disk Health

To check the current health of all disks, execute the included script. Because your working directory may vary, you should use the absolute path to the script:

```bash
python3 ./scripts/disk-health-check.py
```
*(Run from within the skill directory, or use the absolute path `scripts/disk-health-check.py` relative to this skill)*

### Automation & AI Processing

To export structured tabular data containing pure integer measurements (ideal for AI parsing, parsing loops, or monitoring stacks like Zabbix/Prometheus), add the `--csv` flag:

```bash
python3 ./scripts/disk-health-check.py --csv
```

### Understanding the Output

The script outputs a formatted table containing:
- **主机 (Host)**: The machine hosting the drive.
- **型号 (Model)**: The specific model of the drive.
- **温度 (Temperature)**: Current operating temperature. High temperatures (>50°C) will trigger warnings.
- **运行时间 (Power On Hours)**: Total time the drive has been active.
- **寿命 (Wearout/Percentage Used)**: For SSDs, this indicates the remaining lifespan.
- **更新时间 (Update Time)**: The last time SMART data was collected. Ensure this is recent to guarantee accuracy.
- **风险 (Risk)**: 
  - 🔴 Critical: Immediate attention needed (High temp, end of life).
  - 🟡 Warning: Monitor closely (Elevated temp, long run time, low remaining life).
  - 🟢 Normal: Healthy.

## Advanced: Scrutiny APIs (Historical Data & Monitoring)

When the user asks for historical data, trend analysis, or raw monitoring data beyond the CLI script, you can directly query the underlying Scrutiny APIs. The default host is typically `https://smart.pve.icu`.

| Endpoint | Method | Purpose & Data Structure |
|----------|--------|--------------------------|
| `/api/device/{wwn}/details` | `GET` | **Historical Data:** Best for building temperature/wearout trend charts. Returns `data.device` (metadata) and `data.smart_results` (an array of historical SMART snapshots including `date`, `temp`, `power_on_hours`, and `attrs`). |
| `/api/summary` | `GET` | **Global Snapshot:** Returns a lightweight dictionary (`data.summary`) containing the *latest* status of all monitored disks. Used by the `disk-health-check` script. |
| `/api/health` | `GET` | **Service Health:** Returns status of internal components (influxdb, sqlite, frontend). Useful for testing if the monitoring system itself is down. |

**Example Automation Flow for Trending:**
1. Fetch `/api/summary` to get all WWN keys.
2. Loop through WWNs and fetch `/api/device/{wwn}/details`.
3. Extract `data.smart_results[].date` and `data.smart_results[].temp` (or any attribute from `attrs`) to build a time-series dataset.

## Reporting Guidelines

When reporting disk health to a user, follow these principles:
1. **Highlight the Critical**: Always lead with the 🔴 Red and 🟡 Yellow alerts. Don't bury them in a wall of text.
2. **Context is Key**: If a disk has a high temperature but is 100% healthy otherwise, suggest checking the cooling/fans.
3. **Verify Data Freshness**: Pay close attention to the `更新时间` (Update Time). If a failing disk's data hasn't updated in weeks, explicitly point out that the data is stale and the disk might already be dead.
4. **Actionable Advice**: Provide clear recommendations (e.g., "Schedule replacement", "Check ventilation").

## Checklist

执行前：
- [ ] 已确认目标是健康检查，而不是容量统计或磁盘修复
- [ ] 已确认数据源可访问（默认 Scrutiny API 或用户指定 URL）
- [ ] 已根据场景决定是否需要 `--csv` 结构化输出

执行后：
- [ ] 已优先突出 🔴 / 🟡 风险盘
- [ ] 已检查 `更新时间` 是否足够新
- [ ] 已给出可执行建议，而不是只贴原始表格

## 常见错误

| 错误做法 | 正确做法 |
|----------|----------|
| 把健康检查当成磁盘容量检查 | 仅用此技能处理 SMART / 温度 / 寿命 / 风险状态 |
| 忽略 `更新时间`，直接断言磁盘当前状态 | 先判断数据是否新鲜，再下结论 |
| 只看总通过/失败数量，不看具体风险盘 | 先列出异常盘，再补总体统计 |
| 需要历史趋势时仍只依赖 `/api/summary` | 改查 `/api/device/{wwn}/details` 获取历史快照 |
