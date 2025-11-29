import streamlit as st
import pandas as pd
import re
from io import BytesIO


# Regex Functions
def get_ae2(text, instance_keyword):
    pattern = rf"{re.escape(instance_keyword)}"
    match = re.search(pattern, str(text), re.IGNORECASE)
    return match.group(0) if match else None

def get_outer(text, unit_keyword):
    escaped = re.escape(unit_keyword)
    escaped = escaped.replace(r"\ ", r"\s*[-_]*\s*")
    pattern = rf"{escaped}"
    match = re.search(pattern, str(text), re.IGNORECASE)
    return match.group(0) if match else None

def get_unit(text):
    match = re.search(r'unit\s+(\d+)', str(text), re.IGNORECASE)
    return match.group(1) if match else None

def get_instance(text):
    match = re.search(r'description\s+"([^"]+)', str(text), re.IGNORECASE)
    return match.group(1).split(' - ')[0] if match else None

def routing_instances(text):
    match = re.search(r'routing-instances\s+(\S+)', str(text), re.IGNORECASE)
    return match.group(1) if match else None



# -----------------------------
# Streamlit Page Configuration
# -----------------------------
st.set_page_config(page_title="Data Extraction", page_icon="📘", layout="centered")

st.markdown("""
<style>
    .main-container { max-width: 850px; margin: auto; }
    .card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        border: 1px solid #e6e6e6;
    }
    .stButton>button {
        background-color: #1a73e8;
        color: white;
        padding: 10px 25px;
        border-radius: 8px;
        font-size: 16px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #155bb5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

st.title("📘 Data Extracting Tool")

st.markdown("<div class='card'>", unsafe_allow_html=True)
file = st.file_uploader("Upload your Excel file", type=["xlsx"])
instance_keyword = st.text_input("Enter instance type (example: ae2)")
unit_keyword = st.text_input("Enter outer value (example: outer -1002)")
st.markdown("</div>", unsafe_allow_html=True)

if file and instance_keyword and unit_keyword:
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    if st.button("🚀 Process File"):
        df = pd.read_excel(file)

        # Apply your backend logic
        # df["instance_extracted"] = df["source_text"].apply(lambda x: get_ae2(str(x), instance_keyword))
        # df["unit_extracted"] = df["source_text"].apply(lambda x: get_outer_1002(str(x), unit_keyword))

        # Apply to each row
        df["ae2_value"]= df["Description"].apply(lambda x: get_ae2(str(x), instance_keyword)) 
        df["outer_value"] = df["Description"].apply(lambda x: get_outer(str(x), unit_keyword))
        df["unit_val"]=df["Description"].apply(get_unit)
        df["instance_val"]=df["Description"].apply(get_instance) 
        df["routing_instance"]=df["Description"].apply(routing_instances)

        # Filter rows where instance and outer exist
        filtered_df= df[(df["ae2_value"].notnull()) & (df["outer_value"].notnull())]

        # Group by unit
        unit_val_list=filtered_df['unit_val'].to_list()
        fin_filtered_df=df[(df["ae2_value"].notnull()) & (df["unit_val"].isin(unit_val_list))]

        instance_val_list= fin_filtered_df['instance_val'].to_list()
        instance_filtered_df=df[(df["routing_instance"].isin(instance_val_list))]

        final_rows=[] 

        for unit, group in fin_filtered_df.groupby("unit_val"):
            final_rows.append(group)
            # Add an empty row (same columns, all Nord)
            final_rows.append(pd.DataFrame([[None]*len(group.columns)], columns=group.columns))

        for unit, group in instance_filtered_df.groupby("routing_instance"):
            final_rows.append(group)
            # Add an empty row (same columns, all None)
            final_rows.append(pd.DataFrame([[None]*len(group.columns)], columns=group.columns))

        final_df=pd.concat(final_rows, ignore_index=True)
        final_df.drop(columns=["ae2_value", "outer_value", "unit_val", "instance_val", "routing_instance"], inplace=True)
        output = BytesIO()
        final_df.to_excel(output, index=False)
        output.seek(0)

        st.success("Processing complete. Download your file below.")

        st.download_button(
            label="📥 Download Processed Excel",
            data=output,
            file_name="processed_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.markdown("</div>", unsafe_allow_html=True)
