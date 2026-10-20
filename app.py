from datetime import datetime, timedelta, timezone
import json
import os
import streamlit as st

st.set_page_config(
    page_title="Glicemia & Insulina", page_icon="🩸", layout="centered"
)

CONFIG_FILE = "config_glicemia.json"

DEFAULT_CONFIG = {
    "glicemia_alvo": 100.0,
    "fator_sensibilidade": 50.0,
    "ic_por_hora": {f"{h:02d}h - {h+1:02d}h": 10.0 for h in range(24)},
}


def carregar_config():
  if os.path.exists(CONFIG_FILE):
    try:
      with open(CONFIG_FILE, "r") as f:
        return json.load(f)
    except Exception:
      return DEFAULT_CONFIG
  return DEFAULT_CONFIG


def salvar_config(config):
  with open(CONFIG_FILE, "w") as f:
    json.dump(config, f, indent=4)


if "config" not in st.session_state:
  st.session_state["config"] = carregar_config()

config = st.session_state["config"]

st.title("🩸 Calculadora Rápida")

# --- AJUSTE DE FUSO HORÁRIO (Horário do Brasil / Brasília) ---
fuso_brasil = timezone(timedelta(hours=-3))
agora_local = datetime.now(fuso_brasil)
hora_atual_int = agora_local.hour
faixa_atual = f"{hora_atual_int:02d}h - {hora_atual_int+1:02d}h"

# --- REGISTRO PRINCIPAL ---
with st.form("form_celular"):
  st.markdown("### 📝 Nova Medição")

  glicemia_atual = st.number_input(
      "Glicemia Atual (mg/dL)", min_value=0, max_value=600, value=140, step=1
  )

  carboidratos = st.number_input(
      "Carboidratos a consumir (g)",
      min_value=0.0,
      max_value=300.0,
      value=0.0,
      step=5.0,
  )

  lista_horarios = list(config["ic_por_hora"].keys())
  horario_selecionado = st.selectbox(
      "Horário da Refeição", options=lista_horarios, index=hora_atual_int
  )

  ic_aplicado = config["ic_por_hora"].get(horario_selecionado, 10.0)
  st.caption(
      f"💡 Relação IC automática para este horário: **{ic_aplicado} g/UI**"
  )

  submitted = st.form_submit_button(
      "🚀 Calcular Dose", use_container_width=True
  )

if submitted:
  glicemia_alvo = config["glicemia_alvo"]
  fator_sensibilidade = config["fator_sensibilidade"]

  diferenca = glicemia_atual - glicemia_alvo
  dose_correcao = diferenca / fator_sensibilidade if diferenca > 0 else 0.0

  if diferenca < 0:
    st.warning("⚠️ Glicemia abaixo do alvo! Cuidado com hipoglicemia.")

  dose_refeicao = carboidratos / ic_aplicado if ic_aplicado > 0 else 0.0
  dose_total = max(0.0, dose_correcao + dose_refeicao)

  # --- CAMPO EM DESTAQUE COM A DOSE CORRETA ---
  st.markdown(
      f"""
        <div style="background-color:#d4edda; padding:15px; border-radius:10px; border: 1px solid #c3e6cb; text-align:center; margin-bottom: 15px;">
            <h4 style="color:#155724; margin:0 0 5px 0;">💉 Tome exatamente:</h4>
            <h1 style="color:#155724; font-size:42px; margin:0;">{dose_total:.2f} UI</h1>
            <p style="color:#155724; margin:5px 0 0 0; font-size:14px;">Correção: {dose_correcao:.2f} UI | Refeição: {dose_refeicao:.2f} UI</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

# --- CONFIGURAÇÕES ---
with st.expander("⚙️ Ajustes e Alvos (Alvo, FS e IC por Hora)"):
  novo_alvo = st.number_input(
      "Glicemia Alvo Padrão (mg/dL)",
      min_value=50.0,
      max_value=200.0,
      value=float(config["glicemia_alvo"]),
  )
  novo_fs = st.number_input(
      "Fator de Sensibilidade (FS)",
      min_value=1.0,
      max_value=200.0,
      value=float(config["fator_sensibilidade"]),
  )

  st.markdown("#### Relação IC por Hora")
  novos_ics = {}
  for h_str, val in config["ic_por_hora"].items():
    novos_ics[h_str] = st.number_input(
        f"{h_str}", min_value=1.0, max_value=100.0, value=float(val), step=0.5
    )

  if st.button("💾 Salvar Alterações", use_container_width=True):
    config["glicemia_alvo"] = novo_alvo
    config["fator_sensibilidade"] = novo_fs
    config["ic_por_hora"] = novos_ics
    st.session_state["config"] = config
    salvar_config(config)
    st.success("Configurações atualizadas!")
    st.rerun()
