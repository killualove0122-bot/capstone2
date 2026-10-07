"""
Google Earth Engine (GEE) Python API 기반 dNBR 산출 및 산불 피해 심각도 분석표 자동 생성 스크립트

사용 방법:
1. earthengine-api 및 geemap 라이브러리 설치: pip install earthengine-api geemap pandas matplotlib
2. ee.Initialize() 완료 후 스크립트 실행
"""

import ee
import pandas as pd

# Google Earth Engine 초기화
try:
    ee.Initialize()
except Exception as e:
    print("GEE 인증이 필요합니다. 'ee.Authenticate()'를 먼저 실행하세요.")

def calculate_dnbr_and_severity(geometry, fire_date, pre_days=30, post_days=30):
    """
    특정 ROI 영역과 산불 발생 일자를 기반으로 Sentinel-2 위성의 dNBR 및 심각도 통계를 계산합니다.
    """
    fire_date_ee = ee.Date(fire_date)
    pre_start = fire_date_ee.advance(-pre_days, 'day')
    pre_end = fire_date_ee
    post_start = fire_date_ee
    post_end = fire_date_ee.advance(post_days, 'day')

    # Sentinel-2 SR 컬렉션 가져오기
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(geometry) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

    # Pre-fire & Post-fire 중간값(Median) 합성
    pre_img = s2.filterDate(pre_start, pre_end).median().clip(geometry)
    post_img = s2.filterDate(post_start, post_end).median().clip(geometry)

    # NBR 계산: (B8 - B12) / (B8 + B12)
    pre_nbr = pre_img.normalizedDifference(['B8', 'B12']).rename('pre_nbr')
    post_nbr = post_img.normalizedDifference(['B8', 'B12']).rename('post_nbr')

    # dNBR 계산 (scaled by 1000)
    dnbr = pre_nbr.subtract(post_nbr).multiply(1000).rename('dnbr')

    # USGS 심각도 등급 재분류 (Reclassification)
    # 1: High Regrowth (< -500)
    # 2: Unburned / Low Regrowth (-500 ~ 99)
    # 3: Low Severity (100 ~ 269)
    # 4: Moderate-Low Severity (270 ~ 439)
    # 5: Moderate-High Severity (440 ~ 650)
    # 6: High Severity (> 650)
    severity_img = ee.Image(0) \
        .where(dnbr.lt(-500), 1) \
        .where(dnbr.gte(-500).And(dnbr.lte(99)), 2) \
        .where(dnbr.gte(100).And(dnbr.lte(269)), 3) \
        .where(dnbr.gte(270).And(dnbr.lte(439)), 4) \
        .where(dnbr.gte(440).And(dnbr.lte(650)), 5) \
        .where(dnbr.gt(650), 6) \
        .rename('severity') \
        .clip(geometry)

    # 클래스별 면적(ha) 계산 (Pixel Area Count)
    area_img = ee.Image.pixelArea().divide(10000) # m2 -> ha
    stats = area_img.addBands(severity_img).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName='severity'),
        geometry=geometry,
        scale=10, # Sentinel-2 10m 해상도
        maxPixels=1e9
    )

    # 결과 정리
    severity_names = {
        1: "Enhanced Regrowth (고식생 회복)",
        2: "Unburned / Low Regrowth (미피해/저회복)",
        3: "Low Severity (경도 피해)",
        4: "Moderate-Low Severity (중경도 피해)",
        5: "Moderate-High Severity (중중도 피해)",
        6: "High Severity (중증 피해)"
    }

    groups = stats.get('groups').getInfo()
    data = []
    total_ha = sum([g['sum'] for g in groups])

    for g in groups:
        sev_code = int(g['severity'])
        area_ha = g['sum']
        pct = (area_ha / total_ha) * 100
        data.append({
            '등급 코드': sev_code,
            'USGS 심각도 등급': severity_names.get(sev_code, "기타"),
            '면적 (ha)': round(area_ha, 2),
            '면적 (km²)': round(area_ha / 100, 3),
            '비율 (%)': round(pct, 2)
        })

    df = pd.DataFrame(data).sort_values('등급 코드')
    return dnbr, severity_img, df

# 예시 실행 (2022 울진 산불 영역)
if __name__ == "__main__":
    # 울진 북면 ROI (Polygon)
    uljin_roi = ee.Geometry.Polygon([[
        [129.25, 37.00],
        [129.45, 37.00],
        [129.45, 37.15],
        [129.25, 37.15]
    ]])
    
    print("=== GEE 기반 dNBR 및 심각도 연산 시작 ===")
    # dnbr, severity_img, df_summary = calculate_dnbr_and_severity(uljin_roi, '2022-03-04')
    # print(df_summary.to_string(index=False))
