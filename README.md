# 🌲 Korea GeoFire Explorer (대한민국 산불 이력 & dNBR 피해 비교 분석 시스템)

대한민국 국토 내 역대 주요 산불 발생 지역 및 실재 산불 발생 날짜별위성 데이터 기반 **dNBR (Normalized Burn Ratio)** 산불 피해 위험도 및 변화를 시각적으로 분석/비교할 수 있는 인터랙티브 웹 애플리케이션입니다.

---

## 🌟 주요 기능 (Key Features)

1. **인터랙티브 위치 및 지역 선택**:
   - 지점 클릭, 지명 검색, 또는 주요 산불 지자체 드롭다운을 통해 간편하게 위치 선택.
2. **역대 산불 이력 데이터 연동**:
   - 강릉/동해, 울진/삼척, 고성/속초, 안동, 밀양, 합천, 서울 인왕산 등 실재 산불 데이터 제공.
3. **dNBR 피해 등급 시각화**:
   - 미피해(정상), 경도 피해, 중경도 피해, 중중도 피해, 중증 피해 등 6단계 심해도 등급 시각화.
4. **분할 비교 모드 (Compare View)**:
   - 정상일 vs 산불 피해 발생일 듀얼 뷰포트 동기화 비교.
5. **통계 데이터 & 내보내기**:
   - 피해 심해도 비율 차트, CSV 내보내기 및 리포트 인쇄 기능 지원.

---

## 🚀 실행 방법 (Getting Started)

### 1. 웹 브라우저에서 바로 사용하기 (GitHub Pages)
배포된 웹 사이트를 통해 별도 설치 없이 접속할 수 있습니다:
👉 `https://<YOUR-GITHUB-USERNAME>.github.io/<YOUR-REPO-NAME>/`

---

### 2. 로컬에서 실행하기 (Local Server - (https://capstone23-azure.vercel.app/)

1. 저장소 클론 (Repository Clone):
```bash
git clone https://github.com/<YOUR-GITHUB-USERNAME>/<YOUR-REPO-NAME>.git
cd <YOUR-REPO-NAME>
```

2. 로컬 웹 서버 실행 (Python 기본 서버 사용):
```bash
python -m http.server 8080
```

3. 웹 브라우저 접속:
`https://capstone23-azure.vercel.app/`

---

## 📂 프로젝트 구조 (Project Structure)

```
├── index.html               # 메인 HTML 구조
├── index.css                # 스타일시트 (디자인 시스템 & 테마)
├── main.js                  # 지도(Leaflet), 차트(Chart.js) 및 dNBR 시각화 로직
├── panel_assets/            # 이미지 및 정적 자산
├── sample_structure.json    # sample 데이터 파일
├── real_landsat_app.py      # Python GUI 버전 애플리케이션
├── gee_dnbr_analysis.py     # Google Earth Engine / Landsat dNBR 연산 스크립트
└── README.md                # 프로젝트 문서
```

---

## 📄 라이선스 (License)
MIT License
