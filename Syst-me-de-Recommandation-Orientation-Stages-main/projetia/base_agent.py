"""
base_agent.py — Classe de base pour tous les agents du SMA
Gère les appels LLM (Gemini, OpenAI ou Anthropic selon la config).
"""

import json
from typing import Optional
import config


class BaseAgent:
    """
    Classe parente de tous les agents.
    Gère l'abstraction LLM : Gemini, OpenAI ou Anthropic selon config.LLM_PROVIDER.
    """

    def __init__(self, nom: str, system_prompt: str):
        self.nom = nom
        self.system_prompt = system_prompt
        self.historique: list[dict] = []  # mémoire de la conversation
        self._init_client()

    def _init_client(self):
        """Initialise le client LLM selon le provider configuré."""
        if config.LLM_PROVIDER == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.genai = genai
                self.model = config.GEMINI_MODEL
                self.provider = "gemini"
            except ImportError:
                raise ImportError(
                    "Installez le SDK Gemini : pip install google-generativeai"
                )

        elif config.LLM_PROVIDER == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
                self.model = config.OPENAI_MODEL
                self.provider = "openai"
            except ImportError:
                raise ImportError("Installez openai : pip install openai")

        elif config.LLM_PROVIDER == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.model = config.ANTHROPIC_MODEL
                self.provider = "anthropic"
            except ImportError:
                raise ImportError("Installez anthropic : pip install anthropic")
        else:
            raise ValueError(f"Provider inconnu : {config.LLM_PROVIDER}")

    def appeler_llm(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1500,
        tools: Optional[list] = None,
        json_mode: bool = False
    ) -> dict:
        """
        Appelle le LLM et retourne la réponse normalisée.

        Returns:
            {"content": str, "tool_calls": list | None, "raw": objet_response}
        """
        if self.provider == "gemini":
            return self._appeler_gemini(messages, temperature, max_tokens, tools, json_mode)
        elif self.provider == "openai":
            return self._appeler_openai(messages, temperature, max_tokens, tools, json_mode)
        else:
            return self._appeler_anthropic(messages, temperature, max_tokens)

    # ------------------------------------------------------------------
    # Provider Gemini
    # ------------------------------------------------------------------
    def _appeler_gemini(self, messages, temperature, max_tokens, tools, json_mode):
        """
        Appel via API Google Gemini (google-generativeai).

        Convertit l'historique OpenAI-style {role, content} vers le format
        Gemini {role: "user"|"model", parts: [...]}.
        Le system_prompt est injecté comme premier tour "user" suivi d'un
        acquittement "model" (pattern recommandé par Google pour les system prompts).
        """
        import google.generativeai as genai

        # Conversion du format messages → format Gemini
        gemini_history = []

        # Injection du system prompt comme premier échange
        gemini_history.append({
            "role": "user",
            "parts": [f"[Instructions système]\n{self.system_prompt}\n\n"
                      "Confirme que tu as bien compris tes instructions."]
        })
        gemini_history.append({
            "role": "model",
            "parts": ["Compris, je suivrai ces instructions."]
        })

        # Conversion des messages historique
        for msg in messages:
            role_gemini = "model" if msg["role"] == "assistant" else "user"
            gemini_history.append({
                "role": role_gemini,
                "parts": [msg["content"]]
            })

        # Configuration de génération
        generation_config = self.genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if json_mode:
            generation_config = self.genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",  # JSON mode natif Gemini
            )

        # Gestion du tool calling Gemini
        gemini_tools = None
        if tools:
            gemini_tools = self._convertir_tools_gemini(tools)

        # Création du modèle et appel
        model_kwargs = {
            "model_name": self.model,
            "generation_config": generation_config,
        }
        if gemini_tools:
            model_kwargs["tools"] = gemini_tools

        gemini_model = self.genai.GenerativeModel(**model_kwargs)

        # On utilise start_chat avec l'historique (sauf le dernier message = prompt actuel)
        if len(gemini_history) > 1:
            chat = gemini_model.start_chat(history=gemini_history[:-1])
            last_message = gemini_history[-1]["parts"][0]
            response = chat.send_message(last_message)
        else:
            response = gemini_model.generate_content(
                gemini_history[-1]["parts"][0] if gemini_history else ""
            )

        # Extraction du contenu et des éventuels tool calls
        content = ""
        tool_calls = None

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    content += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    # Tool call détecté
                    fc = part.function_call
                    if tool_calls is None:
                        tool_calls = []
                    tool_calls.append({
                        "name": fc.name,
                        "arguments": dict(fc.args),
                        "id": fc.name  # Gemini n'a pas d'ID unique, on utilise le nom
                    })

        return {
            "content": content,
            "tool_calls": tool_calls,
            "raw": response
        }

    def _convertir_tools_gemini(self, tools_openai: list) -> list:
        """
        Convertit les tool definitions du format OpenAI vers le format Gemini
        (FunctionDeclaration).
        """
        import google.generativeai as genai
        from google.generativeai.types import content_types

        gemini_tools = []
        for tool in tools_openai:
            if callable(tool):
                gemini_tools.append(tool)
                continue
            if getattr(tool, "get", lambda x: None)("type") != "function":
                continue
            func = tool["function"]
            params = func.get("parameters", {})

            # Conversion des propriétés
            properties = {}
            for prop_name, prop_def in params.get("properties", {}).items():
                prop_type = prop_def.get("type", "string")
                # Mapping types JSON Schema → Gemini
                type_map = {
                    "string": genai.protos.Type.STRING,
                    "integer": genai.protos.Type.INTEGER,
                    "number": genai.protos.Type.NUMBER,
                    "boolean": genai.protos.Type.BOOLEAN,
                    "array": genai.protos.Type.ARRAY,
                    "object": genai.protos.Type.OBJECT,
                }
                gemini_type = type_map.get(prop_type, genai.protos.Type.STRING)

                prop_gemini = {
                    "type_": gemini_type,
                    "description": prop_def.get("description", ""),
                }

                # Gestion des enums
                if "enum" in prop_def:
                    prop_gemini["enum"] = prop_def["enum"]

                # Gestion des arrays
                if prop_type == "array" and "items" in prop_def:
                    item_type = prop_def["items"].get("type", "string")
                    prop_gemini["items"] = genai.protos.Schema(type_=type_map.get(item_type, genai.protos.Type.STRING))

                properties[prop_name] = genai.protos.Schema(**prop_gemini)

            function_declaration = genai.protos.FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters=genai.protos.Schema(
                    type_=genai.protos.Type.OBJECT,
                    properties=properties,
                    required=params.get("required", []),
                ),
            )
            gemini_tools.append(
                genai.protos.Tool(function_declarations=[function_declaration])
            )

        return gemini_tools

    # ------------------------------------------------------------------
    # Provider OpenAI
    # ------------------------------------------------------------------
    def _appeler_openai(self, messages, temperature, max_tokens, tools, json_mode):
        """Appel via API OpenAI."""
        kwargs = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        tool_calls = None
        if msg.tool_calls:
            tool_calls = [
                {
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                    "id": tc.id
                }
                for tc in msg.tool_calls
            ]

        return {
            "content": msg.content or "",
            "tool_calls": tool_calls,
            "raw": response
        }

    # ------------------------------------------------------------------
    # Provider Anthropic
    # ------------------------------------------------------------------
    def _appeler_anthropic(self, messages, temperature, max_tokens):
        """Appel via API Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            system=self.system_prompt,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return {"content": content, "tool_calls": None, "raw": response}

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------
    def ajouter_message(self, role: str, content: str):
        """Ajoute un message à l'historique de conversation."""
        self.historique.append({"role": role, "content": content})

    def reset_historique(self):
        """Efface l'historique de la conversation."""
        self.historique = []
