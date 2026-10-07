"""
Landsat 8/9 기반 산불 dNBR 산출 및 피해 심각도 시각화 프로그램 (Python)

필요 라이브러리:
pip install pystac-client planetary-computer rasterio numpy matplotlib folium pandas
"""

import os
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# Matplotlib 한글 폰트 설정 (Windows Malgun Gothic 지원)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

# STAC API 연동 (Microsoft Planetary Computer 또는 Element84)
try:
    import pystac_client
    import planetary_computer
    import rasterio
    HAS_STAC = True
except ImportError:
    HAS_STAC = False
    print("[안내] STAC 라이브러리가 없는 환경에서는 시뮬레이션 및 로컬 연산으로 동작합니다.")

# USGS 산불 피해 심각도 등급 정의 (Landsat dNBR * 1000 기준)
SEVERITY_CLASSES = [
    {"name": "Enhanced Regrowth (고식생 회복)", "min": -9999, "max": -501, "color": "#006600", "code": 1},
    {"name": "Unburned / Low Regrowth (미피해/저회복)", "min": -500, "max": 99, "color": "#33cc33", "code": 2},
    {"name": "Low Severity (경도 피해)", "min": 100, "max": 269, "color": "#ffff00", "code": 3},
    {"name": "Moderate-Low Severity (중경도 피해)", "min": 270, "max": 439, "color": "#ff9900", "code": 4},
    {"name": "Moderate-High Severity (중중도 피해)", "min": 440, "max": 650, "color": "#ff3300", "code": 5},
    {"name": "High Severity (중증 피해)", "min": 651, "max": 9999, "color": "#7a0099", "code": 6}
]

class LandsatDNBRAnalyzer:
    def __init__(self, bbox, fire_date_str, pre_days=30, post_days=30):
        """
        :param bbox: [min_lon, min_lat, max_lon, max_lat] (경도/위도 좌표 범주)
        :param fire_date_str: 'YYYY-MM-DD' 형식의 산불 발생 날짜
        :param pre_days: 산불 전 탐색 일수 (기본 30일)
        :param post_days: 산불 후 탐색 일수 (기본 30일)
        """
        self.bbox = bbox
        self.fire_date = datetime.datetime.strptime(fire_date_str, "%Y-%m-%d")
        self.pre_days = pre_days
        self.post_days = post_days
        
    def fetch_landsat_stac(self):
        """ Planetary Computer STAC API를 이용해 Landsat 8/9 C2 L2 밴드 5(NIR) & 밴드 7(SWIR2) 수집 """
        if not HAS_STAC:
            raise RuntimeError("pystac_client 및 rasterio 라이브러리가 설치되어 있어야합니다.")

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        pre_start = (self.fire_date - datetime.timedelta(days=self.pre_days)).strftime("%Y-%m-%d")
        pre_end = self.fire_date.strftime("%Y-%m-%d")
        post_start = self.fire_date.strftime("%Y-%m-%d")
        post_end = (self.fire_date + datetime.timedelta(days=self.post_days)).strftime("%Y-%m-%d")

        print(f"[*] Pre-fire 기간 탐색: {pre_start} ~ {pre_end}")
        print(f"[*] Post-fire 기간 탐색: {post_start} ~ {post_end}")

        # Landsat 8/9 C2 L2 수집
        search_pre = catalog.search(
            collections=["landsat-c2-l2"],
            bbox=self.bbox,
            datetime=f"{pre_start}/{pre_end}",
            query={"eo:cloud_cover": {"lt": 20}}
        )
        search_post = catalog.search(
            collections=["landsat-c2-l2"],
            bbox=self.bbox,
            datetime=f"{post_start}/{post_end}",
            query={"eo:cloud_cover": {"lt": 20}}
        )

        items_pre = list(search_pre.items())
        items_post = list(search_post.items())

        if not items_pre or not items_post:
            raise ValueError("지정한 조건 내 구름 20% 이하의 Landsat 위성영상을 찾지 못했습니다.")

        item_pre = items_pre[0]
        item_post = items_post[0]

        print(f"[+] 선택된 Pre-fire 영상: {item_pre.id} ({item_pre.datetime})")
        print(f"[+] 선택된 Post-fire 영상: {item_post.id} ({item_post.datetime})")

        # Landsat 8/9: Band 5 = nir08, Band 7 = swir22
        b5_pre_url = item_pre.assets["nir08"].href
        b7_pre_url = item_pre.assets["swir22"].href
        b5_post_url = item_post.assets["nir08"].href
        b7_post_url = item_post.assets["swir22"].href

        with rasterio.open(b5_pre_url) as src:
            b5_pre = src.read(1).astype(np.float32)
        with rasterio.open(b7_pre_url) as src:
            b7_pre = src.read(1).astype(np.float32)
        with rasterio.open(b5_post_url) as src:
            b5_post = src.read(1).astype(np.float32)
        with rasterio.open(b7_post_url) as src:
            b7_post = src.read(1).astype(np.float32)

        return b5_pre, b7_pre, b5_post, b7_post

    def compute_nbr_and_dnbr(self, b5_pre, b7_pre, b5_post, b7_post):
        """ Landsat Band 5 (NIR) & Band 7 (SWIR2) 로 NBR 및 dNBR 연산 """
        # NBR = (B5 - B7) / (B5 + B7)
        denom_pre = b5_pre + b7_pre
        denom_pre[denom_pre == 0] = np.nan
        nbr_pre = (b5_pre - b7_pre) / denom_pre

        denom_post = b5_post + b7_post
        denom_post[denom_post == 0] = np.nan
        nbr_post = (b5_post - b7_post) / denom_post

        # dNBR = (NBR_pre - NBR_post) * 1000
        dnbr = (nbr_pre - nbr_post) * 1000.0
        return nbr_pre, nbr_post, dnbr

    def classify_severity(self, dnbr_array, pixel_resolution_m=30):
        """ dNBR 배열을 USGS 심각도 등급으로 분류하고 면적(ha) 계산 """
        severity_grid = np.zeros_like(dnbr_array, dtype=np.int32)
        
        # 30m x 30m Landsat 해상도 -> 1 Pixel = 900 m2 = 0.09 ha
        pixel_area_ha = (pixel_resolution_m * pixel_resolution_m) / 10000.0
        
        results = []
        total_pixels = np.count_nonzero(~np.isnan(dnbr_array))

        for cls in SEVERITY_CLASSES:
            mask = (dnbr_array >= cls["min"]) & (dnbr_array <= cls["max"])
            severity_grid[mask] = cls["code"]
            count = np.sum(mask)
            area_ha = count * pixel_area_ha
            pct = (count / total_pixels * 100) if total_pixels > 0 else 0

            results.append({
                "코드": cls["code"],
                "USGS 심각도 등급": cls["name"],
                "dNBR 범주": f"{cls['min']} ~ {cls['max']}",
                "픽셀 수": count,
                "면적 (ha)": round(area_ha, 2),
                "면적 (km²)": round(area_ha / 100.0, 3),
                "비율 (%)": round(pct, 2)
            })

        df = pd.DataFrame(results)
        return severity_grid, df

    def generate_visual_report(self, dnbr_array, severity_grid, df_summary, output_prefix="landsat_dnbr_result"):
        """ Matplotlib 차트 및 시각화 이미지 파일 저장 """
        fig, axes = plt.subplots(1, 2, figsize=(16, 7))

        # 1. dNBR 래스터 지도
        cmap_colors = ["#006600", "#33cc33", "#ffff00", "#ff9900", "#ff3300", "#7a0099"]
        bounds = [-1000, -500, 100, 270, 440, 650, 2000]
        norm = mcolors.BoundaryNorm(bounds, len(cmap_colors))
        cmap = mcolors.ListedColormap(cmap_colors)

        im = axes[0].imshow(dnbr_array, cmap=cmap, norm=norm)
        axes[0].set_title(f"Landsat dNBR Burn Severity Map ({self.fire_date.strftime('%Y-%m-%d')})", fontsize=14, fontweight='bold')
        plt.colorbar(im, ax=axes[0], ticks=[-750, -200, 185, 355, 545, 1000], label="dNBR (x1000)")

        # 2. 심각도 면적 파이 차트
        labels = df_summary["USGS 심각도 등급"]
        areas = df_summary["면적 (ha)"]
        colors = [c["color"] for c in SEVERITY_CLASSES]

        axes[1].pie(areas, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        axes[1].set_title("Burn Severity Area Breakdown (ha)", fontsize=14, fontweight='bold')

        plt.tight_layout()
        img_file = f"{output_prefix}_plot.png"
        plt.savefig(img_file, dpi=200)
        print(f"[+] 시각화 그래프 저장 완료: {img_file}")
        plt.close()

# 테스트 실행 예시 (2022 울진 산불 영역)
if __name__ == "__main__":
    # 울진 북면 경도/위도 BBOX: [min_lon, min_lat, max_lon, max_lat]
    uljin_bbox = [129.25, 37.00, 129.45, 37.15]
    fire_date = "2022-03-04"

    analyzer = LandsatDNBRAnalyzer(bbox=uljin_bbox, fire_date_str=fire_date)
    print(f"=== Landsat 8/9 dNBR 산불 심각도 분석 시작 (날짜: {fire_date}) ===")

    # 시뮬레이션 모드 테스트
    width, height = 150, 150
    np.random.seed(42)
    b5_pre = np.random.uniform(0.3, 0.5, (height, width))
    b7_pre = np.random.uniform(0.1, 0.2, (height, width))
    b5_post = b5_pre.copy()
    b7_post = b7_pre.copy()

    # 화재 구역 주입
    cy, cx = 75, 75
    y, x = np.ogrid[:height, :width]
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    burn_mask = dist < 45
    b5_post[burn_mask] *= 0.35  # NIR 감소
    b7_post[burn_mask] *= 2.2   # SWIR2 증가

    nbr_pre, nbr_post, dnbr = analyzer.compute_nbr_and_dnbr(b5_pre, b7_pre, b5_post, b7_post)
    severity_grid, df_summary = analyzer.classify_severity(dnbr, pixel_resolution_m=30)

    print("\n[ 분석 결과: USGS 산불 피해 심각도 분석표 ]")
    print(df_summary.to_string(index=False))

    analyzer.generate_visual_report(dnbr, severity_grid, df_summary)
