"""
Agricultural Groundwater Analysis Dashboard
============================================
A single, configurable Streamlit app serving all country deployments
(Jordan, Iraq, Palestine, ...). Country settings live in config/*.json —
to add a new country you only add a config file and the GEE assets.

Data: monthly abstraction (mm, m3) and recharge images stored as
Google Earth Engine assets named  <parameter>_<YYYY>_<MM>.

Authentication: a GEE service-account key stored in Streamlit secrets
under [gee_credentials]  (see docs/03_deploy_streamlit_EN.md).
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
        "dashboard_header": "Groundwater Analysis Dashboard — Erbil Region",
        "country": "Country / Area",
        "ee_init_failed": "Failed to initialize Earth Engine. Please check your credentials.",
        "ee_init_critical": "Critical Error Initializing Earth Engine",
        "ee_init_default": "Earth Engine initialized with default credentials",
        "ee_verify_failed": "Earth Engine verification failed",
        "ee_init_error": "Earth Engine initialization failed",
        "control_panel": "Control Panel",
        "location_settings": "📍 Location Settings",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "zoom_level": "Zoom Level",
        "data_selection": "Data Selection",
        "parameter": "Parameter",
        "parameter_help": "Choose the parameter to visualize",
        "no_assets": "No assets found in the specified path. Please verify the path and permissions.",
        "no_dates": "No valid dates found in assets",
        "month": "Month",
        "visual_settings": "🎨 Visual Settings",
        "layer_opacity": "Layer Opacity",
        "generate_map": "Generate Map",
        "error_asset": "Error in asset handling",
        "interactive_map": "Interactive Map",
        "no_data_month": "No data available for selected month and parameter",
        "statistics": "Statistics",
        "time_series_analysis": "Time Series Analysis",
        "click_map": "Click on the map to view time series data for that location",
        "error_map": "Error generating map",
        "welcome_title": "Welcome to the Groundwater Analysis Dashboard",
        "welcome_text": "Select parameters and click 'Generate Map' to begin your analysis",
        "about_tool": "ℹ️ About This Tool",
        "about_text": """This dashboard provides comprehensive groundwater analysis capabilities:

- 🌍 **Interactive Visualization**: View monthly groundwater data on an interactive map
- 📊 **Statistical Analysis**: Access key statistics for the selected parameter
- 📈 **Time Series Analysis**: Click any location to view historical trends
- 📥 **Data Export**: Download time series and regional summaries as CSV
- 🎨 **Customizable Display**: Adjust visualization parameters to your needs

Data sources: FAO WaPOR v3 (actual evapotranspiration), CHIRPS (rainfall),
OpenLandMap (soil properties), processed in Google Earth Engine.

For support or more information, please contact the development team.""",
        "layer_statistics": "Layer Statistics",
        "minimum": "Minimum",
        "maximum": "Maximum",
        "mean": "Mean",
        "error_statistics": "Error calculating statistics",
        "no_data_location": "No data available for this location",
        "date": "Date",
        "time_series_title": "Time Series for {parameter} at ({lat}, {lon})",
        "legend": "{parameter} Legend",
        "layer": "Layer",
        "abstraction_mm": "Abstraction (mm)",
        "abstraction_m3": "Abstraction (m³)",
        "recharge": "Recharge",
        "error_get_assets": "Error in get_ee_assets",
        "error_parse_date": "Error parsing date from asset",
        "value_label": "Value",
        "download_csv": "📥 Download as CSV",
        "regional_summary": "📊 Regional Monthly Summary",
        "compute_summary": "Compute regional summary",
        "summary_help": "Average value over the whole study area for every month (may take up to a minute)",
        "summary_title": "Regional mean {parameter} per month",
        "computing": "Computing... this may take a minute",
        "raw_data": "View raw data",
        "nav_abstraction_mm": "Abstraction (mm)",
        "nav_abstraction_m3": "Abstraction (m³)",
        "nav_recharge": "Recharge",
        "data_status": "Data Status",
        "active_months": "Active Months",
        "last_update": "Last Update",
        "select_date": "Select Date",
        "generate_analysis": "Generate Analysis",
        "welcome_subtitle": "✨ Welcome! Select parameters and click 'Generate Map' to begin your analysis.",
    },
    "ar": {
        "page_title": "تحليل المياه الجوفية",
        "dashboard_header": "لوحة تحليل المياه الجوفية — منطقة أربيل",
        "country": "الدولة / المنطقة",
        "ee_init_failed": "فشل تهيئة محرك الأرض. يرجى التحقق من بيانات الاعتماد.",
        "ee_init_critical": "خطأ حرج في تهيئة محرك الأرض",
        "ee_init_default": "تم تهيئة محرك الأرض ببيانات الاعتماد الافتراضية",
        "ee_verify_failed": "فشل التحقق من محرك الأرض",
        "ee_init_error": "فشل تهيئة محرك الأرض",
        "control_panel": "لوحة التحكم",
        "location_settings": "📍 إعدادات الموقع",
        "latitude": "خط العرض",
        "longitude": "خط الطول",
        "zoom_level": "مستوى التكبير",
        "data_selection": "اختيار البيانات",
        "parameter": "المعامل",
        "parameter_help": "اختر المعامل للتصور",
        "no_assets": "لم يتم العثور على أصول في المسار المحدد. يرجى التحقق من المسار والأذونات.",
        "no_dates": "لم يتم العثور على تواريخ صالحة في الأصول",
        "month": "الشهر",
        "visual_settings": "🎨 إعدادات العرض",
        "layer_opacity": "شفافية الطبقة",
        "generate_map": "إنشاء الخريطة",
        "error_asset": "خطأ في معالجة الأصول",
        "interactive_map": "الخريطة التفاعلية",
        "no_data_month": "لا توجد بيانات للشهر والمعامل المحددين",
        "statistics": "الإحصاءات",
        "time_series_analysis": "تحليل السلاسل الزمنية",
        "click_map": "انقر على الخريطة لعرض بيانات السلاسل الزمنية لذلك الموقع",
        "error_map": "خطأ في إنشاء الخريطة",
        "welcome_title": "مرحباً بكم في لوحة تحليل المياه الجوفية",
        "welcome_text": "اختر المعاملات وانقر على 'إنشاء الخريطة' لبدء التحليل",
        "about_tool": "ℹ️ حول هذه الأداة",
        "about_text": """توفر هذه اللوحة إمكانيات شاملة لتحليل المياه الجوفية:

- 🌍 **التصور التفاعلي**: عرض بيانات المياه الجوفية الشهرية على خريطة تفاعلية
- 📊 **التحليل الإحصائي**: الوصول إلى الإحصاءات الرئيسية للمعامل المحدد
- 📈 **تحليل السلاسل الزمنية**: انقر على أي موقع لعرض الاتجاهات التاريخية
- 📥 **تصدير البيانات**: تنزيل السلاسل الزمنية والملخصات الإقليمية بصيغة CSV
- 🎨 **عرض قابل للتخصيص**: ضبط معاملات التصور حسب احتياجاتك

مصادر البيانات: FAO WaPOR v3 (التبخر-نتح الفعلي)، CHIRPS (الأمطار)،
OpenLandMap (خصائص التربة)، تمت المعالجة في Google Earth Engine.

للدعم أو مزيد من المعلومات، يرجى الاتصال بفريق التطوير.""",
        "layer_statistics": "إحصاءات الطبقة",
        "minimum": "الحد الأدنى",
        "maximum": "الحد الأقصى",
        "mean": "المتوسط",
        "error_statistics": "خطأ في حساب الإحصاءات",
        "no_data_location": "لا توجد بيانات لهذا الموقع",
        "date": "التاريخ",
        "time_series_title": "السلسلة الزمنية لـ {parameter} عند ({lat}, {lon})",
        "legend": "مفتاح {parameter}",
        "layer": "طبقة",
        "abstraction_mm": "السحب (مم)",
        "abstraction_m3": "السحب (م³)",
        "recharge": "التغذية الجوفية",
        "error_get_assets": "خطأ في جلب الأصول",
        "error_parse_date": "خطأ في تحليل التاريخ من الأصل",
        "value_label": "القيمة",
        "download_csv": "📥 تنزيل بصيغة CSV",
        "regional_summary": "📊 الملخص الشهري الإقليمي",
        "compute_summary": "حساب الملخص الإقليمي",
        "summary_help": "متوسط القيمة على كامل منطقة الدراسة لكل شهر (قد يستغرق دقيقة)",
        "summary_title": "المتوسط الإقليمي لـ {parameter} شهرياً",
        "computing": "جارٍ الحساب... قد يستغرق دقيقة",
        "raw_data": "عرض البيانات الخام",
        "nav_abstraction_mm": "السحب (مم)",
        "nav_abstraction_m3": "السحب (م³)",
        "nav_recharge": "التغذية الجوفية",
        "data_status": "حالة البيانات",
        "active_months": "الأشهر النشطة",
        "last_update": "آخر تحديث",
        "select_date": "اختر التاريخ",
        "generate_analysis": "إنشاء التحليل",
        "welcome_subtitle": "✨ مرحباً! اختر المعاملات وانقر على 'إنشاء الخريطة' لبدء التحليل.",
    },
    "ku": {
        "page_title": "شیکردنەوەی ئاوی ژێرزەوی",
        "dashboard_header": "شیکردنەوەی ئاوی ژێرزەوی — هەرێمی هەولێر",
        "country": "وڵات / ناوچە",
        "ee_init_failed": "دەستپێکردنی ئێرث ئینجین شکستی هێنا. تکایە ڕەقمەکانی خۆت بپشکنە.",
        "ee_init_critical": "هەڵەی گەورە لە دەستپێکردنی ئێرث ئینجین",
        "ee_init_default": "ئێرث ئینجین بە ڕەقمی بنەڕەتی دەستپێکرا",
        "ee_verify_failed": "پشکنینی ئێرث ئینجین شکستی هێنا",
        "ee_init_error": "دەستپێکردنی ئێرث ئینجین شکستی هێنا",
        "control_panel": "پانێلی کۆنتڕۆڵ",
        "location_settings": "📍 ڕێکخستنەکانی شوێن",
        "latitude": "پانی",
        "longitude": "درێژی",
        "zoom_level": "ئاستی زووم",
        "data_selection": "هەڵبژاردنی داتا",
        "parameter": "پارامەتر",
        "parameter_help": "پارامەتری خواست بۆ بینین هەڵبژێرە",
        "no_assets": "هیچ ئەستێک نەدۆزرایەوە لە ڕێڕەوی دیاریکراو. تکایە ڕێڕەوەکە و مۆڵەتەکان بپشکنە.",
        "no_dates": "هیچ بەروارێکی دروست نەدۆزرایەوە لە ئەستەکاندا",
        "month": "مانگ",
        "visual_settings": "🎨 ڕێکخستنەکانی بینین",
        "layer_opacity": "ڕوونی چین",
        "generate_map": "دروستکردنی نەخشە",
        "error_asset": "هەڵە لە بەرکارهێنانی ئەست",
        "interactive_map": "نەخشەی کارلێک",
        "no_data_month": "هیچ داتایەک بۆ مانگ و پارامەتری دیاریکراو بوونی نییە",
        "statistics": "ئامارەکان",
        "time_series_analysis": "شیکردنەوەی زنجیرەکاتی",
        "click_map": "لەسەر نەخشەکە کلیک بکە بۆ بینینی داتای زنجیرەکاتی بۆ ئەو شوێنە",
        "error_map": "هەڵە لە دروستکردنی نەخشە",
        "welcome_title": "بەخێربێیت بۆ پانێلی شیکردنەوەی ئاوی ژێرزەوی",
        "welcome_text": "پارامەترەکان هەڵبژێرە و کلیک لە 'دروستکردنی نەخشە' بکە بۆ دەستپێکردنی شیکردنەوەکەت",
        "about_tool": "ℹ️ دەربارەی ئەم ئامرازە",
        "about_text": """ئەم پانێلە توانای شیکردنەوەی گشتگیری ئاوی ژێرزەوی دابین دەکات:

- 🌍 **بینینی کارلێک**: داتای ئاوی ژێرزەوی مانگانە لەسەر نەخشەی کارلێک ببینە
- 📊 **شیکردنەوەی ئاماری**: دەستگەیشتن بە ئامارە سەرەکییەکان بۆ پارامەتری دیاریکراو
- 📈 **شیکردنەوەی زنجیرەکاتی**: کلیک لەسەر هەر شوێنێک بکە بۆ بینینی ڕەوتە مێژووییەکان
- 📥 **هەناردنی داتا**: دابەزاندنی زنجیرەکات و پوختەی ناوچەیی وەک CSV
- 🎨 **پیشاندانی گونجاو**: ڕێکخستنی پارامەترەکانی بینین بەپێی پێویستییەکانی تۆ

سەرچاوەکانی داتا: FAO WaPOR v3، CHIRPS، OpenLandMap، لە Google Earth Engine دا پرسەکراوە.

بۆ پشتیوانی یان زانیاری زیاتر، تکایە پەیوەندی بە تیمی پەرەپێدانەوە بکە.""",
        "layer_statistics": "ئاماری چین",
        "minimum": "کەمترین",
        "maximum": "زۆرترین",
        "mean": "تێکڕا",
        "error_statistics": "هەڵە لە ژماردنی ئامارەکان",
        "no_data_location": "هیچ داتایەک بۆ ئەم شوێنە بوونی نییە",
        "date": "بەروار",
        "time_series_title": "زنجیرەکات بۆ {parameter} لە ({lat}, {lon})",
        "legend": "ڕێنوێنی {parameter}",
        "layer": "چین",
        "abstraction_mm": "دەرهێنان (مم)",
        "abstraction_m3": "دەرهێنان (م³)",
        "recharge": "پڕبوونەوە",
        "error_get_assets": "هەڵە لە هێنانی ئەستەکان",
        "error_parse_date": "هەڵە لە شیکردنەوەی بەروار لە ئەست",
        "value_label": "نرخ",
        "download_csv": "📥 دابەزاندن وەک CSV",
        "regional_summary": "📊 پوختەی مانگانەی ناوچەیی",
        "compute_summary": "ژماردنی پوختەی ناوچەیی",
        "summary_help": "تێکڕای نرخ بۆ هەموو ناوچەی لێکۆڵینەوە بۆ هەر مانگێک (لەوانەیە خولەکێک بخایەنێت)",
        "summary_title": "تێکڕای ناوچەیی {parameter} بۆ هەر مانگێک",
        "computing": "تێژینەوە... لەوانەیە خولەکێک بخایەنێت",
        "raw_data": "داتای خاو",
        "nav_abstraction_mm": "دەرهێنان (مم)",
        "nav_abstraction_m3": "دەرهێنان (م³)",
        "nav_recharge": "پڕبوونەوە",
        "data_status": "دۆخی داتا",
        "active_months": "مانگە چالاکەکان",
        "last_update": "دوایین نوێکردنەوە",
        "select_date": "بەروار هەڵبژێرە",
        "generate_analysis": "دروستکردنی شیکردنەوە",
        "welcome_subtitle": "✨ بەخێربێیت! پارامەترەکان هەڵبژێرە و کلیک لە 'دروستکردنی نەخشە' بکە بۆ دەستپێکردنی شیکردنەوەکەت.",
    },
}


def t(key, **kwargs):
    """Get translated string for the current language"""
    lang = st.session_state.get("lang", "en")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


# ==================== Country configuration ====================
APP_DIR = Path(__file__).parent
CONFIG_DIR = APP_DIR / "config"


@st.cache_data
def load_country_configs():
    """Load all country config files.

    Looks first in a `config/` folder, then falls back to any *.json file
    sitting next to the app (a common setup mistake). Only files that look
    like a country config — i.e. contain a "key" and an "asset_path" — are
    accepted, so package files like requirements never get mistaken for one.
    """
    configs = {}
    search_dirs = [CONFIG_DIR, APP_DIR] if CONFIG_DIR.is_dir() else [APP_DIR]
    for folder in search_dirs:
        for f in sorted(folder.glob("*.json")):
            try:
                cfg = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if isinstance(cfg, dict) and "key" in cfg and "asset_path" in cfg:
                configs.setdefault(cfg["key"], cfg)
        if configs:  # stop at the first folder that yielded configs
            break
    return configs


def country_label(cfg):
    name = cfg["name_ar"] if st.session_state.get("lang") == "ar" else cfg["name_en"]
    return f"{cfg.get('flag', '')} {name}".strip()


# ==================== Earth Engine ====================
def initialize_ee():
    try:
        if hasattr(st.secrets, "gee_credentials"):
            credentials_dict = dict(st.secrets["gee_credentials"])
            credentials = ee.ServiceAccountCredentials(
                credentials_dict["client_email"],
                key_data=json.dumps(credentials_dict),
            )
            # Pass the Cloud project explicitly. Without it the newer
            # earthengine-api installed on Streamlit Cloud falls back to the
            # "earthengine-legacy" project and mangles cloud asset paths
            # (e.g. projects/earthengine-legacy/assets/projects/<id>/...).
            project_id = credentials_dict.get("project_id")
            ee.Initialize(credentials, project=project_id)
        else:
            ee.Initialize()
        ee.Number(1).getInfo()  # verify the connection actually works
        return True
    except Exception as e:
        st.error(f"{t('ee_init_error')}: {e}")
        st.error(traceback.format_exc())
        return False


@st.cache_resource(ttl=3600)
def get_ee_assets(asset_path):
    """List image asset ids inside an Earth Engine folder"""
    try:
        assets = ee.data.listAssets({"parent": asset_path})
        return [asset["id"] for asset in assets["assets"]]
    except Exception as e:
        st.error(f"{t('error_get_assets')}: {str(e)}")
        return []


def parse_asset_date(asset_id):
    """Parse date from asset ID (format: <parameter>_<YYYY>_<MM>)"""
    try:
        parts = asset_id.split("_")
        year, month = parts[-2], parts[-1]
        return datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
    except Exception:
        st.warning(f"{t('error_parse_date')}: {asset_id}")
        return None


# ==================== Map helpers ====================
def create_base_map(center_lat, center_lon, zoom):
    """Base map: satellite imagery default, OSM alternative, fullscreen control"""
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

    formatter = "function(num) {return L.Util.formatNum(num, 4) + '°';};"
    MousePosition(
        position="bottomleft",
        separator=" | ",
        prefix="Lat/Lon:",
        num_digits=4,
        lat_formatter=formatter,
        lng_formatter=formatter,
    ).add_to(m)

    return m


def add_ee_layer(map_obj, ee_image, vis_params, name):
    """Add an Earth Engine image as a tile layer on a folium map"""
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
    "abstraction_m3": ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8",
                        "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027"],
    "recharge": ["#a50026", "#d73027", "#f46d43", "#fdae61", "#fee08b",
                  "#ffffbf", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
}


@st.cache_data(ttl=3600)
def get_image_min_max(asset_id):
    """Min/max of an image asset (cached — one server call per asset)"""
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
        caption=t("legend", parameter=t(parameter)),
    )
    colormap.add_to(m)


# ==================== Analysis ====================
def _collection_with_dates(assets, parameter):
    """ImageCollection of one parameter with time_start parsed from asset names"""
    parameter_assets = [a for a in assets if parameter in a]
    images = ee.ImageCollection.fromImages([ee.Image(a) for a in parameter_assets])

    def add_date(img):
        parts = ee.String(img.get("system:id")).split("_")
        year = ee.Number.parse(parts.get(-2))
        month = ee.Number.parse(parts.get(-1))
        return img.set("system:time_start", ee.Date.fromYMD(year, month, 1).millis())

    return images.map(add_date).sort("system:time_start")


@st.cache_data(ttl=3600)
def get_time_series_data(point, parameter, assets):
    """Monthly values of `parameter` at a clicked point. point = [lat, lon]"""
    ee_point = ee.Geometry.Point([point[1], point[0]])
    images = _collection_with_dates(assets, parameter)

    time_series = images.map(
        lambda img: ee.Feature(
            None,
            {
                "date": img.get("system:time_start"),
                "value": img.reduceRegion(
                    reducer=ee.Reducer.first(), geometry=ee_point, scale=30
                ).values().get(0),
            },
        )
    )
    results = time_series.getInfo()

    processed = []
    for feature in results["features"]:
        props = feature["properties"]
        if props["value"] is not None:
            processed.append(
                {
                    "date": datetime.fromtimestamp(props["date"] / 1000),
                    "value": float(props["value"]),
                }
            )
    processed.sort(key=lambda x: x["date"])
    return processed


@st.cache_data(ttl=3600, show_spinner=False)
def get_regional_summary(parameter, assets, scale):
    """Mean value of `parameter` over the whole study area, for every month"""
    images = _collection_with_dates(assets, parameter)

    def region_mean(img):
        mean = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=img.geometry(),
            scale=max(scale, 100),  # coarse scale keeps this fast
            maxPixels=1e9,
        ).values().get(0)
        return ee.Feature(None, {"date": img.get("system:time_start"), "mean": mean})

    results = images.map(region_mean).getInfo()
    rows = []
    for feature in results["features"]:
        props = feature["properties"]
        if props.get("mean") is not None:
            rows.append(
                {
                    "date": datetime.fromtimestamp(props["date"] / 1000),
                    "mean": float(props["mean"]),
                }
            )
    rows.sort(key=lambda x: x["date"])
    return rows


def create_time_series_plot(time_series_data, parameter, lat, lon):
    df = pd.DataFrame(time_series_data)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=t("no_data_location"),
            xaxis_title=t("date"),
            yaxis_title=t(parameter),
        )
        return fig

    df = df.sort_values("date")
    months = [d.strftime("%Y-%m") for d in df["date"]]
    x_numeric = list(range(len(months)))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_numeric,
            y=df["value"].tolist(),
            mode="lines+markers",
            line=dict(color="#B429F9", width=2),
            marker=dict(size=8, color="#B429F9"),
            hovertemplate="%{text}: %{y:.2f}<extra></extra>",
            text=months,
        )
    )
    fig.update_layout(
        title=t("time_series_title", parameter=t(parameter), lat=f"{lat:.4f}", lon=f"{lon:.4f}"),
        xaxis=dict(
            title=t("date"),
            tickmode="array",
            tickvals=x_numeric,
            ticktext=months,
            tickangle=45,
            showgrid=True,
        ),
        yaxis=dict(title=t(parameter), showgrid=True, zeroline=True),
        template="plotly_white",
        height=400,
        margin=dict(t=50, b=80, l=50, r=50),
    )
    return fig


def to_csv_bytes(rows, value_col="value"):
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = df["date"].dt.strftime("%Y-%m")
    return df.to_csv(index=False).encode("utf-8")


# ==================== Main app ====================
def main():
    if "lang" not in st.session_state:
        st.session_state.lang = "en"
    
    if "selected_parameter" not in st.session_state:
        st.session_state.selected_parameter = "abstraction_mm"
    
    if "selected_date_str" not in st.session_state:
        st.session_state.selected_date_str = None

    st.set_page_config(
        page_title=t("page_title"),
        page_icon="💧",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # ---- DARK THEME CSS with Digital Berry Colors - Full Width ----
    st.markdown(
        """
        <style>
        /* Remove ALL padding and margins to allow full-width */
        .stApp {
            background-color: #0e1117 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* Remove default padding at the top and sides */
        .main .block-container {
            padding: 0rem !important;
            margin: 0rem !important;
            max-width: 100% !important;
        }
        
        /* Remove all side padding */
        .st-emotion-cache-1r6slb0 {
            padding: 0 !important;
        }
        
        /* Dark background for all containers */
        div[data-testid="stVerticalBlock"] {
            background-color: #0e1117 !important;
        }
        
        /* 🟡 DIGITAL BERRY: Full-width banner - spans entire screen */
        .banner {
            background: linear-gradient(135deg, 
                #1a0a2e 0%,
                #3d1b5e 10%,
                #6b2fa0 20%,
                #B429F9 35%,
                #26C5F3 50%,
                #B429F9 65%,
                #6b2fa0 80%,
                #3d1b5e 90%,
                #1a0a2e 100%
            );
            padding: 2.5rem 4rem 2rem 4rem;
            margin: 0 !important;
            width: 100vw !important;
            max-width: 100vw !important;
            position: relative;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            color: white;
            text-shadow: 0 2px 4px rgba(0,0,0,0.4);
            box-shadow: 0 4px 30px rgba(180, 41, 249, 0.3);
            overflow: hidden;
        }
        
        /* Digital sparkle overlay */
        .banner::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 30%, rgba(180, 41, 249, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 70%, rgba(38, 197, 243, 0.08) 0%, transparent 40%),
                        radial-gradient(circle at 50% 50%, rgba(107, 47, 160, 0.05) 0%, transparent 60%);
            pointer-events: none;
        }
        
        .banner-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1rem;
            position: relative;
            z-index: 1;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .banner-title {
            flex: 1;
            min-width: 200px;
        }
        
        .banner-title h1 {
            font-size: 2.2rem;
            font-weight: 700;
            margin: 0;
            padding: 0;
            color: white;
            text-shadow: 0 2px 20px rgba(180, 41, 249, 0.5);
        }
        
        .banner-title .subtitle {
            font-size: 1rem;
            color: rgba(255,255,255,0.85);
            margin: 0.25rem 0 0 0;
            padding: 0;
        }
        
        .banner-title .welcome {
            font-size: 0.95rem;
            font-weight: 500;
            color: rgba(255,255,255,0.9);
            margin: 0.5rem 0 0 0;
            padding: 0;
            text-shadow: 0 1px 10px rgba(180, 41, 249, 0.3);
        }
        
        /* Language selector in banner - right side */
        .banner-language {
            flex-shrink: 0;
            min-width: 120px;
        }
        
        .banner-language .stSelectbox > div > div {
            background: rgba(255,255,255,0.15) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2) !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.3rem 1rem !important;
            min-height: 36px !important;
            height: 36px !important;
            font-size: 0.9rem !important;
        }
        
        .banner-language .stSelectbox > div > div:hover {
            background: rgba(255,255,255,0.25) !important;
        }
        
        .banner-language .stSelectbox > div > div > div {
            color: white !important;
        }
        
        .banner-language .stSelectbox svg {
            fill: white !important;
            color: white !important;
        }
        
        .banner-language .stSelectbox > label {
            color: rgba(255,255,255,0.8) !important;
        }
        
        /* Content wrapper with padding */
        .content-wrapper {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }
        
        /* Dark background for all containers */
        div[data-testid="stVerticalBlock"] {
            background-color: #0e1117 !important;
        }
        
        /* Light text for headers and labels */
        h1, h2, h3, h4, h5, h6, label, .stMarkdown, .stText {
            color: #e0e0e0 !important;
        }
        
        /* ALL BUTTONS - Digital Berry colors */
        .stButton > button {
            background: linear-gradient(135deg, #B429F9, #26C5F3) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
            text-align: center !important;
            justify-content: center !important;
            align-items: center !important;
            display: flex !important;
            height: 38px !important;
            line-height: 1.2 !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #9A1FD4, #1EA8D4) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 2px 15px rgba(180, 41, 249, 0.5) !important;
            transform: translateY(-1px) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0px) !important;
        }
        
        /* LANGUAGE SELECTOR - Digital Berry colors */
        .stSelectbox > div > div {
            background: linear-gradient(135deg, #B429F9, #26C5F3) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            min-height: 38px !important;
            height: 38px !important;
            display: flex !important;
            align-items: center !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
        }
        
        .stSelectbox > div > div:hover {
            background: linear-gradient(135deg, #9A1FD4, #1EA8D4) !important;
        }
        
        .stSelectbox > div > div > div {
            color: white !important;
        }
        
        .stSelectbox > div > div > div[data-baseweb="select"] {
            color: white !important;
        }
        
        .stSelectbox > div > div > div[data-baseweb="select"] > div {
            color: white !important;
        }
        
        .stSelectbox > div > div > div[data-baseweb="select"] > div > div {
            color: white !important;
        }
        
        .stSelectbox [data-testid="stMarkdownContainer"] p {
            color: white !important;
        }
        
        .stSelectbox > label {
            color: white !important;
        }
        
        .stSelectbox svg {
            fill: white !important;
            color: white !important;
        }
        
        /* Dropdown menu items */
        .stSelectbox > div > div ul {
            background-color: #1a0a2e !important;
        }
        
        .stSelectbox > div > div ul li {
            color: white !important;
        }
        
        .stSelectbox > div > div ul li:hover {
            background: linear-gradient(135deg, #B429F9, #26C5F3) !important;
            color: white !important;
        }
        
        /* Dark background for metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            padding: 10px !important;
            border-radius: 8px !important;
            border: 1px solid rgba(180, 41, 249, 0.2) !important;
        }
        
        div[data-testid="stMetric"] label {
            color: #26C5F3 !important;
        }
        
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #e0e0e0 !important;
        }
        
        /* Dark background for info boxes */
        .stAlert {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }
        
        /* Dark background for expanders */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }
        
        .streamlit-expanderContent {
            background: linear-gradient(135deg, #1a0a2e, #2d1b4e) !important;
            color: #e0e0e0 !important;
        }
        
        /* Hide map attribution */
        .leaflet-control-attribution {
            display: none !important;
        }
        
        .folium-map .leaflet-control-attribution {
            display: none !important;
        }
        
        /* Dark background for dataframes */
        .stDataFrame {
            background-color: #1a0a2e !important;
        }
        
        /* Dark background for sidebar */
        .stSidebar {
            background-color: #0e1117 !important;
        }
        
        /* Divider color */
        hr {
            border-color: rgba(180, 41, 249, 0.3) !important;
        }
        
        /* Caption text */
        .stCaption {
            color: #9ca3af !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ---- TOP BAR: language + country ----
    configs = load_country_configs()

    if not configs:
        st.error(
            "No country configuration was found.\n\n"
            "The app expects at least one country JSON file (with a `key` and an "
            "`asset_path`) inside a **`config/`** folder next to `streamlit_app.py`.\n\n"
            "On GitHub: open your config file, click the ✏️ edit pencil, and rename it "
            "to `config/yourcountry.json` (typing `config/` before the name creates the "
            "folder). Then commit — the app will redeploy automatically."
        )
        st.stop()

    country_keys = list(configs.keys())
    if len(country_keys) == 1:
        selected_country = country_keys[0]
    else:
        try:
            default_key = st.query_params.get("country", country_keys[0])
        except AttributeError:
            default_key = st.experimental_get_query_params().get("country", [country_keys[0]])[0]
        if default_key not in configs:
            default_key = country_keys[0]
        selected_country = st.selectbox(
            t("country"),
            options=country_keys,
            index=country_keys.index(default_key),
            format_func=lambda k: country_label(configs[k]),
            label_visibility="collapsed",
        )
    cfg = configs[selected_country]

    # ---- RTL support ----
    dir_attr = "rtl" if st.session_state.lang in ["ar", "ku"] else "ltr"

    # ---- 🟡 DIGITAL BERRY BANNER - Full Width ----
    lang_options = {"English": "en", "العربية": "ar", "کوردی": "ku"}
    current_label = next(k for k, v in lang_options.items() if v == st.session_state.lang)
    
    # Create the full-width banner with language selector
    st.markdown(
        f"""
        <div class="banner">
            <div class="banner-content">
                <div class="banner-title">
                    <h1>🌊 {t('dashboard_header')}</h1>
                    <div class="subtitle">{cfg.get('name_en', '')} | {datetime.now().strftime('%Y')}</div>
                    <div class="welcome">✨ {t('welcome_subtitle')}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Language selector in banner (using columns)
    lang_col1, lang_col2 = st.columns([5, 1])
    with lang_col2:
        lang_options = {"English": "en", "العربية": "ar", "کوردی": "ku"}
        current_label = next(k for k, v in lang_options.items() if v == st.session_state.lang)
        selected_label = st.selectbox(
            "🌐",
            options=list(lang_options.keys()),
            index=list(lang_options.keys()).index(current_label),
            key="lang_selector_banner",
            label_visibility="collapsed",
        )
        if lang_options[selected_label] != st.session_state.lang:
            st.session_state.lang = lang_options[selected_label]
            st.rerun()
    
    # ---- Navigation Buttons (5 columns with date selector) ----
    st.markdown("---")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1.2, 1.2, 1.2, 1.5, 1.5])
    
    with nav_col1:
        if st.button(t("nav_abstraction_mm"), key="nav_mm", use_container_width=True):
            st.session_state.selected_parameter = "abstraction_mm"
            st.session_state.map_generated = False
            st.rerun()
    
    with nav_col2:
        if st.button(t("nav_abstraction_m3"), key="nav_m3", use_container_width=True):
            st.session_state.selected_parameter = "abstraction_m3"
            st.session_state.map_generated = False
            st.rerun()
    
    with nav_col3:
        if st.button(t("nav_recharge"), key="nav_recharge", use_container_width=True):
            st.session_state.selected_parameter = "recharge"
            st.session_state.map_generated = False
            st.rerun()
    
    # Date selector
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
                    
                    selected_date_str = st.selectbox(
                        t("select_date"),
                        options=date_options,
                        index=len(date_options) - 1,
                        key="top_date_selector",
                        label_visibility="collapsed",
                    )
                    st.session_state.selected_date_str = selected_date_str
        except Exception as e:
            st.warning("Could not load dates")
    
    with nav_col5:
        if st.button("🚀 " + t("generate_analysis"), key="top_generate", use_container_width=True, type="primary"):
            st.session_state.map_generated = True
            st.session_state.current_parameter = st.session_state.selected_parameter
            st.session_state.current_date = st.session_state.selected_date_str
            st.rerun()
    
    st.markdown("---")

    # ---- Earth Engine ----
    try:
        if not initialize_ee():
            st.error(t("ee_init_failed"))
            return
    except Exception as e:
        st.error(f"{t('ee_init_critical')}: {str(e)}")
        st.error(traceback.format_exc())
        return

    # ---- Session state ----
    defaults = {
        "last_clicked": None,
        "map_generated": False,
        "current_parameter": "abstraction_mm",
        "current_date": None,
        "time_series_data": None,
        "current_country": selected_country,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Reset map when the country changes
    if st.session_state.current_country != selected_country:
        st.session_state.current_country = selected_country
        st.session_state.map_generated = False
        st.session_state.last_clicked = None
        st.session_state.time_series_data = None

    # ---- If no date is selected, set to latest available ----
    if st.session_state.selected_date_str is None:
        try:
            asset_path = cfg["asset_path"]
            assets = get_ee_assets(asset_path)
            if assets:
                asset_dates = [d for d in (parse_asset_date(a) for a in assets) if d is not None]
                if asset_dates:
                    latest_date = max(asset_dates)
                    st.session_state.selected_date_str = latest_date.strftime("%Y-%m")
        except:
            pass

    # ---- Main content ----
    with st.container():
        if not st.session_state.map_generated:
            st.markdown(f"### 📊 {t('statistics')}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(t('minimum'), "—")
            with col2:
                st.metric(t('maximum'), "—")
            with col3:
                st.metric(t('mean'), "—")
            st.caption(t('click_map'))
        else:
            try:
                # TWO-COLUMN LAYOUT: Map on left, Statistics on right
                map_col, stats_col = st.columns([2, 1])

                # ---- LEFT COLUMN: MAP ----
                with map_col:
                    st.markdown(f"### 🗺️ {t('interactive_map')}")

                    selected_date = datetime.strptime(st.session_state.current_date, "%Y-%m")
                    selected_year_month = selected_date.strftime("%Y_%m")

                    selected_asset = next(
                        (
                            a
                            for a in assets
                            if st.session_state.current_parameter in a and selected_year_month in a
                        ),
                        None,
                    )
                    if not selected_asset:
                        st.error(t("no_data_month"))
                        return

                    center_lat = float(cfg["center_lat"])
                    center_lon = float(cfg["center_lon"])
                    zoom = int(cfg["zoom"])
                    
                    m = create_base_map(center_lat, center_lon, zoom)
                    ee_image = ee.Image(selected_asset)
                    
                    opacity = st.session_state.get("opacity", 0.7)
                    vis_params = get_vis_params(st.session_state.current_parameter, selected_asset)
                    vis_params["opacity"] = opacity

                    add_ee_layer(
                        m,
                        ee_image,
                        vis_params,
                        f"{t(st.session_state.current_parameter)} {t('layer')}",
                    )
                    add_colormap(m, vis_params, st.session_state.current_parameter)
                    folium.LayerControl().add_to(m)

                    map_data = st_folium(m, width=None, height=500, returned_objects=["last_clicked"])

                    if map_data["last_clicked"] and map_data["last_clicked"] != st.session_state.last_clicked:
                        st.session_state.last_clicked = map_data["last_clicked"]
                        st.session_state.time_series_data = get_time_series_data(
                            point=[map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]],
                            parameter=st.session_state.current_parameter,
                            assets=tuple(assets),
                        )

                # ---- RIGHT COLUMN: STATISTICS (HORIZONTAL) ----
                with stats_col:
                    st.markdown(f"### 📊 {t('statistics')}")
                    try:
                        stats = ee_image.reduceRegion(
                            reducer=ee.Reducer.mean().combine(ee.Reducer.minMax(), None, True),
                            geometry=ee_image.geometry(),
                            scale=1000,
                            maxPixels=1e9,
                        ).getInfo()
                        prefix = next(
                            (k[: -len("_mean")] for k in stats if k.endswith("_mean")), "b1"
                        )
                        
                        min_val = stats.get(f"{prefix}_min")
                        max_val = stats.get(f"{prefix}_max")
                        mean_val = stats.get(f"{prefix}_mean")
                        
                        # HORIZONTAL STATISTICS: Display in 3 columns
                        stat_cols = st.columns(3)
                        with stat_cols[0]:
                            st.metric(
                                t('minimum'),
                                f"{min_val:.2f}" if isinstance(min_val, (int, float)) else "N/A",
                            )
                        with stat_cols[1]:
                            st.metric(
                                t('maximum'),
                                f"{max_val:.2f}" if isinstance(max_val, (int, float)) else "N/A",
                            )
                        with stat_cols[2]:
                            st.metric(
                                t('mean'),
                                f"{mean_val:.2f}" if isinstance(mean_val, (int, float)) else "N/A",
                            )
                    except Exception as e:
                        st.error(f"{t('error_statistics')}: {str(e)}")
                    
                    st.markdown("---")
                    st.caption("📌 " + t('click_map'))

                # ---- FULL WIDTH: Time Series & Regional Summary ----
                st.markdown("---")
                st.markdown(f"### 📈 {t('time_series_analysis')}")
                if st.session_state.time_series_data:
                    clicked_lat = st.session_state.last_clicked["lat"]
                    clicked_lng = st.session_state.last_clicked["lng"]

                    fig = create_time_series_plot(
                        st.session_state.time_series_data,
                        st.session_state.current_parameter,
                        clicked_lat,
                        clicked_lng,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    st.download_button(
                        t("download_csv"),
                        data=to_csv_bytes(st.session_state.time_series_data),
                        file_name=f"{cfg['key']}_{st.session_state.current_parameter}"
                        f"_timeseries_{clicked_lat:.4f}_{clicked_lng:.4f}.csv",
                        mime="text/csv",
                    )
                    with st.expander(t("raw_data")):
                        st.dataframe(pd.DataFrame(st.session_state.time_series_data))
                else:
                    st.info(t("click_map"))

                # ---- Regional summary ----
                st.markdown(f"### 📊 {t('regional_summary')}")
                if st.button(t("compute_summary"), help=t("summary_help")):
                    with st.spinner(t("computing")):
                        summary = get_regional_summary(
                            st.session_state.current_parameter,
                            tuple(assets),
                            int(cfg.get("native_scale_m", 20)),
                        )
                    if summary:
                        df = pd.DataFrame(summary)
                        months_lbl = [d.strftime("%Y-%m") for d in df["date"]]
                        fig = go.Figure(
                            go.Bar(x=months_lbl, y=df["mean"], marker_color="#B429F9")
                        )
                        fig.update_layout(
                            title=t(
                                "summary_title",
                                parameter=t(st.session_state.current_parameter),
                            ),
                            xaxis=dict(tickangle=45),
                            template="plotly_white",
                            height=350,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.download_button(
                            t("download_csv"),
                            data=to_csv_bytes(summary, value_col="mean"),
                            file_name=f"{cfg['key']}_{st.session_state.current_parameter}"
                            f"_regional_summary.csv",
                            mime="text/csv",
                            key="dl_summary",
                        )

            except Exception as e:
                st.error(f"{t('error_map')}: {str(e)}")
                st.error(traceback.format_exc())

    # ---- Footer ----
    st.markdown("---")
    with st.expander(t("about_tool")):
        st.markdown(t("about_text"))


if __name__ == "__main__":
    main()
