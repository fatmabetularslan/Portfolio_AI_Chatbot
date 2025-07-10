import streamlit as st

def copy_button(text: str, label: str = "Copy to clipboard", key: str = "copy_button", tooltip: str = ""):
    """
    Streamlit arayüzüne bir kopyalama butonu ekler.

    Args:
        text (str): Kopyalanacak metin.
        label (str): Buton etiketi.
        key (str): Streamlit bileşeni için anahtar (aynı anda birden fazla kopya butonu varsa farklı olmalı).
        tooltip (str, optional): Butonun üzerine gelindiğinde gösterilecek açıklama.
    """

    st.text_area("Kopyalanacak metin:", value=text, height=100, key=f"{key}_text", disabled=True)
    
    # Tooltip desteği
    tooltip_attr = f' title="{tooltip}"' if tooltip else ''
    
    copy_code = f'''
    <textarea id="{key}" style="position:absolute; left:-9999px;">{text}</textarea>
    <script>
    function copyToClipboard() {{
        var copyText = document.getElementById("{key}");
        copyText.select();
        document.execCommand("copy");
    }}
    </script>
    <button onclick="copyToClipboard()"{tooltip_attr}>{label}</button>
    '''
    
    st.markdown(copy_code, unsafe_allow_html=True)
