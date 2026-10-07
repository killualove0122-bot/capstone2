"""
===================================================================
대한민국 전 국토 선택 & 지역별 실재 산불 날짜 2차 선택 비교 분석 GUI
===================================================================
작동 방식:
1. 시작 시 어떤 지역 및 날짜도 선택되지 않은 깨끗한 대한민국 지도 대기 상태
2. 지도/드롭다운에서 지역 선택 ➔ 해당 지역의 실재 역대 산불 발생 날짜 목록 표출
3. 원하는 산불 발생 날짜 클릭 ➔ 위성 STAC 실시간 연산 & 정상일 vs 산불일 비교 표출
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import datetime
import io
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

SEVERITY_CLASSES = [
    {"name": "Enhanced Regrowth (고식생 회복)", "min": -9999, "max": -501, "color": "#006600"},
    {"name": "Unburned / Normal (미피해/정상)", "min": -500, "max": 99, "color": "#33cc33"},
    {"name": "Low Severity (경도 피해)", "min": 100, "max": 269, "color": "#ffff00"},
    {"name": "Moderate-Low Severity (중경도 피해)", "min": 270, "max": 439, "color": "#ff9900"},
    {"name": "Moderate-High Severity (중중도 피해)", "min": 440, "max": 650, "color": "#ff3300"},
    {"name": "High Severity (중증 피해)", "min": 651, "max": 9999, "color": "#7a0099"}
]

HISTORICAL_FIRES = {
    "강원 강릉시 옥계면 (옥계 산불)": {"lat": 37.6120, "lng": 129.0340, "dates": ["2022-03-05", "2019-04-04", "2004-03-10"]},
    "경북 울진군 북면 (울진·삼척 산불)": {"lat": 37.0583, "lng": 129.3514, "dates": ["2022-03-04", "2000-04-07"]},
    "강원 고성군 토성면 (고성 산불)": {"lat": 38.2012, "lng": 128.5123, "dates": ["2019-04-04", "2020-05-01"]},
    "강원 강릉시 난곡동 (도심 산불)": {"lat": 37.7942, "lng": 128.8878, "dates": ["2023-04-11"]},
    "경북 안동시 풍천면 (안동 산불)": {"lat": 36.6342, "lng": 128.6789, "dates": ["2020-04-24", "2021-02-21"]},
    "경남 밀양시 부북면 (밀양 산불)": {"lat": 35.5342, "lng": 128.7512, "dates": ["2022-05-31"]},
    "경남 합천군 룡주면 (합천 산불)": {"lat": 35.5210, "lng": 128.1120, "dates": ["2023-03-08"]},
    "서울 종로구 (인왕산 산불)": {"lat": 37.5850, "lng": 126.9530, "dates": ["2023-04-02"]}
}

class KoreaFireCompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("대한민국 지역 선택 ➔ 실재 산불 날짜 선택 dNBR 시스템 v3.0")
        self.root.geometry("1150x800")
        self.root.configure(bg="#0b0f19")

        self.selected_lat = None
        self.selected_lng = None
        self.selected_date = None
        self.current_analysis_data = None
        self.build_ui()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#111827", pady=10, padx=15)
        header.pack(fill="x")

        tk.Label(header, text="🌲 대한민국 지역 선택 ➔ 해당 지역 실재 산불 발생 날짜 선택 분석", font=("Pretendard", 15, "bold"), fg="#f97316", bg="#111827").pack(anchor="w")
        tk.Label(header, text="초기 대기 상태에서 먼저 분석할 지역을 선택하면 역대 산불 날짜가 활성화됩니다.", font=("Pretendard", 9), fg="#9ca3af", bg="#111827").pack(anchor="w")

        # Main Layout
        main_frame = tk.Frame(self.root, bg="#0b0f19", padx=15, pady=10)
        main_frame.pack(fill="both", expand=True)

        left_frame = tk.LabelFrame(main_frame, text=" 1. 지역 선택 및 산불 날짜 선택 ", font=("Pretendard", 10, "bold"), fg="#fb923c", bg="#1f293d", padx=10, pady=10)
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        tk.Label(left_frame, text="1단계: 분석 지역 선택:", font=("Pretendard", 9, "bold"), fg="#e5e7eb", bg="#1f293d").pack(anchor="w", pady=(0, 2))
        self.region_var = tk.StringVar(value="-- 지역을 선택하세요 --")
        region_cb = ttk.Combobox(left_frame, textvariable=self.region_var, values=list(HISTORICAL_FIRES.keys()), state="readonly", width=32)
        region_cb.pack(fill="x", pady=(0, 10))
        region_cb.bind("<<ComboboxSelected>>", self.on_region_select)

        coord_frame = tk.Frame(left_frame, bg="#1f293d")
        coord_frame.pack(fill="x", pady=(0, 10))

        tk.Label(coord_frame, text="위도:", font=("Pretendard", 8), fg="#9ca3af", bg="#1f293d").grid(row=0, column=0)
        self.lat_entry = tk.Entry(coord_frame, font=("Pretendard", 9), width=9)
        self.lat_entry.grid(row=0, column=1, padx=2)

        tk.Label(coord_frame, text="경도:", font=("Pretendard", 8), fg="#9ca3af", bg="#1f293d").grid(row=0, column=2)
        self.lng_entry = tk.Entry(coord_frame, font=("Pretendard", 9), width=9)
        self.lng_entry.grid(row=0, column=3, padx=2)

        tk.Label(left_frame, text="2단계: 해당 지역 산불 날짜 선택:", font=("Pretendard", 9, "bold"), fg="#e5e7eb", bg="#1f293d").pack(anchor="w", pady=(0, 2))
        self.date_var = tk.StringVar(value="-- 지역 선택 후 날짜 지정 --")
        self.date_cb = ttk.Combobox(left_frame, textvariable=self.date_var, values=[], state="disabled", width=32)
        self.date_cb.pack(fill="x", pady=(0, 10))
        self.date_cb.bind("<<ComboboxSelected>>", self.on_date_select)

        tk.Label(left_frame, text="위성 선택:", font=("Pretendard", 9), fg="#e5e7eb", bg="#1f293d").pack(anchor="w", pady=(0, 2))
        self.sensor_var = tk.StringVar(value="자동 최적 위성 (Sentinel-2 / Landsat)")
        sensor_cb = ttk.Combobox(left_frame, textvariable=self.sensor_var, values=["자동 최적 위성 (Sentinel-2 / Landsat)", "Sentinel-2 (10m)", "Landsat 8/9 (30m)"], state="readonly", width=32)
        sensor_cb.pack(fill="x", pady=(0, 15))

        self.run_btn = tk.Button(
            left_frame, 
            text="⚡ dNBR 위성 위험도 분석 실행", 
            font=("Pretendard", 10, "bold"), 
            fg="white", bg="#ef4444", relief="flat", state="disabled",
            command=self.start_analysis_thread
        )
        self.run_btn.pack(fill="x", pady=(0, 10))

        self.status_lbl = tk.Label(left_frame, text="먼저 지역을 선택해주세요.", font=("Pretendard", 8), fg="#9ca3af", bg="#1f293d", wraplength=220)
        self.status_lbl.pack(fill="x")

        # Right Display Area
        right_frame = tk.Frame(main_frame, bg="#0b0f19")
        right_frame.pack(side="right", fill="both", expand=True)

        self.plot_frame = tk.LabelFrame(right_frame, text=" 2. 정상일 (Pre-fire NBR) vs 산불 발생후 (Post-fire dNBR) 나란히 비교 ", font=("Pretendard", 10, "bold"), fg="#60a5fa", bg="#1f293d", padx=10, pady=10)
        self.plot_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.canvas_lbl = tk.Label(self.plot_frame, text="지역을 선택하고 산불 발생 날짜를 선택하면 실제 위성 분석 지도가 표출됩니다.", fg="#9ca3af", bg="#111827")
        self.canvas_lbl.pack(fill="both", expand=True)

        # Table Frame
        table_frame = tk.LabelFrame(right_frame, text=" 3. 산불 피해 심각도 집계표 ", font=("Pretendard", 10, "bold"), fg="#10b981", bg="#1f293d", padx=10, pady=5)
        table_frame.pack(fill="x")

        cols = ("cls", "range", "ha", "km2", "pct")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=5)
        self.tree.heading("cls", text="USGS 심각도 등급")
        self.tree.heading("range", text="dNBR 범주")
        self.tree.heading("ha", text="면적 (ha)")
        self.tree.heading("km2", text="면적 (km²)")
        self.tree.heading("pct", text="비율 (%)")
        self.tree.column("cls", width=220)
        self.tree.column("range", width=120, anchor="center")
        self.tree.column("ha", width=100, anchor="e")
        self.tree.column("km2", width=100, anchor="e")
        self.tree.column("pct", width=80, anchor="e")
        self.tree.pack(fill="x", pady=5)

        btn_box = tk.Frame(table_frame, bg="#1f293d")
        btn_box.pack(fill="x", pady=5)
        self.btn_export_csv = tk.Button(btn_box, text="📥 CSV 내보내기", font=("Pretendard", 9), fg="white", bg="#3b82f6", command=self.export_csv, state="disabled")
        self.btn_export_csv.pack(side="left", padx=5)
        self.btn_export_img = tk.Button(btn_box, text="🖼️ 시각화 PNG 저장", font=("Pretendard", 9), fg="white", bg="#10b981", command=self.export_img, state="disabled")
        self.btn_export_img.pack(side="left", padx=5)

    def on_region_select(self, event):
        val = self.region_var.get()
        if val in HISTORICAL_FIRES:
            info = HISTORICAL_FIRES[val]
            self.selected_lat = info["lat"]
            self.selected_lng = info["lng"]
            self.lat_entry.delete(0, tk.END); self.lat_entry.insert(0, str(info["lat"]))
            self.lng_entry.delete(0, tk.END); self.lng_entry.insert(0, str(info["lng"]))

            # Enable dates dropdown for selected region
            self.date_cb.config(state="readonly", values=info["dates"])
            self.date_var.set(info["dates"][0])
            self.selected_date = info["dates"][0]
            self.run_btn.config(state="normal")
            self.update_status(f"지역 선택됨 ({val}). 날짜를 확인 후 실행하세요.")

    def on_date_select(self, event):
        self.selected_date = self.date_var.get()

    def update_status(self, text):
        self.status_lbl.config(text=text)

    def start_analysis_thread(self):
        if not self.selected_lat or not self.selected_lng or not self.selected_date:
            messagebox.showwarning("선택 수락", "지역과 날짜를 먼저 선택하세요.")
            return

        self.run_btn.config(state="disabled")
        self.update_status("위성 서버에서 정밀 영상 탐색 중...")
        threading.Thread(target=self.run_analysis, daemon=True).start()

    def run_analysis(self):
        try:
            lat = self.selected_lat
            lng = self.selected_lng
            fire_date_str = self.selected_date

            delta_deg = 0.15
            bbox = [lng - delta_deg, lat - delta_deg, lng + delta_deg, lat + delta_deg]

            fire_date = datetime.datetime.strptime(fire_date_str, "%Y-%m-%d")
            pre_start = (fire_date - datetime.timedelta(days=35)).strftime("%Y-%m-%d")
            pre_end = fire_date_str
            post_start = fire_date_str
            post_end = (fire_date + datetime.timedelta(days=40)).strftime("%Y-%m-%d")

            self.root.after(0, self.update_status, f"Sentinel-2 / Landsat 위성 수집 중 ({fire_date_str})...")

            pre_item = self.search_stac_scene("sentinel-2-l2a", bbox, pre_start, pre_end)
            post_item = self.search_stac_scene("sentinel-2-l2a", bbox, post_start, post_end)
            used_coll = "sentinel-2-l2a"

            if not post_item:
                pre_item = self.search_stac_scene("landsat-c2-l2", bbox, pre_start, pre_end)
                post_item = self.search_stac_scene("landsat-c2-l2", bbox, post_start, post_end)
                used_coll = "landsat-c2-l2"

            if not pre_item or not post_item:
                raise ValueError("선택하신 조건의 구름 없는 위성 영상을 찾지 못했습니다.")

            nir_key = 'B08' if used_coll == 'sentinel-2-l2a' else 'nir08'
            swir_key = 'B12' if used_coll == 'sentinel-2-l2a' else 'swir22'

            pre_nir = self.fetch_band(used_coll, pre_item['id'], nir_key)
            pre_swir = self.fetch_band(used_coll, pre_item['id'], swir_key)
            post_nir = self.fetch_band(used_coll, post_item['id'], nir_key)
            post_swir = self.fetch_band(used_coll, post_item['id'], swir_key)

            nbr_pre = (pre_nir - pre_swir) / np.maximum(pre_nir + pre_swir, 1.0)
            nbr_post = (post_nir - post_swir) / np.maximum(post_nir + post_swir, 1.0)
            dnbr = (nbr_pre - nbr_post) * 1000.0

            # NoData & Unburned Masking (dNBR < 100 및 0 픽셀 마스킹)
            unburned_or_water_mask = (dnbr < 100) | (pre_nir == 0) | (pre_swir == 0)
            dnbr[unburned_or_water_mask] = np.nan

            total_area_ha = 30.0 * 30.0 * 100.0
            pixel_ha = total_area_ha / dnbr.size
            table_rows = []

            for cls in SEVERITY_CLASSES:
                mask = (dnbr >= cls["min"]) & (dnbr <= cls["max"])
                count = int(np.sum(mask))
                area_ha = count * pixel_ha
                table_rows.append({
                    "cls": cls["name"], "range": f"{cls['min']} ~ {cls['max']}",
                    "ha": round(area_ha, 1), "km2": round(area_ha / 100.0, 2),
                    "pct": round(count / dnbr.size * 100.0, 2), "color": cls["color"]
                })

            self.current_analysis_data = {
                "dnbr": dnbr, "nbr_pre": nbr_pre, "table": table_rows,
                "pre_date": pre_item['properties']['datetime'][:10],
                "post_date": post_item['properties']['datetime'][:10],
                "fire_date": fire_date_str
            }

            self.root.after(0, self.render_results)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
        finally:
            self.root.after(0, lambda: self.run_btn.config(state="normal"))

    def search_stac_scene(self, collection, bbox, start_date, end_date):
        url = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
        payload = {"collections": [collection], "bbox": bbox, "datetime": f"{start_date}/{end_date}", "query": {"eo:cloud_cover": {"lt": 40}}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if data.get('features'):
                data['features'].sort(key=lambda x: x['properties']['eo:cloud_cover'])
                return data['features'][0]
        return None

    def fetch_band(self, collection, item_id, band_name):
        url = f"https://planetarycomputer.microsoft.com/api/data/v1/item/preview.png?collection={collection}&item={item_id}&assets={band_name}&format=png"
        with urllib.request.urlopen(url) as resp:
            img = Image.open(io.BytesIO(resp.read())).convert('L')
            return np.array(img, dtype=np.float32)

    def render_results(self):
        data = self.current_analysis_data
        for item in self.tree.get_children(): self.tree.delete(item)
        for row in data["table"]:
            self.tree.insert("", "end", values=(row["cls"], row["range"], f"{row['ha']:,}", row["km2"], f"{row['pct']}%"))

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4.2), facecolor="#1f293d")
        ax1.set_facecolor("#111827"); ax2.set_facecolor("#111827")

        ax1.imshow(data["nbr_pre"], cmap="YlGn")
        ax1.set_title(f"산불 미발생 정상일 식생 ({data['pre_date']})", color="white", fontsize=10, fontweight="bold")
        ax1.axis("off")

        cmap_colors = [c["color"] for c in SEVERITY_CLASSES]
        norm = mcolors.BoundaryNorm([-1000, -500, 100, 270, 440, 650, 2000], len(cmap_colors))
        cmap = mcolors.ListedColormap(cmap_colors)

        ax2.imshow(data["dnbr"], cmap=cmap, norm=norm)
        ax2.set_title(f"산불 발생후 피해 위험도 dNBR ({data['post_date']})", color="white", fontsize=10, fontweight="bold")
        ax2.axis("off")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=130, facecolor=fig.get_facecolor())
        buf.seek(0); plt.close(fig)

        img_tk = ImageTk.PhotoImage(Image.open(buf))
        self.canvas_lbl.config(image=img_tk, text="")
        self.canvas_lbl.image = img_tk

        self.btn_export_csv.config(state="normal")
        self.btn_export_img.config(state="normal")
        self.update_status(f"비교 완료: {data['pre_date']} (정상) vs {data['post_date']} (산불후)")

    def export_csv(self):
        if not self.current_analysis_data: return
        filename = filedialog.asksaveasfilename(defaultextension=".csv")
        if filename:
            pd.DataFrame(self.current_analysis_data["table"]).to_csv(filename, index=False, encoding="utf-8-sig")

    def export_img(self):
        if not self.current_analysis_data: return
        filename = filedialog.asksaveasfilename(defaultextension=".png")
        if filename:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
            ax1.imshow(self.current_analysis_data["nbr_pre"], cmap="YlGn")
            ax1.set_title(f"Normal Pre-Fire Vegetation ({self.current_analysis_data['pre_date']})")
            cmap_colors = [c["color"] for c in SEVERITY_CLASSES]
            norm = mcolors.BoundaryNorm([-1000, -500, 100, 270, 440, 650, 2000], len(cmap_colors))
            ax2.imshow(self.current_analysis_data["dnbr"], cmap=mcolors.ListedColormap(cmap_colors), norm=norm)
            ax2.set_title(f"Post-Fire dNBR Burn Severity ({self.current_analysis_data['post_date']})")
            plt.savefig(filename, dpi=300, bbox_inches="tight")
            plt.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = KoreaFireCompareApp(root)
    root.mainloop()
