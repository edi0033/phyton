import google.generativeai as genai
import streamlit as st
import os

# ==============================================================================
# PENGATURAN API KEY DAN MODEL (PENTING! UBAH SESUAI KEBUTUHAN ANDA)
# ==============================================================================

# Ambil API Key dari Streamlit Secrets atau Environment Variable
# Cara ini lebih aman daripada menuliskannya langsung di kode.
# Di Streamlit Cloud, Anda akan menentukannya di bagian "Secrets".
# Di lokal, Anda bisa mengatur sebagai Environment Variable atau di file .streamlit/secrets.toml
try:
    API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets["GEMINI_API_KEY"]
except (KeyError, AttributeError):
    st.error("API Key Gemini tidak ditemukan. Harap tambahkan GEMINI_API_KEY ke Streamlit Secrets atau Environment Variables Anda.")
    st.stop() # Hentikan aplikasi jika API Key tidak ada

# Nama model Gemini yang akan digunakan.
MODEL_NAME = 'gemini-1.5-flash'

# ==============================================================================
# KONTEKS AWAL CHATBOT (INI BAGIAN YANG BISA SISWA MODIFIKASI!)
# ==============================================================================

# Definisikan peran chatbot Anda di sini.
# Ini adalah "instruksi sistem" yang akan membuat chatbot berperilaku sesuai keinginan Anda.
# Buatlah singkat, jelas, dan langsung pada intinya untuk menghemat token.

# --- CONTOH : CHATBOT PEMANDU WISATA ---
INITIAL_CHATBOT_CONTEXT = [
    {
        "role": "user",
        "parts": ["Kamu adalah Pemandu wisata alam. Beri 2 rekomendasi tempat wisata alam yang menarik. Jawaban singkat dan faktual. Tolak pertanyaan non-sejarah."]
    },
    {
        "role": "model",
        "parts": ["Baik! Masukkan nama kota untuk saya berikan rekomendasi tempat wisata alam yang menarik."]
    }
]

# ==============================================================================
# FUNGSI UTAMA CHATBOT (HINDARI MENGUBAH BAGIAN INI JIKA TIDAK YAKIN)
# ==============================================================================

# Inisialisasi Google Generative AI
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Kesalahan saat mengkonfigurasi API Key: {e}")
    st.stop()

# Inisialisasi model
try:
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config=genai.types.GenerationConfig(
            temperature=0.4, # Kontrol kreativitas (0.0=faktual, 1.0=kreatif)
            max_output_tokens=500 # Batas maksimal panjang jawaban dalam token
        )
    )
except Exception as e:
    st.error(f"Kesalahan saat inisialisasi model '{MODEL_NAME}': {e}")
    st.stop()

# --- Streamlit UI ---
st.set_page_config(page_title="Chatbot Pemandu Wisata", page_icon="🌳")
st.title("Chatbot Pemandu Wisata Alam 🏞️")
st.markdown("Halo! Saya akan membantu Anda menemukan rekomendasi tempat wisata alam yang menarik.")

# Inisialisasi riwayat chat di session_state Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Tambahkan pesan pembuka dari chatbot ke riwayat
    st.session_state.messages.append({"role": "model", "parts": INITIAL_CHATBOT_CONTEXT[1]["parts"][0]})

# Tampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["parts"][0])

# Input pengguna
user_input = st.chat_input("Masukkan nama kota (contoh: 'Bandung') atau ketik 'exit' untuk keluar:")

if user_input:
    # Tambahkan input pengguna ke riwayat
    st.session_state.messages.append({"role": "user", "parts": [user_input]})
    with st.chat_message("user"):
        st.write(user_input)

    if user_input.lower() == 'exit':
        with st.chat_message("model"):
            st.write("Sampai jumpa! Semoga perjalanan Anda menyenangkan.")
        st.stop() # Hentikan proses lebih lanjut

    # Siapkan riwayat untuk model (tidak termasuk pesan 'exit' jika ada)
    # Penting: Sesuaikan riwayat yang dikirim ke model agar sesuai format API Gemini
    # Model membutuhkan riwayat dalam format list of dicts, contoh:
    # [{"role": "user", "parts": ["Halo"]}, {"role": "model", "parts": ["Hai juga"]}]
    
    # Gabungkan INITIAL_CHATBOT_CONTEXT dengan riwayat sesi yang sudah ada
    # Pastikan tidak ada duplikasi pesan pembuka dari model
    history_for_gemini = INITIAL_CHATBOT_CONTEXT + [
        {"role": msg["role"], "parts": msg["parts"]}
        for msg in st.session_state.messages
        if msg["role"] != "model" or msg["parts"][0] != INITIAL_CHATBOT_CONTEXT[1]["parts"][0]
    ]


    # Buat sesi chat dengan riwayat yang ada
    # Hapus pesan terakhir user_input jika dia 'exit'
    chat = model.start_chat(history=history_for_gemini[:-1] if user_input.lower() == 'exit' else history_for_gemini)


    with st.spinner("Chatbot sedang membalas..."):
        try:
            # Kirim input pengguna ke model
            response = chat.send_message(user_input, request_options={"timeout": 60})

            if response and response.text:
                chatbot_response = response.text
            else:
                chatbot_response = "Maaf, saya tidak bisa memberikan balasan."

            # Tambahkan balasan chatbot ke riwayat
            st.session_state.messages.append({"role": "model", "parts": [chatbot_response]})
            with st.chat_message("model"):
                st.write(chatbot_response)

        except Exception as e:
            st.error(f"Maaf, terjadi kesalahan saat berkomunikasi dengan Gemini: {e}")
            st.warning("Kemungkinan penyebab:")
            st.warning("  - Masalah koneksi internet atau timeout.")
            st.warning("  - API Key mungkin dibatasi, tidak valid, atau melebihi kuota.")
            st.warning("  - Masalah internal di server Gemini.")