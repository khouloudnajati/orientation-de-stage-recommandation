import streamlit as st
import json
import time

from orchestrateur import Orchestrateur

# Configuration de la page
st.set_page_config(
    page_title="Amal - Conseillère d'Orientation IA",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Personnalisé pour une interface plus belle ---
st.markdown("""
<style>
    /* Custom Styling for Streamlit */
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        text-align: center;
        color: #2c3e50;
        font-family: 'Inter', sans-serif;
        padding-bottom: 2rem;
    }
    .chat-container {
        background-color: white;
        border-radius: 10px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #3498db;
    }
    .rec-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-top: 4px solid #2ecc71;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialisation de la Session State ---
if "orch" not in st.session_state:
    with st.spinner("🤖 Initialisation de l'Intelligence Artificielle..."):
        st.session_state.orch = Orchestrateur()

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Démarrer l'entretien avec Amal
    msg_initial = st.session_state.orch.profileur.demarrer_entretien()
    st.session_state.messages.append({"role": "assistant", "content": msg_initial})

if "profil_complet" not in st.session_state:
    st.session_state.profil_complet = False

if "recommandations" not in st.session_state:
    st.session_state.recommandations = None
    st.session_state.message_coach = None
    st.session_state.profil = None

# --- En-tête ---
st.markdown("<h1 class='main-header'>🎓 Amal - Votre Conseillère d'Orientation IA</h1>", unsafe_allow_html=True)

# --- SECTION 1 : Le Chat de Profilage ---
if not st.session_state.profil_complet:
    st.info("Discutez avec Amal pour qu'elle comprenne votre profil et vos envies.")
    
    # Afficher l'historique
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🎓" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
            
    # Input utilisateur
    if prompt := st.chat_input("Votre réponse..."):
        # Afficher la réponse de l'utilisateur
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
            
        # Obtenir la réponse d'Amal
        with st.chat_message("assistant", avatar="🎓"):
            with st.spinner("Amal réfléchit..."):
                msg_agent, complet = st.session_state.orch.profileur.traiter_reponse(prompt)
                
                # Traitement spécial si le JSON de profil est généré
                if "<<<PROFIL_JSON>>>" in msg_agent:
                    msg_affiche = msg_agent.split("<<<PROFIL_JSON>>>")[0].strip()
                    if not msg_affiche:
                        msg_affiche = "Parfait ! J'ai toutes les informations nécessaires. Laisse-moi chercher les meilleures opportunités pour toi ! 🎯"
                else:
                    msg_affiche = msg_agent
                    
                st.markdown(msg_affiche)
                st.session_state.messages.append({"role": "assistant", "content": msg_affiche})
                
                if complet:
                    st.session_state.profil_complet = True
                    time.sleep(2)
                    st.rerun()

# --- SECTION 2 : Analyse et Recommandations ---
else:
    # Phase d'analyse des agents (s'exécute une seule fois)
    if not st.session_state.recommandations:
        with st.status("🔍 Traitement par les agents IA...", expanded=True) as status:
            st.write("📋 Récupération du profil...")
            profil = st.session_state.orch.profileur.obtenir_profil()
            st.session_state.profil = profil
            
            st.write("🕵️‍♂️ L'Agent Chercheur scanne les offres...")
            offres_candidates = st.session_state.orch.chercheur.rechercher(profil)
            
            st.write("⚡ L'Agent Matcher évalue la compatibilité...")
            st.session_state.orch.matcher.vector_store.indexer_offres(offres_candidates)
            top_offres = st.session_state.orch.matcher.matcher(profil, offres_candidates)
            
            st.write("💡 L'Agent Conseiller rédige vos recommandations...")
            recos = st.session_state.orch.conseiller.generer_recommandations(profil, top_offres)
            st.session_state.recommandations = recos
            
            st.write("🏋️ L'Agent Coach analyse vos axes d'amélioration...")
            coach_msg = st.session_state.orch.coach.analyser_evolution(profil, recos.get("recommandations", []))
            st.session_state.message_coach = coach_msg
            
            status.update(label="Analyse terminée avec succès ! ✅", state="complete", expanded=False)
    
    # Affichage des résultats
    if st.session_state.recommandations:
        recos = st.session_state.recommandations
        profil = st.session_state.profil
        
        # Onglets pour une navigation claire
        tab1, tab2, tab3 = st.tabs(["🎯 Offres Recommandées", "🏋️ Conseil & Coaching", "📋 Votre Profil Structuré"])
        
        with tab1:
            st.success(recos.get("message_intro", "Voici tes recommandations personnalisées !"))
            
            for rec in recos.get("recommandations", []):
                score_pct = int(rec.get("score_match", 0) * 100)
                
                # Couleur selon le score
                if score_pct >= 70:
                    color_hex = "#2ecc71" # Vert
                elif score_pct >= 50:
                    color_hex = "#f1c40f" # Jaune
                else:
                    color_hex = "#e74c3c" # Rouge
                    
                st.markdown(f"""
                <div class="rec-card" style="border-top-color: {color_hex};">
                    <h3 style="color: #2c3e50; margin-top:0;">#{rec.get('rang', '?')} - {rec.get("titre", "")} @ {rec.get('entreprise', '')}</h3>
                    <span style="background-color: {color_hex}; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold;">Score: {score_pct}%</span>
                    <p style="margin-top: 15px; font-style: italic;">{rec.get('pourquoi_correspond', '')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if rec.get("points_forts"):
                        st.markdown("**✅ Points forts**")
                        for pf in rec.get("points_forts", []):
                            st.markdown(f"- {pf}")
                with col2:
                    if rec.get("gaps"):
                        st.markdown("**📚 À développer**")
                        for gap in rec.get("gaps", []):
                            st.markdown(f"- {gap}")
                
                if rec.get("plan_action"):
                    with st.expander("🛠️ Voir le plan d'action suggéré"):
                        for action in rec.get("plan_action", []):
                            st.info(f"**{action.get('gap', '')}** : {action.get('action', '')} ({action.get('ressource', '')})")
                
                st.write("---")
                
        with tab2:
            st.markdown("### 💬 Conseil Global")
            st.info(recos.get("conseil_global", "Pas de conseil spécifique."))
            
            st.markdown("### 📌 Prochaines Étapes")
            if recos.get("prochaines_etapes"):
                for i, etape in enumerate(recos.get("prochaines_etapes", [])):
                    st.markdown(f"{i+1}. {etape}")
                    
            st.markdown("### 🏋️ Message de l'Agent Coach")
            st.warning(st.session_state.message_coach)
            
        with tab3:
            st.markdown("### 📋 Données extraites par l'IA")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"<div class='metric-card'><b>Nom :</b> {profil.get('nom', 'N/A')}</div><br>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'><b>Formation :</b> {profil.get('formation', 'N/A')} ({profil.get('niveau', 'N/A')})</div><br>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'><b>Domaine :</b> {profil.get('domaine_interet', 'N/A')}</div><br>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"<div class='metric-card'><b>Compétences Tech :</b> {', '.join(profil.get('competences_techniques', []))}</div><br>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'><b>Soft Skills :</b> {', '.join(profil.get('soft_skills', []))}</div><br>", unsafe_allow_html=True)
                st.markdown(f"<div class='metric-card'><b>Localisation :</b> {profil.get('localisation_preferee', 'N/A')}</div><br>", unsafe_allow_html=True)
            
            st.json(profil)

        if st.button("🔄 Démarrer une nouvelle session"):
            st.session_state.clear()
            st.rerun()
