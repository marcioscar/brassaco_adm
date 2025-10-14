import streamlit as st
import dropbox
from dropbox.files import WriteMode
from datetime import datetime

# === CONFIGURE SEU TOKEN AQUI ===
# IMPORTANTE: Para que o upload funcione, você precisa:
# 1. Ir para https://www.dropbox.com/developers/apps
# 2. Encontrar seu app (ID: 7187777)
# 3. Na aba "Permissions", marcar:
#    - "files.content.write" ✅
#    - "sharing.write" ✅
# 4. Na aba "Settings", gerar um novo access token
# 5. Substituir o token abaixo pelo novo token gerado

DROPBOX_ACCESS_TOKEN = 'sl.u.AFx7rnPIjESDVOkTBJDgdQz6XVGiEoOTURr12rpNZpmzQejXotn1IuOG7ihGYQQTER5AvsK82RL-yc2RtynNlKt_Abo7X5GxWERESqI-YoOApvZ3yRa8SWeSP9ojjTne0fgtqMV6rMS2z7SVj2P9ukR3hv9ACWKYvuMM6eovVPt9Brbjrfdjo7d0szNa3babyxmd8EGNoe3u1wy6Dse3J1FNQ2m76CsfcCMf1wq0ZhgFY_Km-ZeOG1DNn18qqQoj0ZvAYM6rUDJku5TW9fNeNBaDrxKhJ5_LgaVDRmnvQD-BhDoz__EpGAmaNwunrZ-MNsrGvSLfJ5ngS4yPg5fdZBUNw98VcwaYqW7k9LnRU2OZaRmPTjpVD-zNVm5R94wsxMHzoGYRNWLdFPEKW_Q-zG3JMJ23jBS8PEXNS-3udJ6GzDi_nzRQkz06Md3CuXsJMLNJQmPYwUBVVfRsRJ0oDJcHTOkUXVEpqmcYbiKqpxSPxDyh4LjYqo9kDRbj02Dp1_9O0vObdNcPaRs3NImMHEI11X2TsDspo-lf0EAX4iOWfHs5tqaMGqVr3gJzeLT3AOPRz1S6rXXLdHxLa8Kkv2-up9wVlaWAOv_z_IThiGtP4Cvu6Mppd4ajx71-xbj13QYno9F30hh-dZG6a5qmkc7x95ld_TblaFnsGQdWG2lO9dh1F4V_jSTzvrmXVgVKlBKcaBbUDmCdHpTytRbEIFWs72_i7Bo1UB_1YsgD1XVxoqZ45XEfYpHGdPgwDKJL3is3b7b100qdPiBJ5_BHkfys2gMtkNgqmOWtrw-lGQ9trfsI7Keqz5H2HvMiqfJ7wk8CDfxoPoX8m6hZeuCIs2MGs5YzZTGJPXaEi7LzGeSe7iPW-3B8BoTPlkrgLozDVyLEpvYt5UH41kZ9DJy3hUfBKWBLEVmJInfbURJ--YTn1NXsuo6aq8waU7HnGA64saM0uejmgrobaZrnrPzRaaHOtZqU5N9ZEZYBJuujdrZa-WMkO0ncl7nEybfMx0pAmJC6PP2NkjP6nk5KXMsmhR4ssd1rrgiNXq9a9iv3C2NrZzlzNOksOh8C6H617yQ-cwoLEZHwm-JZEn6vrIWJCD4K63bGM09irBURHOmF_H5ZKBJk4_8pmFk9TnD4D7mYPNbXl1_48msgu9WRunfqqrIjTIc2SCADFJcy_3DSQESr2-wiAGEXNgNaUNeMDCaav9MW6HXwXKHivB1_MzfVIZS2WKjOEdFz-MORfjD4v663Y_JDElLbuG2IPLb5Nwxw5r3EtaVq-TujJMtX5Run43iH'

def upload_to_dropbox(file, filename):
    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        
        # Verificar se o token tem as permissões necessárias
        try:
            dbx.users_get_current_account()
        except dropbox.exceptions.AuthError as e:
            st.error(f"Erro de autenticação: {e}")
            st.info("Verifique se o token tem as permissões corretas no Dropbox App Console")
            return None
        
        # Nome único para o arquivo
        nome_arquivo = f"{datetime.now().strftime('%d-%m-%Y')}_{filename}"
        dropbox_path = f'/comprovantes/{nome_arquivo}'
        
        # Resetar o ponteiro do arquivo
        file.seek(0)
        
        # Upload
        dbx.files_upload(file.read(), dropbox_path, mode=WriteMode("overwrite"))
        
        # Criar link compartilhado
        shared_link = dbx.sharing_create_shared_link_with_settings(dropbox_path)
        return shared_link.url.replace("?dl=0", "?dl=1")  # link direto para download
        
    except dropbox.exceptions.AuthError as e:
        st.error(f"Erro de autenticação: {e}")
        st.info("Verifique se o token tem a permissão 'files.content.write' no Dropbox App Console")
        return None
    except Exception as e:
        st.error(f"Erro ao fazer upload para o Dropbox: {str(e)}")
        return None

# === INTERFACE STREAMLIT ===
st.title("Upload para Dropbox")

uploaded_file = st.file_uploader("Escolha um arquivo", type=None)

if uploaded_file:
    st.write(f"Enviando arquivo: {uploaded_file.name}")
    link = upload_to_dropbox(uploaded_file, uploaded_file.name)
    
    if link:
        st.success("Arquivo enviado com sucesso!")
        st.markdown(f"[🔗 Clique aqui para acessar o arquivo]({link})")