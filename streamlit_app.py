import streamlit as st
import openai
import json

# ---- Set your page config and custom colors ----
st.set_page_config(page_title="Content Builder MVP", layout="centered")
GMS_TEAL = "#E6F9F3"
GMS_GREEN = "#22B573"
GMS_BLUE = "#C7E7FD"
GMS_LAVENDER = "#D5D7FB"

# ---- Custom CSS for GMS color palette and rounded corners ----
st.markdown(f"""
    <style>
        .stApp {{ background-color: {GMS_TEAL}; }}
        .block-container {{
            background-color: white !important;
            border-radius: 24px;
            padding: 2em 3em;
            margin-top: 2em;
            box-shadow: 0 0 20px {GMS_LAVENDER};
        }}
        .stButton>button {{
            background-color: {GMS_GREEN};
            color: white;
            border-radius: 12px;
            font-weight: 600;
            margin: 0.25em 0.5em 0.25em 0;
        }}
        .stButton>button:hover {{
            background-color: #19995a;
            color: white;
        }}
        .stTextInput>div>div>input,
        .stTextArea textarea {{
            background-color: {GMS_BLUE}10 !important;
            border-radius: 8px;
        }}
    </style>
""", unsafe_allow_html=True)

# ---- Logo and Page Heading ----
st.image("gms_logo.png", width=160)
st.markdown(f"<h1 style='color:{GMS_GREEN};text-align:center;'>Content Builder MVP</h1>", unsafe_allow_html=True)

# ---- System Prompt ----
system_prompt = """MY PROMPT HERE"""

# ---- Input Form ----
with st.form("campaign_form"):
    st.subheader("Campaign Details")
    channel = st.selectbox("Channel", ["whatsapp", "sms", "viber"])
    prompt = st.text_area("Campaign Instruction / Prompt", placeholder="Describe your campaign, product details, offer, and any special instructions.")
    language = st.text_input("Language", "en")
    tone = st.text_input("Tone", "friendly")
    max_length = st.number_input("Max Length", min_value=1, max_value=1024, value=250)
    variants = st.number_input("Number of Variants", min_value=1, max_value=3, value=1)
    generate_btn = st.form_submit_button("Generate Content")

# ---- Store last output for edits ----
if "last_output" not in st.session_state:
    st.session_state.last_output = None
if "last_variants" not in st.session_state:
    st.session_state.last_variants = []

# ---- Call OpenAI and Show Output ----
if generate_btn and prompt:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = openai.OpenAI(api_key=openai_api_key)
    input_json = {
        "prompt": prompt,
        "channel": channel,
        "language": language,
        "tone": tone,
        "maxLength": max_length,
        "variants": int(variants)
    }
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": str(input_json)}
            ],
            max_tokens=2000,
            temperature=0.7,
            n=int(variants)
        )
        # Support for multiple variants
        variant_list = []
        for i in range(int(variants)):
            output = response.choices[i].message.content
            st.write("RAW GPT OUTPUT:", output)   # <-- Added this for debugging
            result = json.loads(output)
            variant_list.append(result)
        st.session_state.last_variants = variant_list
        st.session_state.last_output = variant_list[0]  # Display first by default
        st.session_state.selected_variant = 0
    except Exception as e:
        st.error(f"OpenAI API Error: {e}")
        st.stop()

# ---- Variant selector if multiple ----
if st.session_state.last_variants:
    if len(st.session_state.last_variants) > 1:
        selected = st.selectbox(
            "Select Variant to View/Edit",
            [f"Variant {i+1}" for i in range(len(st.session_state.last_variants))],
            key="variant_select",
            index=st.session_state.get("selected_variant", 0)
        )
        idx = int(selected.split()[-1]) - 1
        st.session_state.last_output = st.session_state.last_variants[idx]
        st.session_state.selected_variant = idx

# ---- OUTPUT section: Editable fields and Edit Content ----
if st.session_state.last_output:
    output = st.session_state.last_output
    st.markdown("### Generated Content")
    header = st.text_input("Header", output.get("header", ""), key="header_out")
    footer = st.text_input("Footer", output.get("footer", ""), key="footer_out")
    body = st.text_area("Body", output.get("body", ""), height=120, key="body_out")
    length = st.text_input("Length", str(output.get("length", "")), key="length_out", disabled=True)
    variant_id = st.text_input("Variant ID", output.get("variant_id", ""), key="variant_id_out", disabled=True)

    # Buttons field (WhatsApp only)
    if channel == "whatsapp":
        st.markdown("#### Buttons")
        buttons = output.get("buttons", [])
        if not buttons:
            buttons = [{} for _ in range(2)]
        new_buttons = []
        for i, btn in enumerate(buttons):
            col1, col2, col3 = st.columns([2, 3, 4])
            with col1:
                btn_type = st.selectbox(f"Type {i+1}", ["", "url", "quick_reply", "call"], index=0 if not btn.get("type") else ["", "url", "quick_reply", "call"].index(btn.get("type","")), key=f"type_{i}")
            with col2:
                btn_text = st.text_input(f"Text {i+1}", btn.get("text",""), key=f"text_{i}")
            with col3:
                btn_placeholder = st.text_input(f"Placeholder {i+1}", btn.get("placeholder",""), key=f"ph_{i}")
            if btn_type and btn_text:
                new_buttons.append({
                    "type": btn_type,
                    "text": btn_text,
                    "placeholder": btn_placeholder
                })
        st.session_state.last_output["buttons"] = new_buttons

    st.markdown("---")
    st.markdown("#### Follow-up Prompt (for edits)")
    follow_up = st.text_input("Describe your change or revision", key="followup")
    edit_btn = st.button("Edit Content")

    if edit_btn and follow_up:
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        client = openai.OpenAI(api_key=openai_api_key)
        edit_input = {
            "prompt": follow_up,
            "channel": channel,
            "language": language,
            "tone": tone,
            "maxLength": max_length,
            "edit_id": variant_id
        }
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": str(edit_input)}
                ],
                max_tokens=2000,
                temperature=0.7,
            )
            import json
            output = response.choices[0].message.content
            st.write("RAW GPT OUTPUT:", output)   # <-- Add this for debugging
            result = json.loads(output)
            st.session_state.last_output = result
            # Replace selected variant in list
            if st.session_state.last_variants:
                idx = st.session_state.selected_variant if "selected_variant" in st.session_state else 0
                st.session_state.last_variants[idx] = result
            st.success("Content edited! See new result above.")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Edit Error: {e}")
