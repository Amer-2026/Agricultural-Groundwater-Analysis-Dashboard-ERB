# 🚀 Deploy Your Dashboard — everything in this folder
# انشر لوحة معلوماتك — كل شيء في هذا المجلد

This folder contains **every file your dashboard needs**. After finishing Notebooks 1–4 (your model results are in your Earth Engine project), follow these steps. **You do not need a terminal, VS Code, Python, or anything installed** — only a web browser.

يحتوي هذا المجلد على **كل الملفات التي تحتاجها لوحتك**. بعد إنهاء الدفاتر ١–٤ (نتائج نموذجك في مشروعك على محرك الأرض)، اتبع هذه الخطوات. **لا تحتاج إلى طرفية أو VS Code أو تثبيت أي برنامج** — متصفح الويب فقط.

## What's in the folder | محتويات المجلد

| File | Role | Do you edit it? |
|---|---|---|
| `streamlit_app.py` | The dashboard program | ❌ Never |
| `requirements.txt` | Packages Streamlit Cloud installs | ❌ Never |
| `config/yourcountry.json` | **Your country's settings** | ✅ YES — this is the only file you edit |
| `.gitignore` | Prevents accidental secret uploads | ❌ Never |
| `.streamlit/secrets.toml.example` | Template for your credentials | ✅ Fill a copy — but it goes into Streamlit's Secrets screen, **NOT** into GitHub |

## Step 1 — Edit your config file | عدّل ملف الإعدادات

Open `config/yourcountry.json` in any text editor (even Notepad) and replace the TODO values:

- `key` — short name, e.g. `"iraq"`
- `name_en` / `name_ar` — the title shown in the app | العنوان الظاهر في التطبيق
- `flag` — your flag emoji 🇯🇴 🇮🇶 🇵🇸
- `asset_path` — **exactly** the `ASSET_FOLDER` you used in Notebook 3, e.g. `projects/gw-tool-iraq-mowr/assets/GW_Analysis_Erbil`
- `center_lat` / `center_lon` / `zoom` — where the map opens
- `wapor_region_code` — e.g. `"ERB"`

You may rename the file (e.g. `iraq.json`) — the name doesn't matter, the content does.

### Worked example | مثال معبأ

A partner whose Earth Engine project is `gw-tool-iraq-mowr` and who ran Notebook 3 with `ASSET_FOLDER_NAME = "GW_Analysis_Shamamik"` and `REGION = "ERB"`:

```json
{
  "key": "iraq",
  "name_en": "Iraq — Shamamik (Erbil)",
  "name_ar": "العراق — شمامك (أربيل)",
  "flag": "🇮🇶",
  "asset_path": "projects/gw-tool-iraq-mowr/assets/GW_Analysis_Shamamik",
  "center_lat": 36.1,
  "center_lon": 43.7,
  "zoom": 10,
  "wapor_region_code": "ERB",
  "native_scale_m": 20
}
```

| Field | Where the value comes from |
|---|---|
| `key` | you invent it — short, lowercase, no spaces |
| `name_en` / `name_ar` | you invent them — the dashboard title in each language |
| `flag` | your flag emoji (copy from emojipedia.org) |
| `asset_path` | ⚠️ copy **exactly** the line Notebook 3 prints: *"Outputs will go to: projects/…/assets/…"* |
| `center_lat` / `center_lon` | Google Maps → right-click the centre of your area → copy the two numbers |
| `zoom` | 9 ≈ province, 11 ≈ district, 13 ≈ village — start with 10 |
| `wapor_region_code` | the REGION code you used in Notebooks 2–3 |
| `native_scale_m` | leave as 20 (WaPOR Level-3 resolution) |

**The two mistakes that cause 95% of problems | الخطآن الأكثر شيوعاً:**

1. **Wrong `asset_path`** (typo, wrong project ID, capital/small letters) → app says *"No assets found"*. Compare letter-by-letter with Notebook 3's printed output. | خطأ في مسار الأصول → قارن حرفاً بحرف مع ما طبعه الدفتر ٣.
2. **Broken JSON** — a deleted comma, quote or brace → app crashes at start. Only change text **between the quotes** and the numbers; never touch punctuation. | لا تحذف الفواصل أو علامات الاقتباس — غيّر النص بين علامات الاقتباس فقط.

## Step 2 — Put the folder on GitHub (browser only) | ارفع المجلد إلى GitHub

1. On github.com click **+** (top right) → **New repository** → name it e.g. `groundwater-dashboard` → **Public** → Create repository.
2. On the new empty repo page click **uploading an existing file**.
3. Drag **the entire contents of this folder** (not the folder itself — its contents, including the `config` folder) into the upload area.
4. Click **Commit changes**.

> ⚠️ Do **not** upload any filled-in `secrets.toml`. The `.example` file is safe (it contains no real values).

أنشئ مستودعاً جديداً عاماً على GitHub، ثم اسحب **محتويات هذا المجلد كاملة** إلى صفحة الرفع واضغط Commit. **لا ترفع أبداً** ملف secrets.toml معبأً بقيم حقيقية.

## Step 3 — Deploy on Streamlit Cloud | انشر على سحابة Streamlit

1. Go to **share.streamlit.io** (signed in with the same GitHub account).
2. **Create app** → *Deploy a public app from GitHub*.
3. Repository: `your-username/groundwater-dashboard` · Branch: `main` · Main file: `streamlit_app.py`.
4. Choose your URL, e.g. `gw-iraq.streamlit.app`.
5. **Advanced settings → Secrets**: paste your **filled-in** `[gee_credentials]` block (use `.streamlit/secrets.toml.example` as the template; values come from your service-account JSON key — see docs/01 in the training repository).
6. **Deploy** → wait 1–2 minutes → your dashboard is live. 🎉

Because this folder has only one config file, the app opens directly as **your country's dashboard** — no country selector.

بما أن المجلد يحتوي على ملف إعدادات واحد فقط، يفتح التطبيق مباشرة كلوحة **بلدك** — دون مُحدد دول.

## Updating later | التحديث لاحقاً

- **New data**: re-run Notebook 3 (it only computes new months) → refresh the app. No redeploy needed.
- **Change a setting**: edit the config file on GitHub (pencil icon) → Commit → the app redeploys itself in ~1 minute.

## Optional — run on your own computer (advanced, not required)
## اختياري — التشغيل على حاسوبك (متقدم، غير مطلوب)

Only if you *want* to test locally (requires installing Python from python.org):

```
cd path/to/this/folder
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then fill `.streamlit/secrets.toml` (copy the `.example`, remove the `.example` ending) so the local app can authenticate. The app opens at http://localhost:8501.

**This step is NOT part of deployment** — Streamlit Cloud builds everything from GitHub by itself.

**هذه الخطوة ليست جزءاً من النشر** — سحابة Streamlit تبني كل شيء من GitHub بنفسها.
