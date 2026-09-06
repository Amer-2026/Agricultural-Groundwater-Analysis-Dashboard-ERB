"""
Agricultural Groundwater Analysis Dashboard
============================================
Simple version with map full width and right sidebar.
"""

import json
import traceback
from datetime import datetime
from pathlib import Path

import ee
import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Fullscreen, MousePosition
from streamlit_folium import st_folium

# ==================== Translations ====================
TRANSLATIONS = {
    "en": {
        "page_title": "Groundwater Analysis",
        "dashboard_header": "🌊 Groundwater Analysis Dashboard — Erbil Region",
        "welcome_subtitle": "✨ Welcome! Select parameters and click 'Generate Map' to begin your analysis.",
        "select_date": "Select Date",
        "generate_analysis": "Generate Analysis",
        "nav_abstraction_mm": "Abstraction (mm)",
        "nav_abstraction_m3": "Abstraction (m³)",
        "nav_recharge": "Recharge",
        "statistics": "Statistics",
        "minimum": "Minimum",
        "maximum": "Maximum",
        "mean": "Mean",
        "click_map": "Click on the map to view time series data",
        "interactive_map": "Interactive Map",
        "time_series_analysis": "Time Series Analysis",
        "download_csv": "📥 Download as CSV",
        "raw_data": "View raw data",
        "regional_summary": "Regional Monthly Summary",
        "compute_summary": "Compute regional summary",
        "summary_help": "Average value over the whole study area for every month",
        "summary_title": "Regional mean per month",
        "computing": "Computing...",
        "no_data_month": "No data available for selected month and parameter",
        "error_map": "Error generating map",
        "about_tool": "ℹ️ About This Tool",
        "about_text": "Groundwater Analysis Dashboard for Erbil Region.",
    },
    "ar": {
        "page_title": "تحليل المياه الجوفية",
        "dashboard_header": "🌊 لوحة تحليل المياه الجوفية — منطقة أربيل",
        "welcome_subtitle": "✨ مرحباً! اختر المعاملات وانقر على 'إنشاء الخريطة' لبدء التحليل.",
        "select_date": "اختر التاريخ",
        "generate_analysis": "إنشاء التحليل",
        "nav_abstraction_mm": "السحب (مم)",
        "nav_abstraction_m3": "السحب (م³)",
        "nav_recharge": "التغذية الجوفية",
        "statistics": "الإحصاءات",
        "minimum": "الحد الأدنى",
        "maximum": "الحد الأقصى",
        "mean": "المتوسط",
        "click_map": "انقر على الخريطة لعرض بيانات السلاسل الزمنية",
        "interactive_map": "الخريطة التفاعلية",
        "time_series_analysis": "تحليل السلاسل الزمنية",
        "download_csv": "📥 تنزيل بصيغة CSV",
        "raw_data": "عرض البيانات الخام",
        "regional_summary": "الملخص الشهري الإقليمي",
        "compute_summary": "حساب الملخص الإقليمي",
        "summary_help": "متوسط القيمة على كامل منطقة الدراسة لكل شهر",
        "summary_title": "المتوسط الإقليمي شهرياً",
        "computing": "جارٍ الحساب...",
        "no_data_month": "لا توجد بيانات للشهر والمعامل المحددين",
        "error_map": "خطأ في إنشاء الخريطة",
        "about_tool": "ℹ️ حول هذه الأداة",
        "about_text": "لوحة تحليل المياه الجوفية لمنطقة أربيل.",
    },
    "ku": {
        "page_title": "شیکردنەوەی ئاوی ژێرزەوی",
        "dashboard_header": "🌊 شیکردنەوەی ئاوی ژێرزەوی — هەرێمی هەولێر",
        "welcome_subtitle": "✨ بەخێربێیت! پارامەترەکان هەڵبژێرە و کلیک لە 'دروستکردنی نەخشە' بکە.",
        "select_date": "بەروار هەڵبژێرە",
        "generate_analysis": "دروستکردنی شیکردنەوە",
        "nav_abstraction_mm": "دەرهێنان (مم)",
        "nav_abstraction_m3": "دەرهێنان (م³)",
        "nav_recharge": "پڕبوونەوە",
        "statistics": "ئامارەکان",
        "minimum": "کەمترین",
        "maximum": "زۆرترین",
        "mean": "تێکڕا",
        "click_map": "لەسەر نەخشەکە کلیک بکە بۆ بینینی داتای زنجیرەکاتی",
        "interactive_map": "نەخشەی کارلێک",
        "time_series_analysis": "شیکردنەوەی زنجیرەکاتی",
        "download_csv": "📥 دابەزاندن وەک CSV",
        "raw_data": "داتای خاو",
        "regional_summary": "پوختەی مانگانەی ناوچەیی",
        "compute_summary": "ژماردنی پوختەی ناوچەیی",
        "summary_help": "تێکڕای نرخ بۆ هەموو ناوچەی لێکۆڵینەوە بۆ هەر مانگێک",
        "summary_title": "تێکڕای ناوچەیی مانگانە",
        "computing": "تێژینەوە...",
        "no_data_month": "هیچ داتایەک بۆ مانگ و پارامەتری دیاریکراو بوونی نییە",
        "error_map": "هەڵە لە دروستکردنی نەخشە",
        "about_tool": "ℹ️ دەربارەی ئەم ئامرازە",
        "about_text": "پانێلی شیکردنەوەی ئاوی ژێرزەوی بۆ هەرێمی هەولێر.",
    },
}

def t(key):
    lang = st.session_state.get("lang", "en")
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# ==================== Country config ====================
APP_DIR = Path(__file__).parent
CONFIG_DIR = APP_DIR / "config"

@st.cache_data
def load_country_configs():
    configs = {}
    search_dirs = [CONFIG_DIR, APP_DIR] if CONFIG_DIR.is_dir() else [APP_DIR]
    for folder in search_dirs:
        for f in sorted(folder.glob("*.json")):
            try:
                cfg = json.loads(f.read_text(encoding="utf-8"))
            except:
                continue
            if isinstance(cfg, dict) and "key" in cfg and "asset_path" in cfg:
                configs.setdefault(cfg["key"], cfg)
        if configs:
            break
    return configs

# ==================== Earth Engine ====================
def initialize_ee():
    try:
        if hasattr(st.secrets, "gee_credentials"):
            credentials_dict = dict(st.secrets["gee_credentials"])
            credentials = ee.ServiceAccountCredentials(
                credentials_dict["client_email"],
                key_data=json.dumps(credentials_dict),
            )
            project_id = credentials_dict.get("project_id")
            ee.Initialize(credentials, project=project_id)
        else:
            ee.Initialize()
        ee.Number(1).getInfo()
        return True
    except Exception as e:
        st.error(f"Earth Engine error: {e}")
        return False

@st.cache_resource(ttl=3600)
def get_ee_assets(asset_path):
    try:
        assets = ee.data.listAssets({"parent": asset_path})
        return [asset["id"] for asset in assets["assets"]]
    except Exception as e:
        st.error(f"Error getting assets: {e}")
        return []

def parse_asset_date(asset_id):
    try:
        parts = asset_id.split("_")
        year, month = parts[-2], parts[-1]
        return datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
    except:
        return None

# ==================== Map helpers ====================
def create_base_map(center_lat, center_lon, zoom):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap",
        name="OpenStreetMap",
        overlay=False,
        control=True,
    ).add_to(m)
    Fullscreen(position="topleft", force_separate_button=True).add_to(m)
    return m

def add_ee_layer(map_obj, ee_image, vis_params, name):
    map_id_dict = ee_image.getMapId(vis_params)
    folium.TileLayer(
        tiles=map_id_dict["tile_fetcher"].url_format,
        attr="Google Earth Engine",
        name=name,
        overlay=True,
        control=True,
        opacity=vis_params.get("opacity", 1.0),
    ).add_to(map_obj)
    return map_obj

PALETTES = {
    "abstraction_mm": ["#2b83ba", "#abdda4", "#ffffbf", "#fdae61", "#d7191c"],
    "abstraction_m3": ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027"],
    "recharge": ["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b", "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
}

@st.cache_data(ttl=3600)
def get_image_min_max(asset_id):
    img = ee.Image(asset_id)
    minmax = img.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=img.geometry(),
        scale=1000,
        maxPixels=1e9,
    ).getInfo()
    min_key = next(key for key in minmax if key.endswith("_min"))
    max_key = next(key for key in minmax if key.endswith("_max"))
    return minmax[min_key], minmax[max_key]

def get_vis_params(parameter, asset_id):
    min_val, max_val = get_image_min_max(asset_id)
    palette = PALETTES.get(parameter, PALETTES["recharge"])
    return {"min": min_val, "max": max_val, "palette": palette}

def add_colormap(m, vis_params, parameter):
    colormap = folium.LinearColormap(
        colors=vis_params["palette"],
        vmin=vis_params["min"],
        vmax=vis_params["max"],
        caption=f"{parameter} Legend",
    )
    colormap.add_to(m)

# ==================== Main app ====================
def main():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    if "selected_parameter" not in st.session_state:
        st.session_state.selected_parameter = "abstraction_mm"
    if "selected_date_str" not in st.session_state:
        st.session_state.selected_date_str = None
    if "map_generated" not in st.session_state:
        st.session_state.map_generated = False

    st.set_page_config(page_title=t("page_title"), page_icon="💧", layout="wide", initial_sidebar_state="collapsed")

    # ---- Load config ----
    configs = load_country_configs()
    if not configs:
        st.error("No country configuration found.")
        st.stop()

    country_keys = list(configs.keys())
    selected_country = country_keys[0] if len(country_keys) == 1 else country_keys[0]
    cfg = configs[selected_country]

    # ---- HEADER ----
    col_title, col_lang = st.columns([6, 1])
    with col_title:
        st.markdown(f"<h1 style='font-size: 2rem; margin: 0;'>{t('dashboard_header')}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.9rem; color: #6b7280; margin: 0;'>{cfg.get('name_en', '')} | {datetime.now().strftime('%Y')}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 0.9rem; font-weight: 700; color: #0066cc; margin: 0.25rem 0 0 0;'>{t('welcome_subtitle')}</p>", unsafe_allow_html=True)

    with col_lang:
        lang_options = {"English": "en", "العربية": "ar", "کوردی": "ku"}
        current_label = next(k for k, v in lang_options.items() if v == st.session_state.lang)
        selected_label = st.selectbox("🌐", options=list(lang_options.keys()), index=list(lang_options.keys()).index(current_label), key="lang_selector", label_visibility="collapsed")
        if lang_options[selected_label] != st.session_state.lang:
            st.session_state.lang = lang_options[selected_label]
            st.rerun()

    # ---- Navigation ----
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1.2, 1.2, 1.2, 1.5, 1.5])

    with nav_col1:
        if st.button(t("nav_abstraction_mm"), use_container_width=True):
            st.session_state.selected_parameter = "abstraction_mm"
            st.session_state.map_generated = False
            st.rerun()

    with nav_col2:
        if st.button(t("nav_abstraction_m3"), use_container_width=True):
            st.session_state.selected_parameter = "abstraction_m3"
            st.session_state.map_generated = False
            st.rerun()

    with nav_col3:
        if st.button(t("nav_recharge"), use_container_width=True):
            st.session_state.selected_parameter = "recharge"
            st.session_state.map_generated = False
            st.rerun()

    with nav_col4:
        try:
            asset_path = cfg["asset_path"]
            assets = get_ee_assets(asset_path)
            if assets:
                asset_dates = [d for d in (parse_asset_date(a) for a in assets) if d is not None]
                if asset_dates:
                    min_date, max_date = min(asset_dates), max(asset_dates)
                    months = pd.date_range(start=min_date, end=max_date, freq="MS")
                    date_options = [date.strftime("%Y-%m") for date in months]
                    selected_date_str = st.selectbox(t("select_date"), options=date_options, index=len(date_options) - 1, key="top_date_selector", label_visibility="collapsed")
                    st.session_state.selected_date_str = selected_date_str
        except:
            st.warning("Could not load dates")

    with nav_col5:
        if st.button("🚀 " + t("generate_analysis"), use_container_width=True, type="primary"):
            st.session_state.map_generated = True
            st.session_state.current_parameter = st.session_state.selected_parameter
            st.session_state.current_date = st.session_state.selected_date_str
            st.rerun()

    st.markdown("---")

    # ---- Earth Engine ----
    if not initialize_ee():
        st.error("Failed to initialize Earth Engine")
        return

    # ---- Main content ----
    if not st.session_state.map_generated:
        st.markdown(f"### 📊 {t('statistics')}")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric(t('minimum'), "—")
        with col2: st.metric(t('maximum'), "—")
        with col3: st.metric(t('mean'), "—")
        st.caption(t('click_map'))
    else:
        try:
            # ---- GET MAP DATA ----
            selected_date = datetime.strptime(st.session_state.current_date, "%Y-%m")
            selected_year_month = selected_date.strftime("%Y_%m")

            selected_asset = None
            for a in assets:
                if st.session_state.current_parameter in a and selected_year_month in a:
                    selected_asset = a
                    break

            if not selected_asset:
                st.error(t("no_data_month"))
                return

            center_lat = float(cfg["center_lat"])
            center_lon = float(cfg["center_lon"])
            zoom = int(cfg["zoom"])

            # ---- CREATE MAP ----
            m = create_base_map(center_lat, center_lon, zoom)
            ee_image = ee.Image(selected_asset)
            vis_params = get_vis_params(st.session_state.current_parameter, selected_asset)
            vis_params["opacity"] = 0.7

            add_ee_layer(m, ee_image, vis_params, f"{st.session_state.current_parameter} Layer")
            add_colormap(m, vis_params, st.session_state.current_parameter)
            folium.LayerControl().add_to(m)

            # ---- DISPLAY MAP WITH RIGHT SIDEBAR ----
            st.markdown(f"### 🗺️ {t('interactive_map')}")

            # Use sidebar for empty space (reserved for future content)
            # Main content shows the map full width
            # The sidebar will appear on the right
            
            # 🟡 Create a right sidebar for empty space
            with st.sidebar:
                st.markdown("### 🔜 Reserved for Future Content")
                st.markdown("---")
                st.info("This space is reserved for additional features, charts, or data visualizations that will be added in the future.")
                st.markdown("**Coming soon:**")
                st.markdown("- 📊 Additional charts")
                st.markdown("- 📈 Data tables")
                st.markdown("- 🔍 Advanced filters")
                st.markdown("- 📥 Export options")
            
            # 🟡 Display the map full width in the main area
            st_folium(m, width=None, height=500)

            # ---- Statistics under map ----
            st.markdown(f"### 📊 {t('statistics')}")
            try:
                stats = ee_image.reduceRegion(
                    reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), None, True),
                    geometry=ee_image.geometry(),
                    scale=1000,
                    maxPixels=1e9,
                ).getInfo()
                prefix = next((k[: -len("_mean")] for k in stats if k.endswith("_mean")), "b1")
                cols = st.columns(3)
                for col, stat_key, label in zip(cols, ["min", "max", "mean"], ["minimum", "maximum", "mean"]):
                    with col:
                        val = stats.get(f"{prefix}_{stat_key}")
                        st.metric(t(label), f"{val:.2f}" if isinstance(val, (int, float)) else "N/A")
            except Exception as e:
                st.error(f"Error calculating statistics: {e}")

        except Exception as e:
            st.error(f"{t('error_map')}: {str(e)}")
            st.error(traceback.format_exc())

    # ---- Footer ----
    st.markdown("---")
    with st.expander(t("about_tool")):
        st.markdown(t("about_text"))

if __name__ == "__main__":
    main()
