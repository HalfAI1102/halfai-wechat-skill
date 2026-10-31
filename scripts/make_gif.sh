#!/usr/bin/env bash
# 把一段录屏/视频切成适合公众号排版的 GIF：520px 宽、10fps、去噪、无抖动调色板，可选 gifsicle 有损压缩。
# 用法: scripts/make_gif.sh input.mp4 output.gif [开始秒=0] [时长秒=4] [宽=520] [fps=10]
# 目标：单张 300KB–1MB，整篇图片合计 ≈10MB 以内（预览页要压在 16MB 以下）。
set -euo pipefail
in=${1:?input video}; out=${2:?output gif}
ss=${3:-0}; t=${4:-4}; w=${5:-520}; fps=${6:-10}
command -v ffmpeg >/dev/null || { echo "需要 ffmpeg" >&2; exit 1; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
vf="fps=${fps},scale=${w}:-1:flags=lanczos,hqdn3d=3:3:6:6"
ffmpeg -v error -y -ss "$ss" -t "$t" -i "$in" -vf "${vf},palettegen=stats_mode=diff:max_colors=128" "$tmp/pal.png"
ffmpeg -v error -y -ss "$ss" -t "$t" -i "$in" -i "$tmp/pal.png" \
  -lavfi "${vf}[x];[x][1:v]paletteuse=dither=none:diff_mode=rectangle" "$tmp/raw.gif"
if command -v gifsicle >/dev/null; then
  gifsicle -O3 --lossy=100 "$tmp/raw.gif" -o "$out"
else
  cp "$tmp/raw.gif" "$out"
  echo "提示：没装 gifsicle（apt install gifsicle / brew install gifsicle），跳过有损压缩，文件会大 30–60%" >&2
fi
kb=$(( $(wc -c <"$out") / 1024 ))
echo "$out  ${kb}KB"
[ "$kb" -gt 1024 ] && echo "超过 1MB：缩短时长、降到 8fps 或把宽度降到 480 再试" >&2 || true
