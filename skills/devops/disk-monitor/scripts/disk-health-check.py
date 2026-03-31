#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Disk Health Check Script - Pure Python Implementation

import json
import sys
import datetime
import urllib.request
import urllib.error
import argparse
import unicodedata
import csv

DEFAULT_API_URL = "https://smart.pve.icu/api/summary"

def display_width(text):
    """计算字符串的显示宽度，支持中英文混排"""
    return sum(2 if unicodedata.east_asian_width(c) in ('F', 'W') else 1 for c in str(text))

def align_str(text, target_width):
    """处理包含中文字符的左对齐，防止制表符错乱"""
    text = str(text)
    current_width = display_width(text)
    
    if current_width > target_width:
        # 如果超出目标宽度，进行截断并确保不超过宽度
        res = ""
        w = 0
        for char in text:
            cw = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
            if w + cw > target_width:
                break
            res += char
            w += cw
        return res + ' ' * (target_width - w)
        
    # 如果不足，补充空格
    return text + ' ' * (target_width - current_width)

def format_date(date_str):
    if not date_str:
        return '-'
    try:
        # 兼容例如 '2026-02-26T00:00:00Z' 的格式
        dt = datetime.datetime.strptime(date_str[:19], '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%m-%d %H:%M')
    except:
        return '-'

def main():
    parser = argparse.ArgumentParser(description="硬盘健康检查工具")
    parser.add_argument("-u", "--url", default=DEFAULT_API_URL, help="指定数据来源 API 的 URL (默认: %(default)s)")
    parser.add_argument("-w", "--warnings-only", action="store_true", help="筛选模式：仅显示有风险 (🟡/🔴) 的硬盘数据")
    parser.add_argument("--csv", action="store_true", help="输出结构化 CSV 格式，便于 AI 或程序解析")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="网络请求超时时间，单位秒 (默认: 10)")
    args = parser.parse_args()

    try:
        req = urllib.request.Request(args.url, headers={'User-Agent': 'DiskMonitor-CLI/1.0'})
        with urllib.request.urlopen(req, timeout=args.timeout) as response:
            if response.status != 200:
                print(f"ERROR: 数据获取失败，HTTP 状态码: {response.status}", file=sys.stderr)
                sys.exit(1)
            raw_data = response.read().decode('utf-8')
            data = json.loads(raw_data)
    except urllib.error.URLError as e:
        print(f"ERROR: 网络不通或超时 - {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print("ERROR: API 返回了非法 JSON 格式", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: 未知错误 - {e}", file=sys.stderr)
        sys.exit(1)

    devices = data.get('data', {}).get('summary', {})
    if not devices:
        if args.csv:
            sys.exit(0) # CSV 模式下无数据直接安静退出
        else:
            print("WARN: API 返回数据中找不到设备或当前没有设备数据。")
            sys.exit(0)

    # 统计信息
    total = len(devices)
    passed = sum(1 for d in devices.values() if d.get('device', {}).get('device_status', 0) == 0)
    failed = total - passed

    risk_order = {'🔴': 0, '🟡': 1, '🟢': 2}
    sorted_devices = []

    for wwn, info in devices.items():
        dev = info.get('device', {})
        smart = info.get('smart', {})

        host = dev.get('host_id') or dev.get('device_name', 'unknown')
        host = host.split('.')[0] if '.' in host else host # 精简长域名
        model = dev.get('model_name', 'unknown')
        
        temp = smart.get('temp', 0)
        hours = smart.get('power_on_hours', 0)
        pct_used = smart.get('percentage_used')
        wearout_val = smart.get('wearout_value') 
        raw_date = smart.get('collector_date', '')
        update_time = format_date(raw_date)

        # 初始化基本风险状态，避免互相覆盖降级风险
        risk_level = 0 # 0: 🟢, 1: 🟡, 2: 🔴
        if temp > 60 or hours > 50000:
            risk_level = max(risk_level, 2)
        elif temp > 50 or hours > 25000:
            risk_level = max(risk_level, 1)
            
        # 叠加 SSD 寿命状态
        if pct_used is not None and pct_used > 80:
             risk_level = max(risk_level, 2 if pct_used >= 95 else 1)
        elif wearout_val is not None and wearout_val < 20: 
             risk_level = max(risk_level, 2 if wearout_val <= 5 else 1)
             
        risk = {0: '🟢', 1: '🟡', 2: '🔴'}[risk_level]

        # 参数过滤：如果开启了且是正常状态，跳过
        if args.warnings_only and risk == '🟢':
            continue

        # 格式化运行时间
        if hours > 8760:
            hours_str = f'{hours/8760:.1f}年'
        elif hours > 24:
            hours_str = f'{hours/24:.0f}天'
        else:
            hours_str = f'{hours}h'

        # 格式化寿命
        if pct_used is not None:
            raw_wearout = 100 - pct_used if pct_used <= 100 else 0
            wearout_str = f'{100-pct_used}%' if pct_used <= 100 else '-'
        elif wearout_val is not None:
            raw_wearout = wearout_val if wearout_val <= 100 else 0
            wearout_str = f'{wearout_val}%' if wearout_val <= 100 else '-'
        else:
            raw_wearout = ''
            wearout_str = '-'

        temp_str = f'🔥{temp}°C' if temp > 50 else f'{temp}°C'
        
        sorted_devices.append({
            'risk': risk,
            'host': host,
            'model': model,
            'temp': temp,
            'temp_str': temp_str,
            'hours': hours,
            'hours_str': hours_str,
            'wearout': raw_wearout,
            'wearout_str': wearout_str,
            'update_time': update_time,
            'raw_date': raw_date
        })

    # 按风险程度和主机名排序
    sorted_devices.sort(key=lambda x: (risk_order.get(x['risk'], 3), x['host']))

    # 判断输出模式
    if args.csv:
        csv_writer = csv.writer(sys.stdout)
        # 写表头
        csv_writer.writerow(['Host', 'Model', 'Temperature(C)', 'PowerOnHours', 'RemainingLife%', 'UpdateTime', 'Risk'])
        for dev in sorted_devices:
            # risk 在 csv 稍微保留为原文本字典，或者转成 Critical / Warning / OK.
            risk_label = "Critical" if dev['risk'] == '🔴' else ("Warning" if dev['risk'] == '🟡' else "OK")
            csv_writer.writerow([
                dev['host'], 
                dev['model'], 
                dev['temp'], 
                dev['hours'], 
                dev['wearout'], 
                dev['raw_date'], 
                risk_label
            ])
        sys.exit(0)

    # 默认美化表格输出
    print("╔" + "═" * 88 + "╗")
    print("║" + align_str("                                    🖴 硬盘健康检查报告", 88) + "║")
    print("╚" + "═" * 88 + "╝")
    print(f"📅 检查时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("")

    print("┌" + "─" * 88 + "┐")
    print("│" + align_str(" 📊 总体状态", 88) + "│")
    print("├" + "─" * 88 + "┤")
    summary_text = f"   ✅ 通过: {passed:<4} |  ❌ 失败: {failed:<4} |  📦 总计: {total:<4}"
    print("│" + align_str(summary_text, 88) + "│")
    print("└" + "─" * 88 + "┘")
    print("")

    print('┌──────────────┬──────────────────────┬────────┬──────────┬────────┬──────────────┬──────┐')
    print('│ 主机         │ 型号                 │ 温度   │ 运行时间 │ 寿命   │ 更新时间     │ 风险 │')
    print('├──────────────┼──────────────────────┼────────┼──────────┼────────┼──────────────┼──────┤')

    if not sorted_devices:
        print('│' + align_str(' 暂无需要关注的风险硬盘数据...', 88) + '│')
    else:
        for dev in sorted_devices:
            # 填入占位
            print(f"│ {align_str(dev['host'], 12)} │ {align_str(dev['model'], 20)} │ {align_str(dev['temp_str'], 6)} │ {align_str(dev['hours_str'], 8)} │ {align_str(dev['wearout_str'], 6)} │ {align_str(dev['update_time'], 12)} │ {dev['risk']}   │")

    print('└──────────────┴──────────────────────┴────────┴──────────┴────────┴──────────────┴──────┘')
    print("")
    print('💡 风险说明: 🔴 需关注 | 🟡 建议监控 | 🟢 正常')
    print('   配置参数: 可通过 -h 或者 --help 查看支持的过滤和 API 替换参数')
    print('   阈值说明: 温度 >50°C = 🔥 | 运行 >25000小时 = 长期运行 | 剩余寿命 = SSD 剩余寿命百分比')
    print("═" * 90)

if __name__ == "__main__":
    main()
