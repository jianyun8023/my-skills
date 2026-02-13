#!/bin/bash
# install.sh - 将仓库中的 Skill 安装到各 AI 工具目录
#
# 用法:
#   ./scripts/install.sh           # 安装所有 Skill
#   ./scripts/install.sh --dry-run # 预览，不实际执行
#   ./scripts/install.sh --clean   # 清理已安装的 Skill
#
# 安装方式:
#   - Cursor:              ~/.cursor/skills/              (复制 — 不支持符号链接)
#   - Claude Code:         ~/.claude/skills/              (复制 — 符号链接不稳定)
#   - Gemini CLI:          ~/.gemini/skills/              (符号链接)
#   - Gemini Antigravity:  ~/.gemini/antigravity/skills/  (复制 — 不支持符号链接)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SKILLS_DIR="$REPO_ROOT/skills"

# 目标目录
CURSOR_SKILLS_DIR="$HOME/.cursor/skills"
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
GEMINI_SKILLS_DIR="$HOME/.gemini/skills"
GEMINI_AG_SKILLS_DIR="$HOME/.gemini/antigravity/skills"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DRY_RUN=false
CLEAN=false

# ============================================================
# 参数解析
# ============================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [--dry-run] [--clean]"
            echo ""
            echo "选项:"
            echo "  --dry-run  预览安装操作，不实际执行"
            echo "  --clean    清理所有由本脚本安装的 Skill"
            exit 0
            ;;
        *)
            echo -e "${RED}未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

# ============================================================
# 工具函数
# ============================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_dry() {
    echo -e "${BLUE}[DRY-RUN]${NC} $1"
}

# 创建符号链接
# $1: 源路径 (仓库中的 skill 目录)
# $2: 目标路径 (工具的 skill 目录)
link_skill() {
    local src="$1"
    local dest="$2"
    local skill_name
    skill_name="$(basename "$src")"

    local target="$dest/$skill_name"

    if [ -L "$target" ]; then
        # 已存在符号链接，检查是否指向正确
        local current_target
        current_target="$(readlink "$target")"
        if [ "$current_target" = "$src" ]; then
            return 0  # 已正确链接
        else
            log_warn "${skill_name} -> 已存在链接指向 ${current_target}，将替换"
            if [ "$DRY_RUN" = false ]; then
                rm "$target"
            fi
        fi
    elif [ -d "$target" ]; then
        log_warn "${skill_name} -> 目标已存在为普通目录: ${target}，跳过"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        log_dry "ln -s $src -> $target"
    else
        mkdir -p "$dest"
        ln -s "$src" "$target"
        log_info "已链接: $skill_name -> $target"
    fi
}

# 复制 Skill 目录（用于不支持符号链接的目标）
# $1: 源路径 (仓库中的 skill 目录)
# $2: 目标路径 (工具的 skill 目录)
copy_skill() {
    local src="$1"
    local dest="$2"
    local skill_name
    skill_name="$(basename "$src")"

    local target="$dest/$skill_name"

    if [ "$DRY_RUN" = true ]; then
        log_dry "cp -r $src -> $target"
        return 0
    fi

    mkdir -p "$dest"

    # 如果存在历史遗留的符号链接，先移除
    if [ -L "$target" ]; then
        rm "$target"
    fi

    # 使用 rsync 保持幂等：已存在则增量更新，不存在则全量复制
    if command -v rsync &>/dev/null; then
        rsync -a --delete "$src/" "$target/"
    else
        rm -rf "$target"
        cp -r "$src" "$target"
    fi
    log_info "已复制: $skill_name -> $target"
}

# 清理由仓库创建的符号链接
# $1: 工具的 skill 目录
# $2: 工具名称
clean_links() {
    local dest="$1"
    local tool_name="$2"

    if [ ! -d "$dest" ]; then
        return 0
    fi

    local count=0
    for link in "$dest"/*/; do
        [ -d "$link" ] || continue
        link="${link%/}"

        if [ -L "$link" ]; then
            local target
            target="$(readlink "$link")"
            # 检查是否指向本仓库
            if [[ "$target" == "$SKILLS_DIR"/* ]]; then
                if [ "$DRY_RUN" = true ]; then
                    log_dry "rm $link (-> $target)"
                else
                    rm "$link"
                    log_info "已移除: $(basename "$link") from $tool_name"
                fi
                count=$((count + 1))
            fi
        fi
    done

    if [ $count -eq 0 ]; then
        log_info "$tool_name: 无需清理"
    fi
}

# 清理由仓库复制的目录（用于不支持符号链接的目标）
# $1: 工具的 skill 目录
# $2: 工具名称
clean_copies() {
    local dest="$1"
    local tool_name="$2"

    if [ ! -d "$dest" ]; then
        return 0
    fi

    local count=0
    for copied_dir in "$dest"/*/; do
        [ -d "$copied_dir" ] || continue
        copied_dir="${copied_dir%/}"
        local skill_name
        skill_name="$(basename "$copied_dir")"

        # 跳过符号链接（由 clean_links 处理）
        [ -L "$copied_dir" ] && continue

        # 检查仓库中是否存在同名 Skill（遍历所有分类）
        local found=false
        for category_dir in "$SKILLS_DIR"/*/; do
            if [ -d "$category_dir/$skill_name" ] && [ -f "$category_dir/$skill_name/SKILL.md" ]; then
                found=true
                break
            fi
        done

        if [ "$found" = true ]; then
            if [ "$DRY_RUN" = true ]; then
                log_dry "rm -rf $copied_dir"
            else
                rm -rf "$copied_dir"
                log_info "已移除: $skill_name from $tool_name"
            fi
            count=$((count + 1))
        fi
    done

    if [ $count -eq 0 ]; then
        log_info "$tool_name: 无需清理"
    fi
}

# ============================================================
# 安装映射配置
# ============================================================
# 格式: install_to <工具目录> <分类目录...>
#
# 默认策略: 所有 Skill 同时安装到 Cursor 和 Claude Code
# 如果某些 Skill 只适用于特定工具，可调整此处映射

install_skills() {
    local total=0

    # 遍历所有分类目录
    for category_dir in "$SKILLS_DIR"/*/; do
        [ -d "$category_dir" ] || continue

        # 遍历分类下的所有 Skill
        for skill_dir in "$category_dir"/*/; do
            [ -d "$skill_dir" ] || continue
            [ -f "$skill_dir/SKILL.md" ] || continue

            skill_dir="${skill_dir%/}"

            # 安装到 Cursor（复制 — 不支持符号链接）
            copy_skill "$skill_dir" "$CURSOR_SKILLS_DIR"

            # 安装到 Claude Code（复制 — 符号链接不稳定）
            copy_skill "$skill_dir" "$CLAUDE_SKILLS_DIR"

            # 安装到 Gemini CLI（符号链接）
            link_skill "$skill_dir" "$GEMINI_SKILLS_DIR"

            # 安装到 Gemini Antigravity（复制 — 不支持符号链接）
            copy_skill "$skill_dir" "$GEMINI_AG_SKILLS_DIR"

            total=$((total + 1))
        done
    done

    if [ "$DRY_RUN" = true ]; then
        echo ""
        log_dry "共 $total 个 Skill 将被安装到 Cursor、Claude Code、Gemini CLI 和 Gemini Antigravity"
    else
        echo ""
        log_info "共安装 $total 个 Skill"
        log_info "Cursor:              $CURSOR_SKILLS_DIR"
        log_info "Claude Code:         $CLAUDE_SKILLS_DIR"
        log_info "Gemini CLI:          $GEMINI_SKILLS_DIR"
        log_info "Gemini Antigravity:  $GEMINI_AG_SKILLS_DIR"
    fi
}

# ============================================================
# 主逻辑
# ============================================================

echo "=============================="
echo "  my-skills 安装脚本"
echo "=============================="
echo ""

if [ "$CLEAN" = true ]; then
    log_info "清理模式"
    # Cursor / Claude Code：清理复制的目录 + 历史遗留的符号链接
    clean_copies "$CURSOR_SKILLS_DIR" "Cursor"
    clean_links "$CURSOR_SKILLS_DIR" "Cursor"
    clean_copies "$CLAUDE_SKILLS_DIR" "Claude Code"
    clean_links "$CLAUDE_SKILLS_DIR" "Claude Code"
    # Gemini CLI：清理符号链接
    clean_links "$GEMINI_SKILLS_DIR" "Gemini CLI"
    # Gemini Antigravity：清理复制的目录
    clean_copies "$GEMINI_AG_SKILLS_DIR" "Gemini Antigravity"
    echo ""
    log_info "清理完成"
else
    if [ "$DRY_RUN" = true ]; then
        log_info "预览模式 (不会实际执行)"
        echo ""
    fi
    install_skills
fi
