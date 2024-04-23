import streamlit as st
import pandas as pd
import pandas_dedupe
from io import BytesIO
from pandasai import SmartDataframe
import os
import datetime as dt

# Set environment variables
os.environ['PANDASAI_API_KEY'] = '$2a$10$IGYkEHGfkhN4uVNZ34EBI.FaL5CkQD/YuZsgdCLn/Y9pz2SMFpVdG'

# Set page configuration
st.set_page_config(page_title="ADNIC AI DEPDUP", page_icon=":bar_chart:", layout='wide')

# Define file path globally
file_path = "modified_data.xlsx"
background_image_url = "https://e0.pxfuel.com/wallpapers/53/768/desktop-wallpaper-abstract-technology-background-network-connection-structure-sc-high-resolution.jpg"

# Define the CSS styling with the background image
background_image_style = f"""
    <style>
        .stApp {{
            background-image: url('{background_image_url}');
            background-size: cover;
            
        }}
    </style>
"""

# Apply the CSS styling to the page
st.markdown(background_image_style, unsafe_allow_html=True)
dark_theme_css = """
    <style>
        body {
            color: white;
        }
        .stApp {
            color: white;
            /* Add more custom CSS styles for specific elements as needed */
        }
        /* Adjust the background color if necessary */
    </style>
"""

# Apply the custom CSS
st.markdown(dark_theme_css, unsafe_allow_html=True)
@st.cache(allow_output_mutation=True)
def process_file(df, use_saved_settings=False, settings_path="dedupe_settings"):
    if df.empty:
        st.warning("The DataFrame is empty.")
        return None

    # Drop 'cluster id' and 'confidence' columns if they exist
    df = df.drop(['cluster id', 'confidence'], axis=1, errors='ignore')

    if use_saved_settings:
        deduped_df = pandas_dedupe.dedupe_dataframe(df, ['Name', 'DOB', 'Emirates ID', 'Gender', 'Passport', 'Mobile no', 'Traffic ID'], config_name=settings_path)
    else:
        deduped_df = pandas_dedupe.dedupe_dataframe(df, ['Name', 'DOB', 'Emirates ID', 'Gender', 'Passport', 'Mobile no', 'Traffic ID'])
    
    deduped_df_sorted = deduped_df.sort_values(by="cluster id", ascending=True)
    
    deduped_df_sorted.to_excel(file_path, index=False)

    return deduped_df_sorted

# Function to check if a new entry exists in the DataFrame
def check_existing_entry(df, new_entry):
    existing_entries = df[
        (df["Emirates ID"] == new_entry["Emirates ID"]) |
        (df["Passport"] == new_entry["Passport"]) |
        (df["Mobile no"] == new_entry["Mobile no"]) |
        (df["Traffic ID"] == new_entry["Traffic ID"])
    ]
    return not existing_entries.empty
def merge_entries_by_cluster(df):
    # Define a custom aggregation function that prefers the most frequent value, or the latest if a tie
    def most_frequent_or_latest(series):
        if series.dropna().empty:
            return None
        else:
            return series.mode().iloc[0] if not series.mode().empty else series.dropna().iloc[-1]

    # Group by 'cluster id' and aggregate using the custom function
    merged_df = df.groupby('cluster id').agg(lambda x: most_frequent_or_latest(x)).reset_index()

    # Save to a new file
    merged_file_path = "merged_data_set.xlsx"
    merged_df.to_excel(merged_file_path, index=False)
    return merged_df
# Main app
def main():
    st.title("WELCOME USER!")
    st.title(':magic_wand: AI DEDUPE WIZARD')

    with st.spinner("Processing your data..."):
        df_to_append = pd.read_excel(file_path)
        use_saved_settings = st.checkbox('Use saved deduplication settings')

        processed_df = process_file(df_to_append, use_saved_settings)
    
    st.title("Update DataFrame and Export to Excel")

    # Load modified file
    modif = pd.read_excel(file_path)

    # Initialize DataFrame
    if "modif" not in st.session_state:
        st.session_state.modif = modif

    # Display current DataFrame
    st.write("Current DataFrame:")
    st.dataframe(st.session_state.modif, width=5000)

    # Form to input new data
    st.title("ADD/CHECK DATA")
    with st.form("data_entry_form"):
        name = st.text_input("Enter Name:")
        # Set default value for empty date field and increase the date input size
        default_date = dt.datetime.now().date()
        dob = st.date_input("Enter date", value=default_date, min_value=dt.date(1900, 1, 1), max_value=default_date + dt.timedelta(days=365), key="dob")
        Emirates_id = st.text_input("Enter EID:", value=None)
        Gender = st.selectbox("Gender", ["Male", "Female", "Non"], index=0)
        PPN = st.text_input("Enter PASSPORT:", value=None)
        mobile = st.text_input("Enter Mob:", value=None)
        trf = st.text_input("Enter trf:", value=None)
        submit_button = st.form_submit_button(label="Submit")

    # When form is submitted, update DataFrame and export to Excel
    if submit_button:
        # Create a dictionary for the new entry
        new_entry = {"Name": name, "DOB": dob, "Emirates ID": Emirates_id, "Gender": Gender, "Passport": PPN, "Mobile no": mobile, "Traffic ID": trf}
        
        # Check if the new entry already exists
       
        st.error("This entry already exists in the DataFrame.")
        # Display DataFrame with similar values
        similar_entries_df = st.session_state.modif[ 
                                                        (st.session_state.modif["Emirates ID"] == new_entry["Emirates ID"]) | 
                                            
                                                        (st.session_state.modif["Passport"] == new_entry["Passport"]) | 
                                                        (st.session_state.modif["Mobile no"] == new_entry["Mobile no"]) | 
                                                        (st.session_state.modif["Traffic ID"] == new_entry["Traffic ID"])]
        st.write("Similar Entries:")
        st.dataframe(similar_entries_df)
        
        # Append new data to DataFrame
        st.session_state.modif = st.session_state.modif.append(new_entry, ignore_index=True)
            
        # Export DataFrame to Excel
        st.session_state.modif.to_excel(file_path, index=False)

        # Process the DataFrame for deduplication
        processed_df = process_file(st.session_state.modif, use_saved_settings)  
        st.session_state.modif = processed_df  # Update the session DataFrame

        # Display updated DataFrame
        

    if processed_df is not None:
            st.write("Updated DataFrame:")
            st.dataframe(modif, width=1000)
            merged_df = merge_entries_by_cluster(processed_df)
            st.write("Merged DataFrame based on Cluster ID:") 
            st.dataframe(merged_df, width=1000)
            st.success("Merged data set saved as 'merged_data_set.xlsx'.")

            # Allow users to download the merged data set
            towrite = BytesIO()
            merged_df.to_excel(towrite, index=False, header=True)
            towrite.seek(0)
            st.download_button("Download Merged Data Set", towrite, "merged_data_set.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
            df = SmartDataframe(st.session_state.modif)  
    with st.spinner("AI IS RETRIEVING YOUR ANSWER..."):
            st.subheader("CHAT WITH YOUR DATA :wave:")
            st.write(":robot_face: POWERED BY OPENAI")
            with st.chat_message("user"):
                st.write("Hello 👋")
                query = st.chat_input("Enter your question:")

           
                st.write("User question:",query)
                response = df.chat(query)
                st.success(response)

    # Count duplicate and unique values
    if "modif" in st.session_state:
        duplicate_count = len(st.session_state.modif) - len(st.session_state.modif.drop_duplicates())
        unique_count = len(st.session_state.modif.drop_duplicates())
        st.write(f"Number of duplicate values: {duplicate_count}")
        st.write(f"Number of unique values: {unique_count}")

if __name__ == "__main__":
    main()
