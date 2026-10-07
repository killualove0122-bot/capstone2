import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

os.makedirs('panel_assets', exist_ok=True)

# 1. STAC API & Satellite Data Diagram
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
ax.set_facecolor('#0f172a')
fig.patch.set_facecolor('#0f172a')
ax.axis('off')

# Title
ax.text(0.5, 0.92, "STAC API 멀티위성 자동 파이프라인", color='#38bdf8', fontsize=14, fontweight='bold', ha='center')

# Boxes
boxes = [
    ("선택 좌표/날짜\n(User Query)", 0.15, 0.6, '#1e293b', '#0284c7'),
    ("STAC API\n(Planetary Computer)", 0.5, 0.6, '#1e293b', '#3b82f6'),
    ("Sentinel-2 / Landsat\nB08, B12 / NIR, SWIR", 0.85, 0.6, '#1e293b', '#10b981'),
    ("정상일 (Pre-fire)\n위성 영상", 0.3, 0.22, '#1e293b', '#f59e0b'),
    ("비교일 (Post-fire)\n위성 영상", 0.7, 0.22, '#1e293b', '#ef4444')
]

for text, x, y, bg, border in boxes:
    rect = patches.FancyBboxPatch((x-0.13, y-0.1), 0.26, 0.2, boxstyle="round,pad=0.03", fc=bg, ec=border, lw=2)
    ax.add_patch(rect)
    ax.text(x, y, text, color='white', fontsize=9, fontweight='bold', ha='center', va='center')

# Arrows
arrow_style = dict(arrowstyle="->", color='#94a3b8', lw=2)
ax.annotate('', xy=(0.35, 0.6), xytext=(0.28, 0.6), arrowprops=arrow_style)
ax.annotate('', xy=(0.7, 0.6), xytext=(0.63, 0.6), arrowprops=arrow_style)
ax.annotate('', xy=(0.3, 0.33), xytext=(0.5, 0.48), arrowprops=arrow_style)
ax.annotate('', xy=(0.7, 0.33), xytext=(0.5, 0.48), arrowprops=arrow_style)

plt.tight_layout()
plt.savefig('panel_assets/quad1_stac_sat.png', bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()

# 2. dNBR Formula & 6-Level Classification Diagram
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
ax.set_facecolor('#0f172a')
fig.patch.set_facecolor('#0f172a')
ax.axis('off')

ax.text(0.5, 0.92, "dNBR 연산 및 6단계 심각도 분류", color='#38bdf8', fontsize=14, fontweight='bold', ha='center')

# Formulas
ax.text(0.5, 0.78, r"$NBR = \frac{NIR - SWIR}{NIR + SWIR}$", color='#e2e8f0', fontsize=14, ha='center')
ax.text(0.5, 0.64, r"$dNBR = (NBR_{pre} - NBR_{post}) \times 1000$", color='#f43f5e', fontsize=14, fontweight='bold', ha='center')

# Severity Color Legend Bar
severities = [
    ("고식생 회복", "< -500", "#006600"),
    ("정상 / 미피해", "-500 ~ 99", "#33cc33"),
    ("경도 피해", "100 ~ 269", "#ffff00"),
    ("중경도 피해", "270 ~ 439", "#ff9900"),
    ("중중도 피해", "440 ~ 650", "#ff3300"),
    ("중증 피해", "> 650", "#7a0099")
]

y_start = 0.48
for idx, (name, rng, color) in enumerate(severities):
    y = y_start - idx * 0.08
    rect = patches.Rectangle((0.15, y-0.03), 0.08, 0.05, fc=color, ec='white', lw=0.5)
    ax.add_patch(rect)
    ax.text(0.26, y, name, color='white', fontsize=9, fontweight='bold', va='center')
    ax.text(0.65, y, rng, color='#cbd5e1', fontsize=9, fontfamily='monospace', va='center')

plt.tight_layout()
plt.savefig('panel_assets/quad2_dnbr_formula.png', bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()

# 3. Map Alignment Diagram
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
ax.set_facecolor('#0f172a')
fig.patch.set_facecolor('#0f172a')
ax.axis('off')

ax.text(0.5, 0.92, "Titiler EPSG:4326 WGS84 1:1 지도 정렬", color='#38bdf8', fontsize=14, fontweight='bold', ha='center')

# Simulated alignment comparison
rect1 = patches.FancyBboxPatch((0.08, 0.15), 0.38, 0.65, boxstyle="round,pad=0.02", fc='#1e293b', ec='#ef4444', lw=2)
ax.add_patch(rect1)
ax.text(0.27, 0.72, "[기존] 궤도 좌표계 (UTM)\n위치 어긋남 발생 (Shift)", color='#fca5a5', fontsize=9, fontweight='bold', ha='center')

rect2 = patches.FancyBboxPatch((0.54, 0.15), 0.38, 0.65, boxstyle="round,pad=0.02", fc='#1e293b', ec='#10b981', lw=2)
ax.add_patch(rect2)
ax.text(0.73, 0.72, "[개선] EPSG:4326 BBOX\n1:1 완벽 지도 정렬 (Match)", color='#6ee7b7', fontsize=9, fontweight='bold', ha='center')

# Draw simulated shifted vs aligned grid
# Left (Shifted)
ax.plot([0.15, 0.38], [0.35, 0.42], color='#f43f5e', lw=3, ls='--')
ax.plot([0.18, 0.35], [0.25, 0.55], color='#f43f5e', lw=3, ls='--')

# Right (Aligned)
ax.plot([0.60, 0.86], [0.38, 0.38], color='#10b981', lw=3)
ax.plot([0.62, 0.84], [0.28, 0.58], color='#10b981', lw=3)

plt.tight_layout()
plt.savefig('panel_assets/quad3_map_alignment.png', bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()

# 4. App UI & Analytics Chart Diagram
fig, ax = plt.subplots(figsize=(6, 4.5), dpi=200)
ax.set_facecolor('#0f172a')
fig.patch.set_facecolor('#0f172a')
ax.axis('off')

ax.text(0.5, 0.92, "이중 분할 지도 & 자동 통계 보고서 UI", color='#38bdf8', fontsize=14, fontweight='bold', ha='center')

# Mockup UI Boxes
rect_left = patches.Rectangle((0.08, 0.2), 0.38, 0.6, fc='#1e293d', ec='#3b82f6', lw=1.5)
ax.add_patch(rect_left)
ax.text(0.27, 0.72, "정상일 (Pre-fire)", color='#93c5fd', fontsize=9, fontweight='bold', ha='center')

rect_right = patches.Rectangle((0.54, 0.2), 0.38, 0.6, fc='#1e293d', ec='#ef4444', lw=1.5)
ax.add_patch(rect_right)
ax.text(0.73, 0.72, "산불일 (Post-fire dNBR)", color='#fca5a5', fontsize=9, fontweight='bold', ha='center')

# Add a mini pie chart in bottom right
pie_ax = fig.add_axes([0.62, 0.25, 0.22, 0.22])
pie_ax.pie([15, 45, 20, 10, 7, 3], colors=['#006600', '#33cc33', '#ffff00', '#ff9900', '#ff3300', '#7a0099'])

plt.tight_layout()
plt.savefig('panel_assets/quad4_app_ui.png', bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()

print("Generated 4 panel asset diagrams in panel_assets/")
