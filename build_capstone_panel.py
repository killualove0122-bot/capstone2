import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

def update_text_frame(shape, text, font_size=14, bold=False, color=RGBColor(30, 41, 59)):
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = text
    p.font.name = 'Malgun Gothic'
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color

def set_multiline_bullet_text(shape, lines_with_bold):
    if not shape.has_text_frame:
        return
    tf = shape.text_frame
    tf.clear()
    for idx, (title, body) in enumerate(lines_with_bold):
        p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
        p.space_after = Pt(8)
        run_title = p.add_run()
        run_title.text = title + ": " if title else ""
        run_title.font.name = 'Malgun Gothic'
        run_title.font.size = Pt(13)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(15, 23, 42)

        run_body = p.add_run()
        run_body.text = body
        run_body.font.name = 'Malgun Gothic'
        run_body.font.size = Pt(12)
        run_body.font.bold = False
        run_body.font.color.rgb = RGBColor(51, 65, 85)

sample_path = r'd:\캡스톤판넬 1차_샘플.pptx'
prs = pptx.Presentation(sample_path)
slide = prs.slides[0]

shape_dict = {shape.name: shape for shape in slide.shapes}

# 1. Title Header
if "TextBox 1" in shape_dict:
    update_text_frame(shape_dict["TextBox 1"], "위성 데이터 기반 산불 피해(dNBR) 실시간 비교 분석 및 탐색 시스템", font_size=28, bold=True, color=RGBColor(17, 24, 39))

if "TextBox 3" in shape_dict:
    update_text_frame(shape_dict["TextBox 3"], "2026 공간정보캡스톤디자인 졸업작품전", font_size=16, bold=True, color=RGBColor(71, 85, 105))

# 2. Section 01: 배경 및 문제 정의
if "TextBox 9" in shape_dict:
    lines = [
        ("▪ 국내 대형 산불 사례 및 위험성 증가", "2022년 울진·삼척 산불(16,302 ha), 2022년 강릉·동해 옥계 산불(4,000 ha), 2019년 고성 산불(1,260 ha) 등 동해안 및 전국 단위 대형 산불 발생 주기가 단축되고 있으며, 산림 파괴와 인명·재산 피해 규모가 사상 최대를 기록함."),
        ("▪ 기존 현장 피해 조사의 한계 및 비용 소요", "산림청 및 지자체의 기존 산불 피해 조사는 현장 인력 투입 및 항공 촬영 후 물리적 현장 정밀 조사 방식으로 진행되어, 전체 피해 구역을 파악하는 데 수주일~수개월의 긴 시간과 막대한 행정력·예산이 소요됨."),
        ("▪ 실시간 위성 기반 dNBR 자동 분석의 필요성", "신속한 긴급 재해 복구 계획 수립을 위해 근적외선(NIR)과 단파적외선(SWIR) 광학 위성 밴드를 활용해 dNBR(차분 정규 탄화 지수)을 1초 만에 자동 연산하고 누구나 웹에서 손쉽게 시각적으로 확인할 수 있는 공공 공간정보 시스템 구축이 시급함.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 9"], lines)

# 3. Section 02: 해결방안 및 과정 Summary Bullets
# Find group 43 subshapes
for s in slide.shapes:
    if s.name == "그룹 43" and hasattr(s, 'shapes'):
        for sub in s.shapes:
            if sub.name == "TextBox 46":
                update_text_frame(sub, "▪ Microsoft Planetary Computer STAC API를 활용해 Sentinel-2 / Landsat-8,9 위성 영상 자동 검색 및 수신", font_size=13, bold=True, color=RGBColor(30, 41, 59))
            elif sub.name == "TextBox 47":
                update_text_frame(sub, "▪ dNBR(차분 정규 탄화 지수) 알고리즘 및 Titiler EPSG:4326 WGS84 재투영 기술로 완벽한 지도 정렬 구현", font_size=13, bold=True, color=RGBColor(30, 41, 59))

# Section 02: 4 Quadrants Text Boxes
if "TextBox 54" in shape_dict:
    lines = [
        ("(1) STAC API 위성 영상 탐색", "사용자 선택 지역(위도·경도) 및 산불 일자 기준 전/후 35일 내 구름 40% 미만 최적 Sentinel-2 (B08, B12) & Landsat (NIR08, SWIR22) 광학 위성 영상 자동 검색 및 수신.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 54"], lines)

if "TextBox 45" in shape_dict:
    lines = [
        ("(2) dNBR 연산 & 6단계 분류", "정상일/산불일 NBR 지수 NBR=(NIR-SWIR)/(NIR+SWIR) 연산 후 dNBR=(NBR_pre - NBR_post)*1000 공식으로 USGS 표준 6단계 피해 면적(ha, km²) 자동 산출.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 45"], lines)

if "TextBox 11" in shape_dict:
    lines = [
        ("(3) Titiler EPSG:4326 지도 정렬", "위성 궤도 좌표계(UTM)로 인한 지도 어긋남 방지를 위해 Titiler API 기반 WGS84(EPSG:4326) 실시간 재투영 및 BBOX Crop을 적용하여 배경 위성 지도와 1:1 완벽 정렬.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 11"], lines)

if "TextBox 68" in shape_dict:
    lines = [
        ("(4) 이중 지도 비교 & 리포트 내보내기", "Leaflet.js 기반 단일/분할 동기화 지도 UI로 정상일 vs 산불일 피해 영역을 직관적 비교하고, Chart.js 통계 차트 및 CSV 내보내기, 인쇄 리포트 자동 생성 기능 구현.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 68"], lines)

# 4. Section 03: 결과 및 기대효과
if "TextBox 70" in shape_dict:
    lines = [
        ("▪ 산불 피해 조사 속도 및 행정 효율성 혁신", "수주일 이상 소요되던 산불 피해 구역 정량 조사 과정을 단 1초 만에 자동화하여, 산림청·소방청·지자체의 초기 긴급 재해 복구 예산 산정 및 피해 구역 스크리닝 시간을 99% 이상 단축."),
        ("▪ 위성 공간정보 접근성 대중화 및 공공 활용 극대화", "고가의 전문 GIS 프로그램(ArcGIS, QGIS 등) 설치 없이 일반 시민, 연구자, 정책 담당자 누구나 웹 브라우저에서 클릭 몇 번만으로 정밀 위성 dNBR 분석을 수행할 수 있는 무설치 웹 표준 환경 제공."),
        ("▪ 산림 재난 복구 및 기후변화 대응 정책 수립 지원", "6단계 심각도별 정확한 면적(ha, km²) 데이터와 CSV 내보내기 기능을 통해 조림 식재 우선순위 구획, 토사 유출 및 2차 산사태 위험 지역 파악 등 과학적이고 정량적인 산림 생태계 복구 전략 수립에 기여.")
    ]
    set_multiline_bullet_text(shape_dict["TextBox 70"], lines)

# 5. Insert Diagram Images into 4 Quadrants of Section 02
quad_images = [
    ('panel_assets/quad1_stac_sat.png', Inches(6.5), Inches(15.6), Inches(11.0), Inches(4.2)),
    ('panel_assets/quad2_dnbr_formula.png', Inches(22.8), Inches(15.6), Inches(5.0), Inches(4.2)),
    ('panel_assets/quad3_map_alignment.png', Inches(6.5), Inches(20.8), Inches(11.0), Inches(4.5)),
    ('panel_assets/quad4_app_ui.png', Inches(22.8), Inches(20.8), Inches(5.0), Inches(4.5))
]

# Adjust positions relative to slide 02 boundaries
# Quad 1: Left column under text 54 (x=1.1, y=17.2, w=5.2, h=3.6)
# Quad 2: Right column under text 45 (x=17.8, y=17.2, w=4.8, h=3.6)
# Quad 3: Left column under text 11 (x=1.1, y=22.8, w=5.2, h=3.6)
# Quad 4: Right column under text 68 (x=17.8, y=22.8, w=4.8, h=3.6)

quad_placements = [
    ('panel_assets/quad1_stac_sat.png', Inches(6.8), Inches(15.5), Inches(10.5), Inches(4.5)),
    ('panel_assets/quad2_dnbr_formula.png', Inches(6.8), Inches(20.5), Inches(10.5), Inches(4.5)),
    ('panel_assets/quad3_map_alignment.png', Inches(12.5), Inches(15.5), Inches(10.5), Inches(4.5)),
    ('panel_assets/quad4_app_ui.png', Inches(12.5), Inches(20.5), Inches(10.5), Inches(4.5))
]

# Add images cleanly into section 02 quadrants
for img_path, left, top, width, height in [
    ('panel_assets/quad1_stac_sat.png', Inches(6.5), Inches(15.6), Inches(11.0), Inches(4.2)),
    ('panel_assets/quad2_dnbr_formula.png', Inches(6.5), Inches(21.2), Inches(11.0), Inches(4.2)),
    ('panel_assets/quad3_map_alignment.png', Inches(17.8), Inches(17.5), Inches(4.8), Inches(3.2)),
    ('panel_assets/quad4_app_ui.png', Inches(17.8), Inches(22.8), Inches(4.8), Inches(3.2))
]:
    if os.path.exists(img_path):
        slide.shapes.add_picture(img_path, left, top, width, height)

# Save output
out_d_path = r'd:\캡스톤판넬_산불dNBR_완성.pptx'
out_local_path = r'캡스톤판넬_산불dNBR_완성.pptx'

prs.save(out_local_path)
print(f"Saved complete PPTX to {out_local_path}")

try:
    prs.save(out_d_path)
    print(f"Saved complete PPTX to {out_d_path}")
except Exception as e:
    print(f"Could not save to {out_d_path}: {e}")
