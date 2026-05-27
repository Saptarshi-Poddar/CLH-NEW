import base64
import os
import streamlit as st
import pandas as pd
import joblib
from data_processing import prepare_features
from prediction import get_top_flights
from routing import get_feasible_flights
from pod import create_pod_lookup
import io
import hashlib
from sqlalchemy import text
from datetime import datetime
from sqlalchemy import create_engine
import plotly.express as px
import pytz

DATABASE_URL = "postgresql://postgres.zlqrqkkbtiwibfmrlbnx:Manju22690221@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
try:
    
    DATABASE_URL = st.secrets.get("DATABASE_URL",DATABASE_URL)
    
except:
    pass
DATABASE_URL = os.getenv("DATABASE_URL",DATABASE_URL)
    
    
engine = create_engine(DATABASE_URL)
#engine = engine.engineect()
# -------------------------------
# LOAD MODEL FILES
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = joblib.load(os.path.join(BASE_DIR,"flight_model.pkl"))
encoder = joblib.load(os.path.join(BASE_DIR,"flight_encoder.pkl")) 
feature_columns = joblib.load(os.path.join(BASE_DIR,"feature_columns.pkl"))

# -------------------------------
# STREAMLIT PAGE CONFIG
# -------------------------------

st.set_page_config(
    page_title="Smart Flight Assignment System",
    layout="wide",
    initial_sidebar_state="expanded"
)
for key in ["shipment_file", "schedule_file", "routes_file", "capacity_file", "pod_file"]:
    if key not in st.session_state:
        st.session_state[key] = None
        
st.markdown("""
<div class="header-card">
    <h1 style="color:#FF6600;">✈ Intelligent Flight Allocation Engine</h1>
    <p>AI-driven system for optimizing shipment routing, capacity utilization, and delivery commitments across global air networks.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* ===== STATUS BAR ===== */
.status-bar {
    display: flex;
    gap: 20px;
    margin-bottom: 20px;
    font-size: 13px;
    color: #94a3b8;
}

.status-bar span {
    background: rgba(30,41,59,0.6);
    padding: 6px 12px;
    border-radius: 8px;
}

/* ===== FIX TOP RIGHT ICON VISIBILITY ===== */
header svg {
    fill: white !important;
    color: white !important;
}

header button {
    color: white !important;
}

/* Hover */
header button:hover {
    background-color: rgba(255,255,255,0.1) !important;
}

/* ===== MAIN BACKGROUND ===== */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, #46148C, #0B041A);
}


/* ===== STRONG WHITE TITLE ===== */

h1 {
    color: #ffffff !important;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-shadow: 0 2px 8px rgba(255,255,255,0.15);
}

/* ===== FORCE GLASS EFFECT ===== */
.card {
    background: rgba(30, 41, 59, 0.55) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    padding: 22px;
    margin-bottom: 28px;
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.6);
}

/* ===== FADE IN ===== */
[data-testid="stAppViewContainer"] {
    animation: fadeIn 0.6s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ===== BACKGROUND GLOW ===== */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: -200px;
    left: -200px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(37,99,235,0.25), transparent 70%);
    z-index: 0;
}

/* ===== PREMIUM BUTTON ===== */
.stDownloadButton button {
    background: linear-gradient(135deg, #FF6600, #FF8C42);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: 600;
    box-shadow: 0 0 20px rgba(168,85,247,0.5);
}

.stDownloadButton button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 35px rgba(168,85,247,0.9);
}

/* ===== UPLOADER UPGRADE ===== */
[data-testid="stFileUploader"] {
    border-radius: 12px;
    border: 1px dashed #475569;
    padding: 10px;
    background: rgba(15, 23, 42, 0.6);
}

/* ===== TITLES ===== */
h1 {
    font-size: 32px;
}

h2 {
    font-size: 22px;
}

h3 {
    font-size: 18px;
}

/* ===== KPI CARDS ===== */
.metric-card {
    background: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.8));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 22px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
    transition: 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 25px rgba(0,0,0,0.6);
}

/* Label below */
.metric-label {
    font-size: 13px;
    color: #94a3b8 !important;
}

/* ===== KPI GLOW EFFECT ===== */
.metric-value {
    font-size: 42px;
    font-weight: 800;
    color: #FF6600;
    text-shadow: 0 0 20px rgba(255,102,0,0.8);
    letter-spacing: 1px;
    text-shadow: 0 0 20px rgba(168,85,247,0.8);
}

/* ===== PREMIUM GLOW HEADER ===== */

.header-card {
    background: linear-gradient(135deg, #1e1b4b, #0f172a);
    padding: 28px;
    border-radius: 16px;
    margin-bottom: 25px;
    border: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(10px);
}

/* REMOVE glow */
.header-card::before,
.header-card::after {
    display: none !important;
}

/* Title */
.header-card h1 {
    font-size: 30px;
    font-weight: 700;
    color: #ffffff;
}

/* Subtitle */
.header-card p {
    color: #cbd5e1;
    font-size: 14px;
}

/* ===== DATA TABLE ===== */

[data-testid="stDataFrame"] {
    background: rgba(15,23,42,0.9);
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.05);
}

/* Header */
[data-testid="stDataFrame"] thead tr th {
    background: #1e293b !important;
    font-weight: 600;
}

/* Row hover */
[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(255,102,0,0.15) !important;
}

[data-testid="stDataFrame"] thead {
    position: sticky;
    top: 0;
    z-index: 2;
}

[data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background: rgba(255,255,255,0.02);
}

/* ===== Keep header but style it =====*/
header {
    background: transparent !important;
}

/* Optional: hide only logo */
header [data-testid="stToolbar"] {
    right: 10px;
}

/* ===== FILE UPLOADER FULL FIX ===== */
[data-testid="stFileUploader"] {
    background: #1f2937 !important;
    border: 1px solid #475569;
    border-radius: 12px;
    padding: 12px;
}

/* ===== ONLY DRAG TEXT BLACK ===== */

[data-testid="stFileUploader"] {
    background: #1f2937 !important;
}

/* Browse button */
[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #FF6600, #FF8C42);
    color: white !important;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 6px 12px;
}

/* Hover */
[data-testid="stFileUploader"] button:hover {
    background: linear-gradient(135deg, #1d4ed8, #0891b2);
}

/* ===== HEADINGS FIX ===== */
h2, h3 {
    color: #ffffff !important;
    font-weight: 700;
}

/* ===== FIX SELECTED VALUE (MAIN ISSUE) ===== */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    color:  #e2e8f0 !important;
    font-weight: 600;
}

/* Also force inner text */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {
    color:  #e2e8f0 !important;
}

/* ===== FINAL FORCE FIX (WORKS IN ALL STREAMLIT VERSIONS) ===== */

/* Target the white drop area using BaseWeb structure */
[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] * {
    color: #000000 !important;
}

/* Strong override */
[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] span {
    color: #000000 !important;
    font-weight: 600;
}

[data-testid="stFileUploader"] div[data-baseweb="file-uploader"] small {
    color: #000000 !important;
    font-size: 12px;
}

/* ===== FORCE FIX LABEL TEXT ===== */
[data-testid="stFileUploader"] > label,
[data-testid="stFileUploader"] p {
    color: #ffffff !important;
    font-weight: 600;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: #0B041A;
    border-right: none;
    border-right: 1px solid rgba(139,92,246,0.2);
    box-shadow: 6px 0 30px rgba(139,92,246,0.15);
}

/* SIDEBAR ITEM BASE */
/* SIDEBAR ITEMS */
[data-testid="stSidebar"] .stRadio label {
    padding: 10px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: rgba(255,255,255,0.05);
    color: white !important;
    transition: 0.2s ease;
}

/* ACTIVE (SAFE FIX) */
[data-testid="stSidebar"] input[type="radio"]:checked + div {
    background: linear-gradient(90deg, rgba(255,102,0,0.3), rgba(255,102,0,0.05));
    border-left: 4px solid #FF6600;
    padding-left: 8px;
    border-radius: 8px;
}

/* Better hover */
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,102,0,0.15);
}

/* ===== ULTRA FORCE SIDEBAR TEXT FIX ===== */

/* Target EVERYTHING inside radio label */
[data-testid="stSidebar"] .stRadio label * {
    color: #ffffff !important;
    opacity: 1 !important;
    transition: all 0.25s ease;
    cursor: pointer;
}

/* Specifically fix text node */
[data-testid="stSidebar"] .stRadio label div {
    color: #ffffff !important;
    opacity: 1 !important;
}

/* Fix BaseWeb radio wrapper */
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] {
    opacity: 1 !important;
}

/* RESET the big container effect */
[data-testid="stSidebar"] .stRadio > div {
    background: transparent !important;
    padding: 0 !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] .stRadio label {
    display: block;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    transition: all 0.2s ease;
    cursor: pointer;
}
/* ACTIVE SIDEBAR ITEM - STRONG ORANGE */

[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: linear-gradient(90deg, rgba(255,102,0,0.25), rgba(255,102,0,0.05)) !important;
    border-left: 5px solid #FF6600 !important;
    color: white !important;
    font-weight: 600;
    padding-left: 10px;
    border-radius: 10px;
}

/* HOVER EFFECT */
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,102,0,0.12);
    transition: 0.3s ease;
}

/* RADIO BUTTON DOT */
[data-testid="stSidebar"] input[type="radio"]:checked + div::before {
    background-color: #FF6600 !important;
    border: 2px solid #FF6600 !important;
}
/* ===== FIX UI LAYERING ===== */
.block-container {
    position: relative;
    z-index: 10;
}

.card {
    position: relative;
    z-index: 10;
}

.metric-card {
    position: relative;
    z-index: 10;
}

/* Fix all labels */
label {
    color: white !important;
    font-weight: 600;
}

/* Fix selectbox text */
.stSelectbox label {
    color: white !important;
}

/* Fix multiselect */
.stMultiSelect label {
    color: white !important;
}


[data-testid="stSidebar"] > div:first-child {
    padding-top: 0px !important;
}

/* REMOVE TOP HEADER GAP */
header {
    height: 0px !important;
    min-height: 0px !important;
}

[data-testid="stHeader"] {
    height: 0px !important;
}

/* ===== WHITE DATE INPUT ===== */
[data-testid="stDateInput"] input {
    background: #ffffff !important;
    color: #000000 !important;
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
    font-weight: 500;
}

/* focus */
[data-testid="stDateInput"] input:focus {
    border: 1px solid #FF6600 !important;
    box-shadow: 0 0 6px rgba(255,102,0,0.5);
}

/* CALENDAR POPUP */
.react-datepicker {
    background-color: #1e293b !important;
    border-radius: 12px !important;
    color: white !important;
}

.react-datepicker__day--selected {
    background-color: #FF6600 !important;
}
/* ===== FIX SIDEBAR LABEL VISIBILITY ===== */

/* Navigation title */
[data-testid="stSidebar"] div:has(> div:contains("Navigation")) {
    color: #ffffff !important;
}

/* Customs Clearance label */
[data-testid="stSidebar"] label {
    color: #ffffff !important;
    opacity: 1 !important;
    font-weight: 600;
}

/* ===== RUN BUTTON PREMIUM ===== */
div.stButton > button {
    background: linear-gradient(135deg, #FF6600, #FF8C42);
    color: white;
    border-radius: 12px;
    border: none;
    font-weight: 600;
    padding: 12px;
    transition: all 0.2s ease;
}

/* hover */
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(255,102,0,0.4);
}

/* click (POP EFFECT) */
div.stButton > button:active {
    transform: scale(0.96);
    box-shadow: 0 3px 10px rgba(255,102,0,0.3);
}

/* ===== EXPANDER (Shipment Preview) ===== */
details {
    background: rgba(30, 41, 59, 0.8) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 12px;
}

/* Header (the clickable bar) */
summary {
    color: white !important;
    padding: 10px 14px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
}

/* Remove default arrow ugliness */
summary::-webkit-details-marker {
    display: none;
}
/* ===== RUN MODEL BUTTON ===== */
div.stButton > button {
    background: linear-gradient(135deg, #FF6600, #FF8C42);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 8px 16px;
    font-size: 14px;
    transition: all 0.2s ease;
}

/* hover */
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(255,102,0,0.4);
}

/* click pop effect */
div.stButton > button:active {
    transform: scale(0.95);
    box-shadow: 0 3px 8px rgba(255,102,0,0.3);
}
/* ===== FORCE ALL BUTTONS ORANGE (FINAL OVERRIDE) ===== */
div.stButton > button {
    
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
}

/* Hover */
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(255,102,0,0.5) !important;
}

/* Click animation */
div.stButton > button:active {
    transform: scale(0.95);
}

/* REMOVE DISABLED GREY LOOK */
div.stButton > button:disabled {
    background: linear-gradient(135deg, #FF6600, #FF8C42) !important;
    color: white !important;
    opacity: 1 !important;
    cursor: pointer !important;
}

/* ===== FIX SPINNER VISIBILITY ===== */
[data-testid="stSpinner"] {
    color: #FFFFFF !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    z-index: 9999 !important;
}

/* Spinner circle */
[data-testid="stSpinner"] svg {
    stroke: #FF6600 !important;
    width: 40px !important;
    height: 40px !important;
}

/* Spinner container */
[data-testid="stSpinner"] > div {
    background: rgba(0,0,0,0.6) !important;
    padding: 12px 20px;
    border-radius: 10px;
}
/* Force spinner above everything */
div[data-testid="stSpinner"] {
    position: fixed !important;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
/* ===== DEFAULT CLOSED ===== */
details:not([open]) > summary {
    background: rgba(30,41,59,0.85) !important;
    color: #e2e8f0 !important;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 500;
    transition: 0.2s ease;
}

/* ===== HOVER ===== */
details:not([open]) > summary:hover {
    background: rgba(51,65,85,0.9) !important;
    cursor: pointer;
}

/* ===== OPEN (ONLY ACTIVE ONE) ===== */
details[open] > summary {
    background: linear-gradient(135deg, #FF6600, #FF8C42) !important;
    color: #000000 !important;
    font-weight: 600;
}

/* ===== TEXT INSIDE OPEN ===== */
details[open] > summary * {
    color: #000000 !important;
}

/* ===== ARROW ICON ===== */
details > summary svg {
    fill: #e2e8f0 !important;
}

details[open] > summary svg {
    fill: #000000 !important;
}

/* ===== SPACING ===== */
details {
    margin-bottom: 10px;
}
/* CLOSED STATE */
details:not([open]) > summary {
    background: rgba(30,41,59,0.85) !important;
    color: #e2e8f0 !important;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 500;
    transition: 0.2s ease;
}

/* HOVER */
details:not([open]) > summary:hover {
    background: rgba(51,65,85,0.9) !important;
}

/* OPEN STATE (ONLY ACTIVE ONE) */
details[open] > summary {
    background: linear-gradient(135deg, #FF6600, #FF8C42) !important;
    color: #000000 !important;
    font-weight: 600;
}

/* TEXT FIX */
details[open] > summary * {
    color: #000000 !important;
}

/* ICON */
details > summary svg {
    fill: #e2e8f0 !important;
}

details[open] > summary svg {
    fill: #000000 !important;
}

/* =======================================================
   FINAL SIDEBAR TEXT + SELECTBOX + DATE FIX
======================================================= */

/* ===== SIDEBAR LABELS ===== */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] p {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 17px !important;
    opacity: 1 !important;
}

/* ===== PLANNING DATE LABEL ===== */
[data-testid="stSidebar"] div[data-testid="stDateInput"] label {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 17px !important;
    opacity: 1 !important;
}

/* ===== DATE INPUT BOX ===== */
[data-testid="stDateInput"] input {
    background: #FFFFFF !important;
    color: #000000 !important;
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;

    font-weight: 800 !important;
    font-size: 17px !important;

    opacity: 1 !important;
}

/* ===== SELECTBOX MAIN BOX ===== */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #d1d5db !important;
}

/* ===== SELECTED VALUE (7 / 14) ===== */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {
    color: #000000 !important;
    font-weight: 800 !important;
    font-size: 17px !important;
    opacity: 1 !important;
}

/* ===== DROPDOWN MENU ===== */
div[data-baseweb="popover"] {
    background: #FFFFFF !important;
    border-radius: 10px !important;
}

/* ===== DROPDOWN OPTIONS ===== */
div[data-baseweb="popover"] li {
    color: #000000 !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    opacity: 1 !important;
}

/* ===== DROPDOWN HOVER ===== */
div[data-baseweb="popover"] li:hover {
    background: #f3f4f6 !important;
    color: #000000 !important;
}

/* ===== REMOVE FADED LOOK ===== */
[data-testid="stSidebar"] * {
    opacity: 1 !important;
}

/* ===== NAVIGATION TITLE ===== */
.sidebar-nav-title {
    color: white !important;
    font-weight: 900 !important;
}

/* =======================================================
   FINAL WORKING SELECTBOX FIX
======================================================= */

/* main selectbox container */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background-color: #ffffff !important;
    border-radius: 12px !important;
    border: 1px solid #d1d5db !important;

    color: #000000 !important;
    font-weight: 800 !important;
}

/* actual selected text */
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    color: #000000 !important;
    background-color: #ffffff !important;
    font-weight: 800 !important;
}

/* input field */
[data-testid="stSidebar"] .stSelectbox input {
    color: #000000 !important;
    background-color: #ffffff !important;

    font-weight: 800 !important;
    font-size: 17px !important;

    -webkit-text-fill-color: #000000 !important;
    caret-color: #000000 !important;
}

/* selected single value */
[data-testid="stSidebar"] .stSelectbox span {
    color: #000000 !important;
    font-weight: 800 !important;
}

/* dropdown options */
div[data-baseweb="popover"] li {
    color: #000000 !important;
    background-color: #ffffff !important;
    font-weight: 700 !important;
}

/* dropdown arrow */
[data-testid="stSidebar"] .stSelectbox svg {
    fill: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

#----------------------------------------
#FILE UPLOAD INSTRUCTIONS
#----------------------------------------

st.sidebar.markdown(f"""
<div style="
    background:white;
    padding:18px 0px;
    margin:-78px -29px 19px -29px;
">
    <img src="data:image/jpeg;base64,{base64.b64encode(open('FedEx Logo.jpeg','rb').read()).decode()}"
        style="width:100%; height:65px; object-fit:contain; display:block;">
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<div style="
    font-size:22px;
    font-weight:800;
    color:white;
    margin-bottom:4px;
">
✈ Navigation
</div>

<div style="
    height:4px;
    width:55px;
    background:#FF6600;
    border-radius:10px;
    margin-bottom:18px;
"></div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "",
    ["✈ Main Assignment", "📊 Debug Dashboard","📈 Analytics Dashboard"]
)

if "Main Assignment" in page:
    page = "Main Assignment"
elif "Debug Dashboard" in page:
    page = "Debug Dashboard"
else:
    page = "Analytics Dashboard"
    
st.sidebar.markdown("""
<div style="
    color:white;
    font-size:17px;
    font-weight:800;
    margin-bottom:6px;
">
📅 Planning Date
</div>
""", unsafe_allow_html=True)
release_date = st.sidebar.date_input("")

st.sidebar.markdown("""
<div style="
    color:white;
    font-size:17px;
    font-weight:800;
    margin-top:12px;
    margin-bottom:6px;
">
Planning Horizon
</div>
""", unsafe_allow_html=True)

planning_horizon = st.sidebar.selectbox(
    "",
    [7,14,21],
    index=1
)

if release_date:
    release_date = pd.to_datetime(release_date)
    ready_date = release_date 
    ready_day_num = ready_date.weekday() + 1
else:
    ready_day_num = pd.Timestamp.today().weekday() + 1   
    
# -------------------------------
# FILE UPLOAD SECTION
# -------------------------------
st.markdown('<div class="card">', unsafe_allow_html = True)
st.markdown("### 📂 Upload Required Files")

# your uploaders here

shipment_file = st.file_uploader(
    "Upload Shipment Dataset",
    type=["csv","xlsx","xls"]
)
if shipment_file:
    st.session_state["shipment_file"] = shipment_file
    st.success("Shipment file uploaded")

schedule_file = st.file_uploader(
    "Upload Flight Schedule Dataset",
    type=["csv","xlsx","xls"]
)
if schedule_file:
    st.session_state["schedule_file"] = schedule_file
    st.success("Schedule file uploaded")

routes_file = st.file_uploader(
    "Upload Flight Routes Dataset",
    type=["csv","xlsx","xls"]
)
if routes_file:
    st.session_state["routes_file"] = routes_file
    st.success("Flight Routes Dataset file uploaded")
    
capacity_file = st.file_uploader(
    "Upload Flight Capacity Dataset",
    type=["csv","xlsx","xls"]
)
if capacity_file:
    st.session_state["capacity_file"] = capacity_file
    st.success("Capacity file uploaded")

pod_file = st.file_uploader(
    "Upload POD Dataset",
    type=["csv","xlsx","xls"]
)
if pod_file:
    st.session_state["pod_file"] = pod_file
    st.success("POD file uploaded")

st.markdown('</div>', unsafe_allow_html=True)
# Create a Universal File Reader Function

def read_uploaded_file(file):

    file_name = file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(file)

    elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df = pd.read_excel(file)

    else:
        st.error("Unsupported file format")
        return None

    return df

def get_actual_route(flight, origin, destination, routes_df):

    df = routes_df.copy()
    df["Flight_Number"] = df["Flight_Number"].astype(str).str.replace(" ", "").str.strip() #  Ensure flight number is clean for matching

    flight_rows = df[df["Flight_Number"] == flight]  # Filter routes for that flight

    if flight_rows.empty:
        return f"{origin} → {destination}"

    # 1️ Check DIRECT
    direct = flight_rows[
        (flight_rows["Origin"] == origin) &
        (flight_rows["Destination"] == destination)
    ]

    if not direct.empty:
        return f"{origin} → {destination}"

    # 2️ Check HUB
    possible_splits = flight_rows[
        flight_rows["Origin"] == origin
    ]["Destination"].unique()

    for split in possible_splits:

        leg2 = flight_rows[
            (flight_rows["Origin"] == split) &
            (flight_rows["Destination"] == destination)
        ]

        if not leg2.empty:
            return f"{origin} → {split} → {destination}"

    return f"{origin} → {destination}"


# -------------------------------
# PROCESS DATA AFTER UPLOAD
# -------------------------------

def expand_capacity_schedule(capacity_df, schedule_df, ready_date, planning_horizon):

    expanded_rows = []

    day_map = {
        "Monday":1,
        "Tuesday":2,
        "Wednesday":3,
        "Thursday":4,
        "Friday":5,
        "Saturday":6,
        "Sunday":7
    }

    for offset in range(planning_horizon):

        actual_date = ready_date + pd.Timedelta(days=offset)

        weekday_num = actual_date.weekday() + 1

        matching_capacity = capacity_df[
            capacity_df["Day_Num"] == weekday_num
        ]

        for _, row in matching_capacity.iterrows():

            new_row = row.copy()

            new_row["Actual_Date"] = actual_date
            new_row["Date_Key"] = actual_date.strftime("%Y-%m-%d")

            expanded_rows.append(new_row)

    expanded_df = pd.DataFrame(expanded_rows)
    
    expanded_df = expanded_df.reset_index(drop=True)

    return expanded_df


def run_assignment_model(processed,schedule_df, shipment_df,routes_df, capacity_df, pod_lookup, run_id, ready_date):   

  
    # -------------------------------
    # PREDICT + ASSIGN FLIGHTS
    # -------------------------------

    assigned_flights = []
    top3_results = []
    flight_days = []
    operating_dates = []
    routes_output = []
    debug_results = []
    debug_data = []
    assignment_records = []
    capacity_df_copy = capacity_df.copy()  # Create a copy of the capacity dataframe to track changes during assignment
    numerical_cols = [
        "Capacity_KG",
        "Capacity_Volume",
        "Loaded_So_Far",
        "Loaded_Volume",
        "Remaining_Capacity",
        "Load_Percentage"
        ]
    for col in numerical_cols:
        if col in capacity_df_copy.columns:
            capacity_df_copy[col] = pd.to_numeric(capacity_df_copy[col], errors='coerce').fillna(0).astype(float)
    capacity_df_copy["Actual_Date"] = pd.to_datetime(capacity_df_copy["Actual_Date"],errors='coerce')
    
    # ----------------- BIG MODEL --------------
    priority_map = {
        "IP":0,
        "IPF":1,
        "IE":2,
        "IEF":3,
    }
    shipment_df["Service_Priority"] = shipment_df["Service"].apply(lambda x: priority_map.get(x,99)) # Default to 99 for unknown services to push them to the bottom
    
    shipment_df = shipment_df.sort_values(by=["Service_Priority","Destination_Hub","Delivery_Window"], ascending=[True,False,True]).reset_index(drop=True)
    processed = processed.reset_index(drop=True).loc[shipment_df.index]  # Ensure processed features are in the same order as the sorted shipment_df
 
    for i in range(len(processed)):
        
        days_to_commit = shipment_df.iloc[i]["Delivery_Window"]
        
        shipment_weight = float(pd.to_numeric(shipment_df.iloc[i]["Weight"], errors='coerce') or 0)
        shipment_volume = float(pd.to_numeric(shipment_df.iloc[i]["Volume"], errors='coerce') or 0)

        if pd.isna(shipment_volume) or shipment_volume == 0:
            L = shipment_df.iloc[i].get("L",0)
            B = shipment_df.iloc[i].get("B",0)
            H = shipment_df.iloc[i].get("H",0)  
            pieces = shipment_df.iloc[i]["Pieces"] if "Pieces" in shipment_df.columns else 1  # Default to 1 if Pieces column is missing
            if pd.notna(L) and pd.notna(B) and pd.notna(H) and pieces > 0:
                shipment_volume = (L * B * H * pieces) / 6000  # Convert to volumetric weight
            else:
                shipment_volume = 0  # Default to 0 if dimensions are missing or invalid
        shipment_volume = max(float(shipment_volume),0.0)  # Ensure volume is not negative
        
        temp_df = processed.iloc[[i]].copy()
        temp_df["Volume"] = shipment_volume
        features = temp_df          
        
        top3 = get_top_flights(
        model,
        encoder,
        features,   
        is_ip=1 if shipment_df.iloc[i]["Service"] == "IP" else 0,
        days_to_commit=days_to_commit
        )
    
        current_day = ready_date.weekday() + 1

        day_map = {
            "Monday":1,"Tuesday":2,"Wednesday":3,
            "Thursday":4,"Friday":5,"Saturday":6,"Sunday":7
        }
        
        def get_day_gap(flight):

            rows = capacity_df_copy[
                capacity_df_copy["Flight_Number"] == str(flight).replace(" ","").strip()
            ].copy()

            rows = rows[
                rows["Actual_Date"] > pd.Timestamp(ready_date)
            ]

            if rows.empty:
                return 999

            nearest_date = rows["Actual_Date"].min()

            return (
                pd.to_datetime(nearest_date)
                - pd.Timestamp(ready_date)
            ).days

        top3["Day_Gap"] = top3["Flight"].apply(get_day_gap)

        top3 = top3.sort_values(
            ["Day_Gap", "Probability"],
            ascending=[True, False]
        )

        top3["Flight"] = top3["Flight"].astype(str).str.replace(" ", "").str.strip()
        available_flights = capacity_df_copy["Flight_Number"].astype(str).str.strip().unique()
        top3 =top3[top3["Flight"].isin(available_flights)]
        debug_log = []
        debug_log.append(f"Available flights:{list(available_flights)}")
        debug_log.append(f"Top 3 ML predictions after filtering: {top3['Flight'].tolist()}")
        #debug_log.append(
       # f"Top3 ML raw: {top3[['Flight','Probability']].to_dict('records')}")
        
        pickup_day_num = shipment_df.iloc[i]["Pickup Weekday Number"]

        if pd.isna(pickup_day_num):
            continue

        pickup_day_num = int(pickup_day_num)

        if pd.isna(pickup_day_num):
          st.warning(f"Skipping AWB {shipment_df.iloc[i]['AWB']}: missing pickup day number")
          continue
      
        # add _probability %
        top3["Prob_Display"] = top3.apply(lambda x: f"{x['Flight']}({x['Probability']:.1f}%)", axis=1)
        
        if top3.empty:
            debug_log = ["No ML flights available after filtering"]


        service = shipment_df.iloc[i]["Service"]
        destination = shipment_df.iloc[i]["Destination_Hub"]
        origin = shipment_df.iloc[i].get("Origin","BOM")  # Assuming each shipment has a specific origin

        feasible, routing_debug = get_feasible_flights(
            top3,
            shipment_weight,
            shipment_volume,
            capacity_df_copy,
            ready_date,
            service,
            destination,
            routes_df,
            origin,
            schedule_df,
            pod_lookup,
            days_to_commit = days_to_commit
    )
        debug_log.extend(routing_debug)
        
        feasible_names = [str(f[0]).replace(" ", "").strip() for f in feasible]

        debug_log.append(f"Feasible flights after routing: {feasible_names}")
        
        day_num = ready_date.weekday() +1
        flight_day ="Same Day"
        best_flight = "FedEx"
        
        if len(feasible) == 0:
            best_flight = "FedEx"
            flight_day = "Same Day"
            day_num = ready_date.weekday() +1
            actual_date = ready_date

        elif len(feasible) == 1:    
            best_flight, idx, day_num, flight_day, actual_date = feasible[0]

        # Update capacity
            current_loaded = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_So_Far"], errors='coerce') or 0)
            capacity_df_copy.loc[idx, "Loaded_So_Far"] = (current_loaded + shipment_weight)
            
            current_volume = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_Volume"], errors='coerce') or 0)
            shipment_weight = float(pd.to_numeric(shipment_df.iloc[i]["Weight"], errors='coerce') or 0)
            shipment_volume = pd.to_numeric(shipment_df.iloc[i]["Volume"], errors='coerce')
            if pd.isna(shipment_volume):
                shipment_volume = 0.0
                
            shipment_volume = float(shipment_volume)
            current_volume = float(current_volume)
            
            capacity_df_copy.loc[idx,"Loaded_Volume"] = (current_volume + shipment_volume)  # Update volume for the assigned flight
            
            capacity_df_copy.loc[idx,"Remaining_Capacity"] = (capacity_df_copy.loc[idx,"Capacity_KG"] - capacity_df_copy.loc[idx,"Loaded_So_Far"])
            capacity_df_copy.loc[idx,"Load_Percentage"] = (capacity_df_copy.loc[idx,"Loaded_So_Far"] / capacity_df_copy.loc[idx,"Capacity_KG"]) * 100

        else:
            feasible_names = [str(f[0]).replace(" ", "").strip() for f in feasible]

            top3_filtered = top3[top3["Flight"].isin(feasible_names)]
            
            top3_filtered = top3_filtered.copy()  # To avoid SettingWithCopyWarning when adding new columns

            if not top3_filtered.empty:

                def is_direct(flight):
                    match = routes_df[
                        (routes_df["Flight_Number"].astype(str).str.strip() == str(flight).strip()) &
                        (routes_df["Origin"] == origin) &
                        (routes_df["Destination"] == destination) &
                        (routes_df["Route_Type"] == "Direct")
                    ]
                    return not match.empty

                def remaining_capacity(flight):
                    for f, idx, _ , _ , _ in feasible:
                        if f == flight:
                            cap = capacity_df_copy.loc[idx, "Capacity_KG"]
                            used = capacity_df_copy.loc[idx, "Loaded_So_Far"]
                            return cap - used
                    return 0

                top3_filtered["Direct"] = top3_filtered["Flight"].apply(is_direct)
                top3_filtered["Remaining_Capacity"] = top3_filtered["Flight"].apply(remaining_capacity)
                
                debug_log.append(
                    "Evaluation table: " +
                    str(top3_filtered[['Flight','Probability','Direct','Remaining_Capacity']].to_dict('records'))
                )

                #  FINAL DECISION LOGIC
                best_row = top3_filtered.sort_values(
                    ["Direct", "Remaining_Capacity", "Probability"],
                    ascending=[False, False, False]
                ).iloc[0]

                best_flight = best_row["Flight"]
                
                debug_log.append(
                    f"Selected flight: {best_flight} | "
                    f"Reason → Direct: {best_row['Direct']}, "
                    f"Remaining Cap: {best_row['Remaining_Capacity']:.2f}, "
                    f"ML Prob: {best_row['Probability']:.2f}"
                )
                for _, row in top3_filtered.iterrows():
                    if row["Flight"] != best_flight:
                        debug_log.append(
                            f"{row['Flight']} rejected → "
                            f"Direct={row['Direct']}, "
                            f"Cap={row['Remaining_Capacity']:.2f}, "
                            f"Prob={row['Probability']:.2f}"
                        )

        # find matching feasible row
                for f, idx, day_num, flight_day ,actual_date in feasible:
                    if f == best_flight:
                        current_loaded = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_So_Far"], errors='coerce') or 0)
                        capacity_df_copy.loc[idx, "Loaded_So_Far"] = (current_loaded + shipment_weight) # Update capacity for the assigned flight
                        current_volume = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_Volume"], errors='coerce') or 0)
                        shipment_weight = float(pd.to_numeric(shipment_df.iloc[i]["Weight"], errors='coerce') or 0)
                        shipment_volume = pd.to_numeric(shipment_df.iloc[i]["Volume"], errors='coerce')
                        if pd.isna(shipment_volume):
                            shipment_volume = 0.0
                        shipment_volume = float(shipment_volume) # Update volume for the assigned flight
                        
                        capacity_df_copy.loc[idx,"Loaded_Volume"] = (current_volume + shipment_volume)  # Update volume for the assigned flight
                        capacity_df_copy.loc[idx,"Remaining_Capacity"] = (capacity_df_copy.loc[idx,"Capacity_KG"] - capacity_df_copy.loc[idx,"Loaded_So_Far"])
                        capacity_df_copy.loc[idx,"Load_Percentage"] = (capacity_df_copy.loc[idx,"Loaded_So_Far"] / capacity_df_copy.loc[idx,"Capacity_KG"]) * 100
                        break
            else:
            # ML doesn't know (new airline)
                best_option = sorted(feasible, key=lambda x: pd.to_datetime(x[4]))[0]  # Sort by actual date and take the earliest
                best_flight, idx, day_num, flight_day ,actual_date = best_option

                current_loaded = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_So_Far"], errors='coerce') or 0)
                capacity_df_copy.loc[idx, "Loaded_So_Far"] = (current_loaded + shipment_weight)
                current_volume = float(pd.to_numeric(capacity_df_copy.loc[idx, "Loaded_Volume"], errors='coerce') or 0)
                shipment_weight = float(pd.to_numeric(shipment_df.iloc[i]["Weight"], errors='coerce') or 0)
                shipment_volume = pd.to_numeric(shipment_df.iloc[i]["Volume"], errors='coerce')
                if pd.isna(shipment_volume):
                    shipment_volume = 0.0
                shipment_volume = float(shipment_volume)
                capacity_df_copy.loc[idx,"Loaded_Volume"] = (current_volume + shipment_volume)
                capacity_df_copy.loc[idx,"Remaining_Capacity"] = (capacity_df_copy.loc[idx,"Capacity_KG"] - capacity_df_copy.loc[idx,"Loaded_So_Far"])
                capacity_df_copy.loc[idx,"Load_Percentage"] = (capacity_df_copy.loc[idx,"Loaded_So_Far"] / capacity_df_copy.loc[idx,"Capacity_KG"]) * 100
        
 
        assigned_flights.append(best_flight)
        flight_days.append(day_num)
        operating_dates.append(actual_date)

        top3_results.append(
            ", ".join(top3["Prob_Display"].tolist())
        )   
        top3 = top3.reset_index(drop=True)
        
        if best_flight not in ["FedEx", "WAIT", None]:
          route_str = get_actual_route(best_flight, origin, destination, routes_df)
        else:
          route_str = "-"
        debug_text = "\n".join(debug_log)
        routes_output.append(route_str)
        debug_results.append(debug_text)
        
        # Store Debug
        debug_data.append({
            "Run_ID":run_id,
            "AWB": shipment_df.iloc[i]["AWB"],
            "Top3_Flights": top3["Prob_Display"].tolist(),
            "Assigned": best_flight,
            "Route": route_str,
            "Service": service,
            "Weight": shipment_weight,
            "Volume": shipment_volume,
            "Pickup_Date": shipment_df.iloc[i]["Pickup_Date"],
            "Commit_Date": shipment_df.iloc[i]["Commit_Date"],
            "Delivery_Window": shipment_df.iloc[i]["Delivery_Window"],
            "Assigned_Day": day_num,
            "Flight_Day": flight_day,
            "Debug_Log": "\n".join(debug_log)
        })
        
        assignment_records.append({
        "run_id": run_id,
        "AWB": shipment_df.iloc[i]["AWB"],
        "Assigned_Flight": best_flight,
        "Pickup_Date": shipment_df.iloc[i]["Pickup_Date"],
        "Commit_Date": shipment_df.iloc[i]["Commit_Date"],
        "Weight": shipment_weight,
        "Volume": shipment_volume,
        "Assigned_Day": day_num,
        "Route": route_str,
        "Service": service,
        "Assigned_Date": actual_date,
        })
        
    # -------------------------------
    # ADD RESULTS
    # -------------------------------

    shipment_df["Top3_Predicted_Flights"] = top3_results
    shipment_df["Assigned_Flight"] = assigned_flights
    shipment_df["Route"] = routes_output
    shipment_df["Operating_Day_Num"] = flight_days
    shipment_df["Debug_Log"] = debug_results
    shipment_df["Operating_Date"] = operating_dates
    shipment_df["Operating_Date"] = pd.to_datetime(shipment_df["Operating_Date"]).dt.date
    
    return shipment_df, debug_data , capacity_df_copy ,assignment_records
       
if page == "Main Assignment":
   if all([
    st.session_state.get("shipment_file"),
    st.session_state.get("schedule_file"),
    st.session_state.get("routes_file"),
    st.session_state.get("capacity_file"),
    st.session_state.get("pod_file")
    ]):

    st.success("All files uploaded successfully")
    
    shipment_df = read_uploaded_file(st.session_state["shipment_file"])
    schedule_df = read_uploaded_file(st.session_state["schedule_file"])
    routes_df = read_uploaded_file(st.session_state["routes_file"])
    pod_df = read_uploaded_file(st.session_state["pod_file"])
    pod_lookup = create_pod_lookup(pod_df)

    # ================================
    # LOAD CAPACITY (WITH MEMORY)
    # ================================
    latest_run_df = pd.read_sql("""
    SELECT run_id 
    FROM run_metadata
    ORDER BY run_time DESC
    LIMIT 1
    """, engine)
    
    if latest_run_df.empty:
        st.warning("No previous runs found in DB. Using uploaded capacity file.")
        capacity_df = read_uploaded_file(st.session_state["capacity_file"])
        
    else:
        latest_run_id = latest_run_df.iloc[0]["run_id"]
        
        capacity_df = pd.read_sql("""
        SELECT * FROM capacity_table
        WHERE run_id = %(run_id)s
        """, engine, params={"run_id": latest_run_id})

        if capacity_df.empty:
            st.warning("No capacity found in DB. Using uploaded file.")
            capacity_df = read_uploaded_file(st.session_state["capacity_file"])
        else:
            st.success("Loaded capacity from database (persistent memory active)")  
    
    
    def get_file_hash(file):
        return hashlib.md5(file.getvalue()).hexdigest()
    
    file_key = (
        get_file_hash(st.session_state["shipment_file"]),
        get_file_hash(st.session_state["schedule_file"]),
        get_file_hash(st.session_state["routes_file"]),
        get_file_hash(st.session_state["capacity_file"]),
        get_file_hash(st.session_state["pod_file"])
    )
    
    if st.session_state.get("last_file_key") != file_key:
        st.session_state["data_saved"] = False
        st.session_state["model_ran"] = False
        st.session_state["run_clicked"] = False

    # store current key
    st.session_state["last_file_key"] = file_key
    
    capacity_df.columns = (
        capacity_df.columns.str.strip().str.lower()
    )
    
    capacity_df.rename(columns={
        "flight_number": "Flight_Number",
        "day_of_week": "Day_of_Week",
        "day_num": "Day_Num",
        "actual_date": "Actual_Date",
        "capacity_kg": "Capacity_KG",
        "capacity_volume": "Capacity_Volume",
        "loaded_so_far": "Loaded_So_Far",
        "loaded_volume": "Loaded_Volume",
        "remaining_capacity": "Remaining_Capacity",
        "load_percentage": "Load_Percentage"
    }, inplace=True)
    
    numeric_cols = [
        "Capacity_KG",
        "Capacity_Volume",
        "Loaded_So_Far",
        "Loaded_Volume",
        "Remaining_Capacity",
        "Load_Percentage"
    ]
    
    for col in numeric_cols:
        if col in capacity_df.columns:
            capacity_df[col] = pd.to_numeric(capacity_df[col], errors="coerce").fillna(0.0) 
            
    schedule_df["Flight_Number"] = schedule_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()
    routes_df["Flight_Number"] = routes_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()
    capacity_df["Flight_Number"] = capacity_df["Flight_Number"].astype(str).str.replace(" ","").str.strip()
    
    
    # -------------------------------
    # CLEAN COLUMN NAMES
    # -------------------------------

    routes_df.columns = routes_df.columns.str.strip()
    schedule_df.columns = schedule_df.columns.str.strip()
    capacity_df.columns = capacity_df.columns.str.strip()
    # -------------------------------
    # STANDARDIZE COLUMN NAMES
    # -------------------------------
    shipment_df.columns = shipment_df.columns.str.strip()

    column_mapping = {
       "Shipment Pickup Date": "Pickup_Date",
       "Pickup_Date": "Pickup_Date",
       "Commit Date": "Commit_Date",
       "Commit_Date": "Commit_Date",
       "Shipment Pickup_DOW": "Pickup_DOW",
       "Destination Hub": "Destination_Hub"
    }

    shipment_df.rename(columns=column_mapping, inplace=True)
    # -------------------------------
    # CONVERT NUMERIC COLUMNS
    # -------------------------------

    shipment_df["Weight"] = pd.to_numeric(shipment_df["Weight"], errors="coerce")
    shipment_df["Pieces"] = pd.to_numeric(shipment_df["Pieces"], errors="coerce")
    shipment_df["Weight"] = shipment_df["Weight"].fillna(0)
    shipment_df["Pieces"] = shipment_df["Pieces"].fillna(1)
    
    #------------------------------
    # VOLUME HANDLING
    #-------------------------------
    if "Volume" in shipment_df.columns:
       shipment_df["Volume"] = pd.to_numeric(shipment_df["Volume"], errors="coerce").fillna(0)
    else:
        st.error("Volume column missing! Please include a Volume column in your shipment data for better assignment accuracy.")
        st.stop()
        
    # -------------------------------
    # PICKUP WEEKDAY NUMBER
    # -------------------------------

    if "Pickup_DOW" in shipment_df.columns:
       shipment_df["Pickup Weekday Number"] = pd.to_numeric(
        shipment_df["Pickup_DOW"], errors="coerce"
      )
    else:
       shipment_df["Pickup Weekday Number"] = shipment_df["Pickup_Date"].dt.weekday + 1
       shipment_df["Pickup Weekday Number"] = shipment_df["Pickup Weekday Number"].fillna(1)
    
    # -------------------------------
    # FIX SCHEDULE DATA
    # -------------------------------

    schedule_df["Day_of_Week"] = schedule_df["Operating_Day"].astype(str).str.strip()
  
    capacity_df["Day_of_Week"] = capacity_df["Day_of_Week"].astype(str).str.strip()
    
    day_map_num = {
    "Monday":1,
    "Tuesday":2,
    "Wednesday":3,
    "Thursday":4,
    "Friday":5,
    "Saturday":6,
    "Sunday":7
    }

    capacity_df["Day_Num"] = capacity_df["Day_of_Week"].map(day_map_num)
    
    if "Actual_Date" not in capacity_df.columns and "actual_date" not in capacity_df.columns:
       

        capacity_df = expand_capacity_schedule(capacity_df, schedule_df, ready_date, planning_horizon)
    
    # -------------------------------
    # CAPACITY TRACKING
    # -------------------------------

    capacity_df["Loaded_So_Far"] = capacity_df.get("Loaded_So_Far", 0)
    capacity_df["Remaining_Capacity"] = capacity_df["Capacity_KG"] - capacity_df["Loaded_So_Far"]
    capacity_df["Load_Percentage"] = (capacity_df["Loaded_So_Far"] / capacity_df["Capacity_KG"]).fillna(0) * 100
    
    capacity_df["Loaded_Volume"] = capacity_df.get("Loaded_Volume", 0)
    
    if "Capacity_Volume" not in capacity_df.columns:
       capacity_df["Capacity_Volume"] = capacity_df["Capacity_KG"] 
       
       
    # -------------------------------

    # Handle Pickup Date
    
    if "Pickup_Date" not in shipment_df.columns:
       st.error("Pickup date column missing!")
       st.stop()

    shipment_df["Pickup_Date"] = pd.to_datetime(
       shipment_df["Pickup_Date"], errors="coerce"
    )

    # Handle Commit Date
    if "Commit_Date" in shipment_df.columns:
       shipment_df["Commit_Date"] = pd.to_datetime(
        shipment_df["Commit_Date"], errors="coerce"
    )
    else:
       shipment_df["Commit_Date"] = pd.NaT

    # -------------------------------
    # FILL MISSING COMMIT DATES
    # -------------------------------

    def generate_commit_date(row):

       if pd.notnull(row["Commit_Date"]):
        return row["Commit_Date"]

       service = row["Service"]
       pickup = row["Pickup_Date"]

       if service == "IP":
        return pickup + pd.Timedelta(days=3)  # IP is faster, so we set a shorter default delivery window
       
       elif service == "IE":
        return pickup + pd.Timedelta(days=5)  # IE is slower, so we set a longer default delivery window
    
       elif service == "IPF":
        return pickup + pd.Timedelta(days=5)

       elif service == "IEF":
        return pickup + pd.Timedelta(days=7)

       else:
        return pickup + pd.Timedelta(days=5)  # default fallback

    shipment_df["Commit_Date"] = shipment_df.apply(generate_commit_date, axis=1)
    shipment_df["Delivery_Window"] = (
        shipment_df["Commit_Date"] - shipment_df["Pickup_Date"]
    ).dt.days
    shipment_df["Delivery_Window"] = shipment_df["Delivery_Window"].fillna(5)  # default to 5 days if commit date is missing or invalid
    # -------------------------------
    # CALCULATE URGENCY LEVEL
    # -------------------------------

    def urgency_level(x):
        if x <= 3:
            return "Critical"
        elif x <= 5:
            return "High"
        elif x <= 7:
            return "Medium"
        else:
            return "Low"

    shipment_df["Urgency_Level"] = shipment_df["Delivery_Window"].apply(urgency_level)

    shipment_df.drop(columns=["Destination"], inplace=True,errors="ignore")

    # -------------------------------
    # PREVIEW SHIPMENT DATAapp.py
    # -------------------------------
    st.markdown('<div class="card">', unsafe_allow_html=True)

    if "show_preview" not in st.session_state:
        st.session_state["show_preview"] = False

    if st.button("📦 Shipment Data Preview"):
        st.session_state["show_preview"] = not st.session_state["show_preview"]

    if st.session_state["show_preview"]:
        if "shipment_df" in st.session_state:
            st.dataframe(st.session_state["shipment_df"].head(), use_container_width=True)
        else:
            st.dataframe(shipment_df.head(), use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------------
    # FEATURE ENGINEERING
    # -------------------------------
    shipment_df= shipment_df.drop_duplicates(subset=["AWB"])
    
    # -------------------------------
    # FEATURE ENGINEERING (FOR TEST DATA)
    # -------------------------------
    
    processed = prepare_features(shipment_df, feature_columns)

  # 🚀 RUN BUTTON (FIX 4)
    col1, col2, col3 = st.columns([1,1,4])

    with col1:
        run_clicked = st.button("🚀 Run Assignment Model",use_container_width=False,help="Click to run intelligent flight allocation")
        
            # Reset flags for fresh run
        if run_clicked:
            st.session_state["run_clicked"] = True
            st.session_state["model_ran"] = False
            st.session_state["metadata_saved"] = False
            st.session_state["data_saved"] = False
            
            # Create new run_id ONLY when button clicked
            ist = pytz.timezone("Asia/Kolkata")
            
            st.session_state["run_id"] = datetime.now(ist).strftime("%Y%m%d_%H%M%S")

        run_id = st.session_state.get("run_id",None)
    
    if st.session_state.get("run_clicked", False):
    
        if not st.session_state.get("model_ran", False):
            with st.spinner("🚀 Running Assignment Model... Please wait"):
                shipment_df, debug_data ,updated_capacity_df ,assignment_records = run_assignment_model(  
                    processed,
                    schedule_df,
                    shipment_df,
                    routes_df,
                    capacity_df,
                    pod_lookup,
                    run_id,
                    ready_date
                )
                
                # -------------------------------
                # CLEAN COLUMN NAMES (CRITICAL FIX)
                # -------------------------------
                updated_capacity_df.columns = (
                    updated_capacity_df.columns
                    .str.strip()
                    .str.lower()
                    .str.replace(" ", "_")
                    .str.replace(r'__\d+', '', regex=True)   
                )
                updated_capacity_df = updated_capacity_df.loc[:, ~updated_capacity_df.columns.duplicated()]  # Remove duplicate columns if any
                updated_capacity_df["actual_date"] = pd.to_datetime(updated_capacity_df["actual_date"], errors="coerce")

                # -------------------------------
                # STANDARDIZE COLUMN NAMES
                # -------------------------------
                updated_capacity_df = updated_capacity_df.rename(columns={
                    "flight_number": "flight_number",
                    "day_of_week": "day_of_week",
                    "day_num": "day_num",
                    "capacity_kg": "capacity_kg",
                    "capacity_volume": "capacity_volume",
                    "loaded_so_far": "loaded_so_far",
                    "loaded_volume": "loaded_volume",
                    "remaining_capacity": "remaining_capacity",
                    "load_percentage": "load_percentage"
                })

                # -------------------------------
                # ADD RUN ID
                # -------------------------------
                updated_capacity_df["run_id"] = run_id
                
                updated_capacity_df["actual_date"] = pd.to_datetime(updated_capacity_df["actual_date"], errors="coerce")

                # -------------------------------
                # KEEP ONLY REQUIRED COLUMNS (VERY IMPORTANT)
                # -------------------------------
                updated_capacity_df = updated_capacity_df[[
                    "run_id",
                    "flight_number",
                    "day_of_week",
                    "day_num",
                    "actual_date",
                    "capacity_kg",
                    "capacity_volume",
                    "loaded_so_far",
                    "loaded_volume",
                    "remaining_capacity",
                    "load_percentage"
                ]]
                
                #  ADD DEBUG PRINTS HERE
                print("DF COLUMNS:", updated_capacity_df.columns.tolist())
                print("DF DTYPES:\n", updated_capacity_df.dtypes)
                print("DF SAMPLE:\n", updated_capacity_df.head())
                
                # -------------------------------
                # INSERT INTO DB
                # -------------------------------
                from sqlalchemy.exc import SQLAlchemyError

                try:
                    # -------------------------------
                    # FORCE DATA TYPES (CRITICAL FIX)
                    # -------------------------------
                    updated_capacity_df["day_num"] = pd.to_numeric(
                        updated_capacity_df["day_num"], errors="coerce"
                    ).fillna(0).astype(int)

                    float_cols = [
                        "capacity_kg",
                        "capacity_volume",
                        "loaded_so_far",
                        "loaded_volume",
                        "remaining_capacity",
                        "load_percentage"
                    ]

                    for col in float_cols:
                        updated_capacity_df[col] = pd.to_numeric(
                            updated_capacity_df[col], errors="coerce"
                        ).fillna(0.0)

                    updated_capacity_df["flight_number"] = updated_capacity_df["flight_number"].astype(str)
                    updated_capacity_df["day_of_week"] = updated_capacity_df["day_of_week"].fillna("Unknown").astype(str)
                    updated_capacity_df["run_id"] = updated_capacity_df["run_id"].astype(str)

                    # -------------------------------
                    # FINAL INSERT
                    # -------------------------------
                    updated_capacity_df.to_sql(
                        "capacity_table",
                        engine,
                        if_exists="append",
                        index=False
                    )

                    print(" Capacity inserted successfully")

                except Exception as e:
                    print(" REAL ERROR:", e)
                    print(" FAILED DATA:")
                    print(updated_capacity_df.head())
                    raise
                
                assignment_df = pd.DataFrame(assignment_records)
                # =========================
                # SAVE DEBUG DATA (CRITICAL FIX)
                # =========================
                debug_df = pd.DataFrame(debug_data)

                debug_df.columns = (
                    debug_df.columns
                    .str.strip()
                    .str.lower()
                    .str.replace(" ", "_")
                )

                debug_df.to_sql(
                    "debug_log",
                    engine,
                    if_exists="append",
                    index=False
                )
                    
                # ================================
                # SAVE ASSIGNMENT LOG (SAFE INSERT)
                # ================================

                # Delete old records for same run_id (prevents duplicates)
                with engine.begin() as conn:
                    conn.execute(
                        text("DELETE FROM assignment_log WHERE run_id = :run_id"),
                        {"run_id": run_id}
                    )

                    # Insert fresh data
                    assignment_df.columns = (
                        assignment_df.columns
                        .str.strip()
                        .str.lower()
                        .str.replace(" ", "_")
                    )

                    assignment_df = assignment_df[[
                        "run_id",
                        "awb",
                        "assigned_flight",
                        "pickup_date",
                        "commit_date",
                        "weight",
                        "volume",
                        "assigned_day",
                        "assigned_date",
                        "route",
                        "service"
                    ]]

                    assignment_df.to_sql(
                        "assignment_log",
                        engine,
                        if_exists="append",
                        index=False
                    )

                # ================================
                # SAVE RUN METADATA (ALWAYS SAFE)
                # ================================
                existing_meta = pd.read_sql(
                text("SELECT COUNT(*) as cnt FROM run_metadata WHERE run_id = :run_id"),
                engine,
                params={"run_id": run_id}
                )

                if existing_meta["cnt"][0] == 0:
                    run_meta = pd.DataFrame([{
                        "run_id": run_id,
                        "run_time": datetime.now(),
                        "planning_date": ready_date,
                        "total_shipments": len(shipment_df)
                    }])

                    run_meta.columns = (
                        run_meta.columns
                        .str.strip()
                        .str.lower()
                    )

                    run_meta = run_meta[[
                        "run_id",
                        "run_time",
                        "planning_date",
                        "total_shipments"
                    ]]

                    run_meta.to_sql(
                        "run_metadata",
                        engine,
                        if_exists="append",
                        index=False
                    )

                st.session_state["shipment_df"] = shipment_df
                st.session_state["debug_data"] = debug_data
                st.session_state["last_file_key"] = file_key
                st.session_state["run_clicked"] = False
                st.session_state["model_ran"] = True
            
    
    shipment_df = st.session_state.get("shipment_df",shipment_df)
    
    
    # -------------------------------
    # DISPLAY RESULTS
    # -------------------------------
    st.markdown('<div class="card">',unsafe_allow_html=True) 
    
    col1, col2 = st.columns(2)

    with col1:
      st.markdown(f"""
      <div class="metric-card">
        <div class="metric-value">
            {len(shipment_df)}
        </div>
        <div class="metric-label">Total Shipments</div>
      </div>
      """, unsafe_allow_html=True)

    with col2:
      if st.session_state.get("model_ran", False):
        value = shipment_df["Assigned_Flight"].nunique()
      else:
        value = 0

      st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">
                    {value}
                </div>
                <div class="metric-label">Unique Assigned Flights</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown('</div>',unsafe_allow_html=True)
        
    if st.session_state.get("model_ran", False):
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Flight Assignment Results")
        display_cols = ["AWB", "Pieces","Weight","Service","Top3_Predicted_Flights","Pickup_Date","Commit_Date","Assigned_Flight","Operating_Day_Num","Route","Debug_Log"]
        
        existing_cols = [col for col in display_cols if col in shipment_df.columns]
        st.dataframe(shipment_df[existing_cols],use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    #else:
        #st.info("👉 Click 'Run Assignment Model' to generate results")
    
    st.markdown('<div class="card">',unsafe_allow_html=True)
    
      # ==============================
    # DOWNLOAD MAIN RESULTS
    # ==============================
    output = io.BytesIO()

    shipment_df = shipment_df.drop(columns=["Shipment Pickup_DOW"], errors="ignore")

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        shipment_df.to_excel(writer, index=False, sheet_name="Results")

    excel_data = output.getvalue()

    st.download_button(
        label="Download Flight Assignment Results",
        data=excel_data,
        file_name="flight_assignment_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.markdown("## 📊 Run History Dashboard")

    # =========================
    # 1. FETCH DATA FIRST
    # =========================
    run_df = pd.read_sql("SELECT * FROM run_metadata ORDER BY run_time DESC", engine)
    
    run_df["planning_date"] = pd.to_datetime(
    run_df["planning_date"],
    errors="coerce"
    )

    run_df["run_time"] = pd.to_datetime(
        run_df["run_time"],
        errors="coerce"
    )

    run_df["display_name"] = (
        run_df["planning_date"].dt.strftime("%d-%b-%Y").fillna("Unknown Date")
        + " | "
        + run_df["run_time"].dt.strftime("%I:%M %p").fillna("Unknown Time")
        + " | Run "
        + run_df["run_id"].astype(str)
    )
    
    latest_run = pd.read_sql("""
    SELECT MAX(run_id) as run_id FROM assignment_log
    """, engine)

    if latest_run.empty or latest_run["run_id"].isnull().iloc[0]:
        st.error("No runs found. Please run Main Assignment first.")
        st.stop()

    run_id = latest_run["run_id"].iloc[0]

    assign_df = pd.read_sql("""
    SELECT * FROM assignment_log
    """, engine)

    if run_df.empty:
        st.warning("No runs available")
        st.stop()

    # =========================
    # 2. SELECT RUN FIRST
    # =========================
    col1, col2 = st.columns([1, 3])

    with col1:
        selected_display = st.selectbox(
            "Select Run",
            run_df["display_name"],
            key="run_selector"
        )
        
    filtered_run = run_df[
    run_df["display_name"] == selected_display
    ]

    if filtered_run.empty:
        st.error("Run not found")
        st.stop()

    selected_run = filtered_run["run_id"].iloc[0]

    # =========================
    # 3. DISPLAY DATA
    # =========================
    filtered_df = assign_df[assign_df["run_id"] == selected_run]

    st.markdown(f"### 📦 Shipments for Run: {selected_run}")
    st.dataframe(filtered_df)

    # =========================
    # 4. DELETE RUN (SHIFTED BELOW TABLE)
    # =========================
    st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns([3, 1])

    with col3:
        delete_display = st.selectbox(
            "Delete Run",
            run_df["display_name"],
            key="delete_run"
        )
        delete_run = run_df[run_df["display_name"] == delete_display]["run_id"].iloc[0]

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)

        delete_clicked = st.button("Delete Selected Run")

        if delete_clicked:

            latest_run_df = pd.read_sql("""
            SELECT run_id FROM run_metadata ORDER BY run_time DESC LIMIT 1
            """, engine)

            latest_run_id = latest_run_df["run_id"].iloc[0] if not latest_run_df.empty else None

            if delete_run != latest_run_id:
                st.error("❌ You can only delete the latest run")

            else:
                with engine.begin() as conn:

                    conn.execute(text("""
                        DELETE FROM assignment_log WHERE run_id = :run_id
                    """), {"run_id": delete_run})

                    conn.execute(text("""
                        DELETE FROM run_metadata WHERE run_id = :run_id
                    """), {"run_id": delete_run})

                    conn.execute(text("""
                        DELETE FROM capacity_table WHERE run_id = :run_id
                    """), {"run_id": delete_run})
                    
                    conn.execute(text("""
                        DELETE FROM debug_log WHERE run_id = :run_id
                    """), {"run_id": delete_run})
                    
                keys_to_clear = [
                    "shipment_df",
                    "debug_data",
                    "model_ran",
                    "run_clicked",
                    "run_id"
                ]   
                
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]



                #  ADD THIS (CRITICAL FIX)
                if "debug_data" in st.session_state:
                    del st.session_state["debug_data"]
                    
                st.session_state["model_ran"] = False
                st.session_state["run_clicked"] = False

                st.success(f"Run {delete_run} deleted successfully")
                st.cache_data.clear()
                st.cache_resource.clear()
                
                st.rerun()
                    
    # =========================
    # 5. COMPARE RUNS
    # =========================
    col5, col6 = st.columns([1, 3])

    with col5:
        compare_runs = st.multiselect(
            "Compare Runs",
            run_df["run_id"].unique()
        )

    if compare_runs:
        compare_df = assign_df[assign_df["run_id"].isin(compare_runs)]
        st.markdown("### 🔍 Comparison View")
        st.dataframe(compare_df)
        


    # =========================
    # 6. METRICS
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(run_df)}</div>
            <div class="metric-label">Total Runs</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(assign_df)}</div>
            <div class="metric-label">Total Shipments Logged</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{assign_df["assigned_flight"].nunique()}</div>
            <div class="metric-label">Unique Flights Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    
    # ==============================
    #  Debug DASHBOARD
    # ==============================
elif page == "Debug Dashboard":

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## Debug Dashboard")  
        
        st.markdown("""
        <style>
        [data-testid="stExpander"] summary {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        [data-testid="stExpander"] summary svg {
            fill: #FFFFFF !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <style>
        /* Expander header text */
        [data-testid="stExpander"] summary {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        /* Arrow icon */
        [data-testid="stExpander"] summary svg {
            fill: #FFFFFF !important;
        }

        /* Hover effect (optional but clean) */
        [data-testid="stExpander"] summary:hover {
            color: #BBDEFB !important;
        }
        /* Debug panel text visibility fix */
        .debug-container {
            color: #FFFFFF !important;
        }
       

        /* Normal text */
        .debug-container p, 
        .debug-container span, 
        .debug-container div {
            color: #E6E6E6 !important;
        }

        /* Top 3 flights */
        .debug-container ul {
            color: #FFFFFF !important;
        }

        /* SUCCESS (Selected) */
        .debug-success {
            color: #00FFAA !important;
            font-weight: 600;
        }

        /* ERROR (Rejected) */
        .debug-error {
            color: #FF4B4B !important;
            font-weight: 600;
        }

        /* WARNING (Skipped) */
        .debug-warning {
            color: #FFD166 !important;
            font-weight: 600;
        }

        /* INFO */
        .debug-info {
            color: #66CFFF !important;
        }
        /* ===== FIX EXPANDER ACTIVE (CLICKED) STATE ===== */

        /* When expander is OPEN */
        details[open] > summary {
            color: #000000 !important;
            background-color: #ffffff !important;
            border-radius: 8px;
        }

        /* Force all text inside header */
        details[open] > summary * {
            color: #000000 !important;
        }

        /* Fix arrow icon */
        details[open] > summary svg {
            fill: #000000 !important;
        }

        /* When expander is CLOSED */
        details:not([open]) > summary {
            color: #FFFFFF !important;
        }
        
        </style>
        """, unsafe_allow_html=True)
        
        run_meta_df = pd.read_sql("""SELECT * FROM run_metadata ORDER BY run_time DESC""", engine)
        if run_meta_df.empty:
            st.warning("No runs found. Please run Main Assignment first.")
            st.stop()
        
        latest_run_id = run_meta_df.iloc[0]["run_id"]

        debug_df = pd.read_sql("""
        SELECT * FROM debug_log WHERE run_id = %(run_id)s
        """, engine, params={"run_id": latest_run_id})

        if debug_df.empty:
            st.warning("No debug data available")
            st.stop()

        # =========================
        # KPI CALCULATION (MOVE OUTSIDE)
        # =========================
        total = len(debug_df)
        fedex_count = sum(debug_df["assigned"] == "FedEx") if "assigned" in debug_df.columns else 0
        commercial = total - fedex_count

        st.markdown(f"""
        <div style="display:flex; gap:20px; margin-bottom:20px;">
            <div style="flex:1; padding:20px; border-radius:12px; background:#1e293b;">
                <h4 style="color:#94a3b8;">Total Shipments</h4>
                <h2 style="color:#ffffff;">{total}</h2>
            </div>
            <div style="flex:1; padding:20px; border-radius:12px; background:#064e3b;">
                <h4 style="color:#6ee7b7;">Commercial</h4>
                <h2 style="color:#ffffff;">{commercial}</h2>
            </div>
            <div style="flex:1; padding:20px; border-radius:12px; background:#7f1d1d;">
                <h4 style="color:#fca5a5;">FedEx</h4>
                <h2 style="color:#ffffff;">{fedex_count}</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # =========================
        # FILTER
        # =========================
        filter_option = st.selectbox(
            "Filter Shipments",
            ["All", "Commercial Only", "FedEx Only"]
        )

        if "assigned" in debug_df.columns:
            if filter_option == "Commercial Only":
                debug_df = debug_df[debug_df["assigned"] != "FedEx"]
            elif filter_option == "FedEx Only":
                debug_df = debug_df[debug_df["assigned"] == "FedEx"]

        # =========================
        # DEBUG LOG SPLIT
        # =========================
        if "debug_log" in debug_df.columns:
            debug_df["debug_list"] = debug_df["debug_log"].apply(
                lambda x: x.split("\n") if isinstance(x, str) else []
            )
        else:
            st.error("debug_log column missing!")
            st.stop()

        # ==============================
        # DOWNLOAD DEBUG
        # ==============================
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            debug_df.to_excel(writer, index=False, sheet_name="Debug")

        st.download_button(
            label="Download Debug Data",
            data=output.getvalue(),
            file_name="debug_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

            
        # ==============================
        # EXPANDABLE UI (MAIN FEATURE)
        # ==============================
        for i, row in debug_df.iterrows():

            status_color = "#22c55e" if str(row["assigned"]).lower() != "fedex" else "#ef4444"

            with st.expander(f"📦 Shipment {row['awb']} → {row['assigned']}"):

                st.markdown(f"""
                <div style="
                    background-color: rgba(0,0,0,0.6);
                    padding: 12px;
                    border-radius: 10px;
                    margin-bottom: 10px;
                ">
                    <p style="color:#FFFFFF; font-weight:600;">Route: {row['route']}</p>
                    <p style="color:#FFFFFF; font-weight:600;">Service: {row['service']}</p>
                    <p style="color:#FFFFFF; font-weight:600;">Pickup Date: {row['pickup_date']}</p>
                    <p style="color:#FFFFFF; font-weight:600;">Commit Date: {row['commit_date']}</p>
                    <p style="color:#FFFFFF; font-weight:600;">Delivery Window: {row['delivery_window']} days</p>
                    <p style="color:#FFFFFF; font-weight:600;">Flight Day: {row['assigned_day']} ({row['flight_day']})</p>
                    <p style="color:#FFFFFF; font-weight:600;">Weight: {row['weight']} | Volume: {row['volume']}</p>
                </div>
                """, unsafe_allow_html=True)

                # TOP 3 ML
                st.markdown("""
                <div style='background:#0f172a; padding:10px; border-radius:8px; margin-bottom:10px;'>
                """, unsafe_allow_html=True)

                st.markdown("### ✈ Top 3 ML Predictions")
                
                import ast

                flights = row["top3_flights"]

                if isinstance(flights, str):
                    try:
                        flights = ast.literal_eval(flights)
                    except:
                        flights = []

                if not isinstance(flights, list):
                    flights = []

                for j, flight in enumerate(flights, 1):
                    st.markdown(f"<p style='color:#93c5fd;'>#{j} → {flight}</p>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

                # DECISION LOG
                st.markdown("### 🔍 Decision Breakdown")

                for log in row["debug_list"]:
                    if "Selected" in log:
                        st.markdown(f"<div style='color:#4ade80;'>✔ {log}</div>", unsafe_allow_html=True)
                    elif "Rejected" in log:
                        st.markdown(f"<div style='color:#f87171;'>✖ {log}</div>", unsafe_allow_html=True)
                    elif "Skipped" in log:
                        st.markdown(f"<div style='color:#facc15;'>⚠ {log}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='color:#38bdf8;'>ℹ {log}</div>", unsafe_allow_html=True)

                st.markdown("<hr style='border:1px solid #1f2937;'>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("Run Main Assignment first to generate debug data.")

        st.markdown('</div>', unsafe_allow_html=True)

 # ==============================
 # Analytics  DASHBOARD
 # ============================== 
elif page == "Analytics Dashboard":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:white;'>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)
    
    assign_df = pd.read_sql("""
    SELECT * FROM assignment_log""",engine)
    
    latest_run_df = pd.read_sql("""
    SELECT run_id FROM run_metadata ORDER BY run_time DESC LIMIT 1""", engine)
    
    latest_run_df = latest_run_df.iloc[0]["run_id"]
    
    latest_assign_df = assign_df[assign_df["run_id"] == latest_run_df]

    capacity_df = pd.read_sql("""
    SELECT * FROM capacity_table
    """, engine)
    
    if "actual_date" in capacity_df.columns:
        capacity_df.rename(
            columns={"actual_date": "Actual_Date"},
            inplace = True
        )

    if capacity_df.empty:
        st.warning("No capacity found in DB. Using uploaded file.")
        capacity_df = read_uploaded_file(st.session_state["capacity_file"])
    else:
        st.success("Loaded latest capacity (memory active)")

    if assign_df.empty:
        st.warning("No data available. Run Main Assignment first.")
        st.stop()

    # CLEAN DATA
    assign_df["assigned_flight"] = (
        assign_df["assigned_flight"]
        .astype(str)
        .str.replace(" ", "")
        .str.strip()
    )

    capacity_df["flight_number"] = (
        capacity_df["flight_number"]
        .astype(str)
        .str.replace(" ", "")
        .str.strip()
    )

    # =========================
    # SHIPMENT COUNT
    # =========================
    airline_counts = latest_assign_df["assigned_flight"].value_counts().reset_index()
    airline_counts.columns = ["Airline", "Shipments"]

    # Safety
    if airline_counts.empty:
        st.warning("No airline data available")
        st.stop()
    airline_counts["Airline"] = airline_counts["Airline"].astype(str)

    import plotly.express as px
    legend=dict(
    font=dict(color="white"),
    bgcolor="rgba(0,0,0,0)"
    )

    fig1 = px.bar(
        airline_counts,
        x="Airline",
        y="Shipments",
        title="Shipments per Airline",   
        color_discrete_sequence=["#FFB366"]
    )

    fig1.update_layout(
        title=dict(
            text="Shipments per Airline",
            font=dict(size=20, color="white")
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        
        xaxis=dict(
    title=dict(
        text="Airline",
        font=dict(color="white", size=16)
    ),
    tickfont=dict(
        color="white",
        size=13
    )   
),
        xaxis_type='category',
        
        
        yaxis=dict(
    title=dict(
        text="Shipments",
        font=dict(color="white", size=16)
    ),
    tickfont=dict(
        color="white",
        size=13
    )
),
    )

    st.plotly_chart(fig1, use_container_width=True)

    # =========================
    # PIE CHART
    # =========================
    fig2 = px.pie(
    airline_counts,
    names="Airline",
    values="Shipments",
    title="Shipment Share",
    color_discrete_sequence=["#FF6A00", "#FF8C42", "#FFA64D", "#FFB366"]
    )

    fig2.update_traces(
    textinfo='percent+label',
    textfont=dict(color='white', size=14),
    marker=dict(
        colors=["#FF6A00", "#FF8C42", "#FFA64D", "#FFB366"],
        line=dict(color='#000000', width=2)
    )
    )
    
    fig2.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color="white"),
    margin=dict(t=50, b=0, l=0, r=0),
    title_font=dict(size=20, color="white"),
    showlegend=True,
    legend=dict(
        font=dict(color="white", size=12),
        bgcolor="rgba(0,0,0,0)"
    )
    )

    st.plotly_chart(fig2, use_container_width=True)

    # =========================
    # CAPACITY VS LOAD
    # =========================
    # DO NOT GROUP — USE RAW DATA
    used_flights = assign_df["assigned_flight"].unique()

    summary_df = capacity_df[
        capacity_df["flight_number"].isin(used_flights)
    ].copy()

    summary_df = summary_df[
        summary_df["loaded_so_far"] > 0
    ]

    # =========================
# DATE SORT FIX
# =========================

    summary_df["Actual_Date"] = pd.to_datetime(
        summary_df["Actual_Date"]
    )

    # FIRST SORT BY DATE
    summary_df = summary_df.sort_values(
        by=["Actual_Date", "flight_number"]
    )

    # THEN CREATE LABEL
    summary_df["flight_day"] = (
        summary_df["flight_number"]
        + " ("
        + summary_df["Actual_Date"].dt.strftime("%Y-%m-%d")
        + ")"
    )
    
    fig3 = px.bar(
        summary_df,
        x="flight_day",
        y=["capacity_kg", "loaded_so_far"],
        barmode="group",
        title="Capacity vs Utilization (Day-wise)",
        color_discrete_sequence=["#FF6A00", "#FFA64D"]
    )

    fig3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        title_font=dict(size=20, color="white"),
        
        xaxis=dict(
    title=dict(
        text="Airline + Date",
        font=dict(color="white", size=16)
    ),
    tickfont=dict(
        color="white",
        size=13
    )
),      
        yaxis=dict(
    title=dict(
        text="Kg",
        font=dict(color="white", size=16)
    ),
    tickfont=dict(
        color="white",
        size=13
    )
),
    xaxis_tickangle=-45,
        legend=dict(
            font=dict(color="white"),
            bgcolor="rgba(0,0,0,0)"
        )
)

    st.plotly_chart(fig3, use_container_width=True)

    def styled_metric(title, value):
        return f"""
            <div style="
                background-color:#1e1e2f;
                padding:15px;
                border-radius:12px;
                text-align:center;
                box-shadow: 0px 0px 10px rgba(255,106,0,0.3);
            ">
                <div style="color:white; font-size:16px;">{title}</div>
                <div style="color:#FF6A00; font-size:28px; font-weight:bold;">
                    {value}
                </div>
            </div>
            """

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(styled_metric("Total Shipments", len(assign_df)), unsafe_allow_html=True)

    with col2:
        st.markdown(styled_metric("Unique Airlines", assign_df["assigned_flight"].nunique()), unsafe_allow_html=True)

    with col3:
        st.markdown(styled_metric("Top Airline", airline_counts.iloc[0]["Airline"]), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    # =========================
    # SERVICE TYPE BREAKDOWN
    # =========================

    assign_df["assigned_date"] = pd.to_datetime(
        assign_df["assigned_date"])
    
    assign_df =assign_df.sort_values(
        by=["assigned_date","assigned_flight"]
    )
    
    service_summary = (
        assign_df.groupby(
            ["assigned_flight", "assigned_date", "service"]
        )
        .size()
        .reset_index(name="Count")
    )

    service_summary["flight_day"] = (
        service_summary["assigned_flight"]
        + " ("
        + service_summary["assigned_date"].dt.strftime("%Y-%m-%d")
        + ")"
    )
    
    service_summary = service_summary.sort_values(by=["assigned_date","assigned_flight"])
    
    ordered_labels = service_summary["flight_day"].unique().tolist()
    
    ordered_labels = service_summary["flight_day"] = pd.Categorical(
        service_summary["flight_day"],
        categories = ordered_labels,
        ordered=True
    )

    fig_service = px.bar(
        service_summary,
        x="flight_day",
        y="Count",
        color="service",
        barmode="stack",
        title="Service Type Distribution by Flight-Date",
        category_orders= {
            "flight_day":ordered_labels
        }
    )

    fig_service.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',

    font=dict(
        color="white",
        size=13
    ),

    title=dict(
        text="Service Type Distribution by Flight-Day",
        font=dict(
            size=20,
            color="white"
        )
    ),

    legend=dict(
        font=dict(
            color="white",
            size=13
        ),
        bgcolor='rgba(0,0,0,0)'
    ),

    xaxis=dict(
        title=dict(
            text="Airline + Date",
            font=dict(
                color="white",
                size=16
            )
        ),
        tickfont=dict(
            color="white",
            size=12
        ),
        tickangle=-45
    ),

    yaxis=dict(
        title=dict(
            text="Shipment Count",
            font=dict(
                color="white",
                size=16
            )
        ),
        tickfont=dict(
            color="white",
            size=12
        )
    )
)
    st.plotly_chart(fig_service, use_container_width=True)
    
    # =========================
    # UTILIZATION PERCENTAGE
    # =========================

    summary_df["Weight_Utilization_%"] = (
        summary_df["loaded_so_far"]
        / summary_df["capacity_kg"]
    ) * 100

    summary_df["Volume_Utilization_%"] = (
        summary_df["loaded_volume"]
        / summary_df["capacity_volume"]
    ) * 100

    summary_df["Weight_Utilization_%"] = (
        summary_df["Weight_Utilization_%"]
        .fillna(0)
        .round(2)
    )

    summary_df["Volume_Utilization_%"] = (
        summary_df["Volume_Utilization_%"]
        .fillna(0)
        .round(2)
    )

    fig_util = px.bar(
        summary_df,
        x="flight_day",
        y=["Weight_Utilization_%", "Volume_Utilization_%"],
        barmode="group",
        title="Capacity Utilization %",
        color_discrete_sequence=["#FF6A00", "#FFD166"]
    )

    fig_util.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',

    font=dict(
        color="white",
        size=13
    ),

    title=dict(
        text="Capacity Utilization %",
        font=dict(
            size=20,
            color="white"
        )
    ),

    legend=dict(
        font=dict(
            color="white",
            size=13
        ),
        bgcolor='rgba(0,0,0,0)'
    ),

    xaxis=dict(
        title=dict(
            text="Airline + Date",
            font=dict(
                color="white",
                size=16
            )
        ),
        tickfont=dict(
            color="white",
            size=12
        ),
        tickangle=-45
    ),

    yaxis=dict(
        title=dict(
            text="Utilization %",
            font=dict(
                color="white",
                size=16
            )
        ),
        tickfont=dict(
            color="white",
            size=12
        )
    )
)
    st.plotly_chart(fig_util, use_container_width=True)
    
    # ==============================
    # DEFAULT PAGE
    # ==============================
else:
    st.info("Please upload all four files to start flight prediction.")
    
