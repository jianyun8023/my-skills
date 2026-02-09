#!/bin/bash
# catalog.sh - 自动生成 Skill 索引目录
#
# 用法:
#   ./scripts/catalog.sh          # 生成索引到 docs/CATALOG.md
#   ./scripts/catalog.sh --stdout # 输出到终端

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$REPO_ROOT/skills"
OUTPUT_FILE="$REPO_ROOT/docs/CATALOG.md"

TO_STDOUT=false
if [[ "${1:-}" == "--stdout" ]]; then
    TO_STDOUT=true
fi

# ============================================================
# 分类名称映射
# ============================================================

category_name() {
    case "$1" in
        java)        echo "Java 技术栈" ;;
        devops)      echo "DevOps & CI/CD" ;;
        tooling)     echo "工具配置" ;;
        development) echo "开发方法论" ;;
        quality)     echo "质量保证" ;;
        workflow)    echo "工作流 & 协作" ;;
        prompting)   echo "AI 提示技巧" ;;
        *)           echo "$1" ;;
    esac
}

# ============================================================
# 解析 SKILL.md frontmatter
# ============================================================

parse_field() {
    local file="$1"
    local field="$2"

    # 提取 frontmatter (between --- and ---)
    local value
    value=$(awk '/^---$/{n++; next} n==1 && /^'"$field"':/{
        # 处理多行 description (以 > 或 | 开头)
        sub(/^'"$field"':[[:space:]]*>?[[:space:]]*/, "")
        if ($0 == "" || $0 == ">") {
            # 多行值，读取后续缩进行
            while ((getline line) > 0) {
                if (line ~ /^[[:space:]]/) {
                    sub(/^[[:space:]]+/, "", line)
                    printf "%s ", line
                } else break
            }
        } else {
            print
        }
        exit
    }' "$file")

    echo "$value"
}

# ============================================================
# 生成目录
# ============================================================

generate_catalog() {
    echo "# Skill 目录索引"
    echo ""
    echo "> 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')，请勿手动编辑。"
    echo "> 运行 \`./scripts/catalog.sh\` 重新生成。"
    echo ""

    local total=0

    # 遍历分类
    for category_dir in "$SKILLS_DIR"/*/; do
        [ -d "$category_dir" ] || continue
        local category
        category="$(basename "$category_dir")"
        local cat_display
        cat_display="$(category_name "$category")"

        local skills_in_cat=0
        local cat_content=""

        # 遍历 Skill
        for skill_dir in "$category_dir"/*/; do
            [ -d "$skill_dir" ] || continue
            local skill_file="$skill_dir/SKILL.md"
            [ -f "$skill_file" ] || continue

            local skill_name
            skill_name="$(basename "$skill_dir")"
            local name
            name="$(parse_field "$skill_file" "name")"
            local desc
            desc="$(parse_field "$skill_file" "description")"

            # 截断描述
            if [ ${#desc} -gt 120 ]; then
                desc="${desc:0:117}..."
            fi

            # 检查附加文件
            local extras=""
            [ -f "$skill_dir/reference.md" ] && extras="$extras reference"
            [ -d "$skill_dir/templates" ] && extras="$extras templates"
            if [ -n "$extras" ]; then
                extras=" (附:$extras)"
            fi

            local rel_path="skills/$category/$skill_name"
            cat_content+="| [\`$skill_name\`]($rel_path/) | $desc$extras |"$'\n'
            skills_in_cat=$((skills_in_cat + 1))
            total=$((total + 1))
        done

        if [ $skills_in_cat -gt 0 ]; then
            echo "## $cat_display ($skills_in_cat)"
            echo ""
            echo "| Skill | 描述 |"
            echo "|-------|------|"
            echo -n "$cat_content"
            echo ""
        fi
    done

    echo "---"
    echo ""
    echo "**共计 $total 个 Skill**"
}

# ============================================================
# 主逻辑
# ============================================================

if [ "$TO_STDOUT" = true ]; then
    generate_catalog
else
    generate_catalog > "$OUTPUT_FILE"
    echo "已生成索引: $OUTPUT_FILE (共 $(grep -c '^\|.*\|$' "$OUTPUT_FILE" || true) 行)"
fi
