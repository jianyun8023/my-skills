---
name: github-actions-multi-platform-build
description: Use when creating or updating GitHub Actions workflows for multi-platform Docker image builds (amd64/arm64) with Buildx, build-push-action, caching, and manifest list merging.
---

# GitHub Actions 多平台构建

## 适用场景
- 多平台镜像构建与发布（amd64/arm64）
- 需要 digest 合并 manifest list
- 需要 Buildx 缓存与标签管理

## 不适用
- 单平台构建且不合并 manifest
- 不推送到镜像仓库

## 核心检查清单

### Build job (matrix)
- [ ] Matrix 可用列表形式：
      platform: [linux/amd64, linux/arm64]（`fail-fast: false`）
- [ ] 环境变量: `REGISTRY_IMAGE` (小写), `VERSION`
- [ ] 生成 `REGISTRY_IMAGE` 时强制小写（如 `tr '[:upper:]' '[:lower:]'`）
- [ ] `actions/checkout@v4`
- [ ] `docker/setup-buildx-action@v3`
- [ ] `docker/login-action@v3` (ghcr.io)
- [ ] `docker/build-push-action@v6`:
  - [ ] `outputs: type=image,name=${{ env.REGISTRY_IMAGE }},push-by-digest=true,name-canonical=true,push=true`
  - [ ] `platforms: ${{ matrix.platform }}`
  - [ ] `cache-from: type=gha`, `cache-to: type=gha,mode=max`
- [ ] 获取 digest: `digest="${{ steps.build.outputs.digest }}"`
- [ ] 导出 digest: `touch "/tmp/digests/${digest#sha256:}"`
- [ ] artifact 名避免 `/`（如 `linux/amd64` → `linux-amd64`）
- [ ] `actions/upload-artifact@v4`: `name: digests-<safe-platform>`

### Merge job
- [ ] `needs: build`, `runs-on: ubuntu-latest`
- [ ] `actions/download-artifact@v4`: `pattern: digests-*`, `merge-multiple: true`
- [ ] `docker/setup-buildx-action@v3`
- [ ] (可选) `docker/metadata-action@v5`: 生成标签
- [ ] `docker/login-action@v3`
- [ ] 通过 metadata 输出或自定义标签传入 `imagetools create`
- [ ] `docker buildx imagetools create -t <tag> <image@sha256:digest>...`

## 值得学习的点
- ✅ digest + manifest 分离式流程（build 推 digest，merge 合并）
- ✅ `push-by-digest` + `name-canonical` 防止 tag 冲突
- ✅ `merge` job 统一打标签，避免重复推送
- ✅ `permissions` 最小化（`contents: read`，`packages: write`）
- ✅ 短期 artifact（`retention-days: 1`）

## 常见错误
- ❌ 单 runner 构建所有平台 → ✅ 使用平台匹配的 runner
- ❌ 忘记 `push-by-digest` → ✅ 必须使用以安全合并
- ❌ GHCR 镜像名未小写 → ✅ 强制小写
- ❌ 跳过 digest artifact → ✅ 必须传递到 merge job

## 基线要求
- ✅ 不声称文件已创建除非实际创建
- ✅ 不跳过验证即使模板存在
- ✅ 输出检查清单而非完整模板（除非明确要求）
- ✅ 尊重个人/项目技能位置

## 快速自检（必做）
- [ ] frontmatter 仅含 `name` 与 `description`
- [ ] `description` 以 “Use when” 开头并包含触发词
- [ ] 未声明任何未执行的操作或验证

## 借口-现实
| 借口 | 现实 |
| --- | --- |
| “模板够用，跳过验证” | 格式错误会导致技能不可发现 |
| “我已经更新了” | 未实际改写就不能声明 |

## 红旗
- “默认输出完整模板”
- “未执行也声明已验证”
