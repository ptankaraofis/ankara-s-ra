import streamlit as st
import pandas as pd
import os
import datetime
import pytz  # Sunucu saatini Türkiye saati yapmak için şart
from streamlit_autorefresh import st_autorefresh

# --- YAPILANDIRMA ---
st.set_page_config(page_title="Paket Lojistik Sıra Sistemi", page_icon="📦", layout="wide")

# Türkiye Saat Dilimi Ayarı (Online sunucularda saatin kaymaması için)
tz_turkey = pytz.timezone("Europe/Istanbul")
now_turkey = datetime.datetime.now(tz_turkey)

today_str = now_turkey.strftime("%Y-%m-%d")
FILE_NAME = f"sira_listesi_{today_str}.csv"
MESAJ_FILE = f"telsiz_mesajlari_{today_str}.csv"
MAX_ICERI_KAPASITE = 3

# --- CANLI SUNUCU UYUMLU KLASÖR AYARI ---
DESKTOP_DIR = "Gunun_Raporlari"
os.makedirs(DESKTOP_DIR, exist_ok=True)


# --- VERİ TABANI FONKSİYONLARI ---
def veri_yukle():
    columns = ["Sıra No", "Adı Soyadı", "Plaka", "Geliş Nedeni", "Saat", "Durum", "Yönlendirilen"]
    if os.path.exists(FILE_NAME):
        try:
            df_loaded = pd.read_csv(FILE_NAME)
            for col in columns:
                if col not in df_loaded.columns:
                    df_loaded[col] = "-"
            return df_loaded
        except:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)


def veri_kaydet(df):
    df.to_csv(FILE_NAME, index=False, encoding="utf-8-sig")


# --- ÇİFT YÖNLÜ TELSİZ FONKSİYONLARI ---
def mesajlari_yukle():
    columns = ["Saat", "Kimden", "Mesaj"]
    if os.path.exists(MESAJ_FILE):
        try:
            df_m = pd.read_csv(MESAJ_FILE)
            for col in columns:
                if col not in df_m.columns:
                    df_m[col] = "-"
            return df_m
        except:
            return pd.DataFrame(columns=columns)
    else:
        return pd.DataFrame(columns=columns)


def mesaj_kaydet(kimden, metin):
    df_m = mesajlari_yukle()
    suan_saat = datetime.datetime.now(tz_turkey).strftime("%H:%M:%S")
    yeni_m = pd.DataFrame([{"Saat": suan_saat, "Kimden": kimden, "Mesaj": metin}])
    df_m = pd.concat([df_m, yeni_m], ignore_index=True)
    df_m.to_csv(MESAJ_FILE, index=False, encoding="utf-8-sig")


def mesajlari_temizle():
    if os.path.exists(MESAJ_FILE):
        os.remove(MESAJ_FILE)


def masaustune_excel_kaydet(df_guncel):
    try:
        suan_saat = datetime.datetime.now(tz_turkey).strftime("%H%M")
        excel_adi = f"Sira_Raporu_{today_str}_{suan_saat}.xlsx"
        dosya_tam_yolu = os.path.join(DESKTOP_DIR, excel_adi)
        df_guncel.to_excel(dosya_tam_yolu, index=False, sheet_name="Günün Listesi")
        
        # Ofis panelinden indirilebilmesi için Streamlit indirme butonu
        with open(dosya_tam_yolu, "rb") as f:
            st.download_button(
                label="📥 Arşivlenmiş Excel Dosyasını İndir",
                data=f,
                file_name=excel_adi,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        return dosya_tam_yolu
    except Exception as e:
        st.error(f"Excel arşivleme sırasında hata oluştu: {e}")
        return None


df = veri_yukle()

# --- URL PARAMETRE KONTROLÜ (QR KOD ÖZELLEŞTİRMESİ) ---
query_params = st.query_params

if "ekran" in query_params and query_params["ekran"] == "kurye":
    ekran_modu = "Kurye Giriş Ekranı"
    # Kurye telefonunda sidebar menüsünü tamamen gizleyen CSS
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {display: none;}
            [data-testid="stSidebarCollapseButton"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    # --- SİDEBAR (EKRAN SEÇİMİ - Sadece Normal Girişte Görünür) ---
    st.sidebar.markdown("### 🖥️ Ekran Seçiniz:")
    ekran_modu = st.sidebar.radio(
        label="Ekran Seçiniz",
        options=["Kurye Giriş Ekranı", "Güvenlik Trafik Ekranı", "Ofis Yönetim Paneli"],
        label_visibility="collapsed"
    )

# --- 1. EKRAN: KURYE GİRİŞ EKRANI ---
if ekran_modu == "Kurye Giriş Ekranı":
    st.title("🛵 Pakettaxi Ofis Giriş Sıra Sistemi 🛵")
    st.write("Lütfen aşağıdaki bilgileri doldurarak sıra numaranızı alınız.")

    with st.container(border=True):
        kurye_isim = st.text_input("Adınız Soyadınız:", placeholder="Örn: Ahmet Yılmaz")
        kurye_plaka = st.text_input("Plakanız (Yoksa boş bırakabilirsiniz):", placeholder="Örn: 34ABC123")

        gelis_sebebi = st.selectbox(
            "Geliş Sebebiniz:",
            ["İş Başlangıcı", "İş Çıkışı", "Operasyon", "Ekipman Satın Alma", "Diğer"]
        )

        diger_aciklama = st.text_input(
            "Geliş Sebebi 'Diğer' ise lütfen buraya açıklama yazınız:",
            placeholder="Açıklama giriniz..."
        )

        st.markdown("---")
        with st.expander("⚖️ KVKK Aydınlatma Metni (Lütfen Okuyunuz)"):
            st.caption(
                "Bu sistem kapsamında işlenen Ad-Soyadı ve Plaka verileriniz, Paket Lojistik ofis içi "
                "giriş-çıkış trafiğinin düzenlenmesi, operasyonel güvenliğin sağlanması ve sıra takibi "
                "amaçlarıyla 6698 sayılı KVKK uyarınca otomatik yollarla işlenmektedir. Verileriniz gün sonunda "
                "güvenli şekilde arşivlenerek yerel sistemlerde saklanacak, üçüncü taraflarla paylaşılmayacaktır."
            )
        kvkk_onay = st.checkbox("Yukarıdaki KVKK Aydınlatma Metni'ni okudum ve verilerimin işlenmesini onaylıyorum.")

        st.markdown("---")
        submit = st.button("Sıra Numarası Al 🚀", use_container_width=True)

        if submit:
            if not kvkk_onay:
                st.error("⚠️ Yasal mevzuat gereği KVKK onay kutusunu işaretlemeniz gerekmektedir!")
            elif kurye_isim.strip() == "":
                st.error("⚠️ Lütfen 'Adınız Soyadınız' alanını boş bırakmayın!")
            else:
                temiz_isim = kurye_isim.strip().title()
                temiz_plaka = kurye_plaka.replace(" ", "").upper()

                if temiz_plaka in ["", "YOK", "0", "-", "."]:
                    temiz_plaka = "-"

                aktif_siralar = df[(df["Adı Soyadı"] == temiz_isim) & (df["Durum"].isin(["Bekliyor", "İşlemde"]))]

                if not aktif_siralar.empty:
                    aktif_sira_no = aktif_siralar.iloc[0]["Sıra No"]
                    st.warning(
                        f"⚠️ {temiz_isim} adına zaten aktif bir sıra bulunmaktadır! Sıra Numaranız: {aktif_sira_no:03d}")
                else:
                    if gelis_sebebi == "Diğer":
                        final_sebep = diger_aciklama.strip() if diger_aciklama.strip() != "" else "Diğer"
                    else:
                        final_sebep = gelis_sebebi

                    yeni_sira = len(df) + 1
                    suan = datetime.datetime.now(tz_turkey).strftime("%H:%M:%S")

                    yeni_kurye = pd.DataFrame([{
                        "Sıra No": yeni_sira,
                        "Adı Soyadı": temiz_isim,
                        "Plaka": temiz_plaka,
                        "Geliş Nedeni": final_sebep,
                        "Saat": suan,
                        "Durum": "Bekliyor",
                        "Yönlendirilen": "-"
                    }])

                    df = pd.concat([df, yeni_kurye], ignore_index=True)
                    veri_kaydet(df)

                    st.success(f"✔️ Sıra Numaranız: {yeni_sira:03d}. Lütfen güvenlik alanında bekleyiniz.")
                    st.balloons()

# --- 2. EKRAN: GÜVENLİK TRAFİK EKRANI ---
elif ekran_modu == "Güvenlik Trafik Ekranı":
    st.title("🛡️ Kapı Güvenlik & Trafik Kontrol Paneli")
    g_sifre = st.text_input("Güvenlik Erişim Şifresi:", type="password", key="g_sifre_input")

    if g_sifre != "filo123":
        st.error("🔒 Bu ekrana yalnızca yetkili güvenlik personeli erişebilir. Lütfen doğru şifreyi giriniz.")
    else:
        st.success("🔓 Güvenlik Paneli Aktif.")
        st_autorefresh(interval=10000, key="guvenlik_yenileme")

        islemde_olanlar = df[df["Durum"] == "İşlemde"]
        islemde_sayisi = len(islemde_olanlar)

        col_trafik, col_iletisim = st.columns([2, 1])

        with col_trafik:
            st.markdown("### 🚦 Giriş Durumu")
            if islemde_sayisi >= MAX_ICERI_KAPASITE:
                st.markdown(
                    f"""
                    <div style="background-color:#ff4b4b; padding:25px; border-radius:12px; text-align:center;">
                        <h1 style="color:white; margin:0;">🔴 İÇERİSİ YOĞUN!</h1>
                        <p style="color:white; font-size:18px; margin-top:8px;">İçeride {islemde_sayisi} kurye var. Yenileri kapıda bekletin.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div style="background-color:#2bab4d; padding:25px; border-radius:12px; text-align:center;">
                        <h1 style="color:white; margin:0;">🟢 İÇERİ ALABİLİRSİNİZ</h1>
                        <p style="color:white; font-size:18px; margin-top:8px;">İçeride müsait masa var. Yönlendirme yapın.</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_iletisim:
            st.markdown("### 📻 Telsiz / İnterkom")
            with st.form("telsiz_formu_g", clear_on_submit=True):
                telsiz_mesaj = st.text_input("Ofise Mesaj Gönder:", placeholder="Örn: Sıra 005 gelsin mi?")
                gonder_btn = st.form_submit_button("Anons Et 🎤", use_container_width=True)
                if gonder_btn and telsiz_mesaj.strip() != "":
                    mesaj_kaydet("Güvenlik", telsiz_mesaj.strip())
                    st.toast("Mesaj iletildi!", icon="🚀")

            df_m_g = mesajlari_yukle()
            if not df_m_g.empty:
                st.markdown("**Son Telsiz Akışı:**")
                with st.container(height=180, border=True):
                    for _, m_row in df_m_g.iloc[::-1].iterrows():
                        if m_row["Kimden"] == "Ofis":
                            st.markdown(f"🟢 **[Ofis - {m_row['Saat']}]:** {m_row['Mesaj']}")
                        else:
                            st.markdown(f"👤 *[Siz - {m_row['Saat']}]:* {m_row['Mesaj']}")

        st.markdown("---")

        if not islemde_olanlar.empty:
            st.markdown("### 📢 Anlık Masa Yönlendirme Bildirimleri")
            for _, row in islemde_olanlar.iterrows():
                st.info(
                    f"🔔 **{row['Yönlendirilen'].upper()}**, {row['Sıra No']:03d} sıra numaralı "
                    f"**{row['Adı Soyadı']}** kuryesini işleme aldı! Lütfen içeriye yönlendiriniz."
                )
            st.markdown("---")

        st.subheader("📋 Güncel Sıra Akış Listesi")
        gosterilecek_akistan = df[df["Durum"].isin(["Bekliyor", "İşlemde"])].sort_values(by="Sıra No")

        if not gosterilecek_akistan.empty:
            st.dataframe(
                gosterilecek_akistan[
                    ["Sıra No", "Adı Soyadı", "Plaka", "Geliş Nedeni", "Saat", "Durum", "Yönlendirilen"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Şu anda sırada bekleyen veya işlemde olan aktif kurye bulunmuyor.")

# --- 3. EKRAN: OFİS YÖNETİM PANELİ ---
elif ekran_modu == "Ofis Yönetim Paneli":
    st.title("📊 Ofis Sıra Yönetim Paneli")
    sifre = st.text_input("Yönetici Şifresini Giriniz:", type="password", key="m_sifre_input")

    if sifre != "filo123":
        st.error("🔒 Bu alana erişmek için yetkiniz yok. Lütfen doğru şifreyi giriniz.")
    else:
        st.success("🔓 Giriş Başarılı.")
        st_autorefresh(interval=10000, key="yonetim_yenileme")

        df_mesajlar = mesajlari_yukle()
        with st.container(border=True):
            st.markdown("### 🚨 Kapı Telsiz İstasyonu")
            c_akisz, c_cevapz = st.columns([2, 1])

            with c_akisz:
                if not df_mesajlar.empty:
                    son_mesaj = df_mesajlar.iloc[-1]
                    if son_mesaj["Kimden"] == "Güvenlik":
                        st.warning(f"📩 **Son Güvenlik Çağrısı ({son_mesaj['Saat']}):** {son_mesaj['Mesaj']}")

                    st.markdown("**Tüm Telsiz Geçmişi (Bugün):**")
                    with st.container(height=150):
                        for _, m_row in df_mesajlar.iloc[::-1].iterrows():
                            if m_row["Kimden"] == "Güvenlik":
                                st.markdown(f"🔴 **[Güvenlik - {m_row['Saat']}]:** {m_row['Mesaj']}")
                            else:
                                st.markdown(f"👤 *[Ofis Cevap - {m_row['Saat']}]:* {m_row['Mesaj']}")
                else:
                    st.info("Telsiz hattı sakin. Gelen anons bulunmuyor.")

            with c_cevapz:
                with st.form("ofis_cevap_formu", clear_on_submit=True):
                    cevap_metni = st.text_input("Güvenliğe Cevap Yaz:", placeholder="Örn: Tamam kanka içeri al.")
                    cevap_btn = st.form_submit_button("Telsizden Cevapla 📻", use_container_width=True)
                    if cevap_btn and cevap_metni.strip() != "":
                        mesaj_kaydet("Ofis", cevap_metni.strip())
                        st.rerun()

                if st.button("🗑️ Telsiz Geçmişini Sıfırla", use_container_width=True, type="secondary"):
                    mesajlari_temizle()
                    st.rerun()

        st.markdown("---")

        toplam_gelen = len(df)
        bekleyen = len(df[df["Durum"] == "Bekliyor"])
        islemde = len(df[df["Durum"] == "İşlemde"])
        tamamlanan = len(df[df["Durum"] == "Tamamlanan"])

        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("🔄 Manuel Yenile", use_container_width=True):
                st.rerun()
        with col_btn2:
            if st.button("🗓️ Günü Kapat ve Excel'e Arşivle", type="secondary", use_container_width=True):
                if not df.empty:
                    kaydedilen_yol = masaustune_excel_kaydet(df)
                    if kaydedilen_yol:
                        st.success(f"📂 Rapor arşivlendi! Aşağıdaki butondan indirebilirsiniz.")
                else:
                    st.warning("⚠️ Bugün henüz hiç sıra alınmamış, raporlanacak veri yok.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Gelen", toplam_gelen)
        m2.metric("Bekleyen", bekleyen)
        m3.metric("İşlemde", islemde)
        m4.metric("Tamamlanan", tamamlanan)

        st.markdown("---")
        st.subheader("⏳ Güncel Sıra Akışı (Bekleyenler ve İşlemdekiler)")

        gosterilecekler = df[df["Durum"].isin(["Bekliyor", "İşlemde"])]

        if not gosterilecekler.empty:
            for index, row in gosterilecekler.iterrows():
                with st.container(border=True):
                    c_info, c_action = st.columns([3, 2])

                    with c_info:
                        durum_rengi = "🔴" if row["Durum"] == "Bekliyor" else "🟡"
                        st.markdown(
                            f"### {durum_rengi} {row['Sıra No']:03d} <span style='font-size:14px; background-color:gray; color:white; padding:2px 6px; border-radius:4px;'>{row['Durum']}</span>",
                            unsafe_allow_html=True)
                        st.markdown(f"**Kurye:** {row['Adı Soyadı']} ({row['Plaka']})")
                        st.markdown(f"**Geliş Nedeni:** {row['Geliş Nedeni']} | **Saat:** {row['Saat']}")
                        if row["Durum"] == "İşlemde":
                            st.info(f"🏃 İşlem Üstlenen: {row['Yönlendirilen']}")

                    with c_action:
                        if row["Durum"] == "Bekliyor":
                            ustlenen = st.selectbox(
                                "İşlemi Üstlenen:",
                                ["Eren", "Sabri", "Batuhan"],
                                key=f"ust_{row['Sıra No']}"
                            )

                            b1, b2 = st.columns(2)
                            if b1.button("📢 Çağır / İşleme Al", key=f"cagir_{row['Sıra No']}", type="primary"):
                                df.loc[df["Sıra No"] == row["Sıra No"], "Durum"] = "İşlemde"
                                df.loc[df["Sıra No"] == row["Sıra No"], "Yönlendirilen"] = ustlenen
                                veri_kaydet(df)
                                st.rerun()

                            if b2.button("❌ İptal Et", key=f"iptal_{row['Sıra No']}"):
                                df.loc[df["Sıra No"] == row["Sıra No"], "Durum"] = "İptal Edildi"
                                veri_kaydet(df)
                                st.rerun()

                        elif row["Durum"] == "İşlemde":
                            if st.button("✅ İşlemi Tamamla (Çıkış)", key=f"bitir_{row['Sıra No']}",
                                         use_container_width=True):
                                df.loc[df["Sıra No"] == row["Sıra No"], "Durum"] = "Tamamlanan"
                                veri_kaydet(df)
                                st.rerun()
        else:
            st.info("Şu anda sırada bekleyen veya işlemde olan kurye bulunmuyor.")
