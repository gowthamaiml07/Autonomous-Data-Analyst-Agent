"""Groq LLM client wrapper with true streaming and fallback handling."""
import os
import time
from typing import Optional, List, Dict, Any, Iterator
from groq import Groq
from langchain_groq import ChatGroq
from src.config import DEFAULT_GROQ_MODEL, FAST_GROQ_MODEL


class LLMClient:
    """Manages Groq LLM instances, streaming responses, and connection state."""

    @classmethod
    def get_api_key(cls, explicit_key: Optional[str] = None) -> Optional[str]:
        """Retrieve Groq API key from explicit argument, env var, or Streamlit secrets."""
        if explicit_key and explicit_key.strip():
            return explicit_key.strip()

        env_key = os.environ.get("GROQ_API_KEY")
        if env_key and env_key.strip():
            return env_key.strip()

        # Check Streamlit secrets if running inside Streamlit
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                return st.secrets["GROQ_API_KEY"].strip()
        except Exception:
            pass

        return None

    @classmethod
    def is_available(cls, explicit_key: Optional[str] = None) -> bool:
        """Check if a valid Groq API key is present."""
        key = cls.get_api_key(explicit_key)
        return bool(key and len(key) > 5 and key.startswith("gsk_"))

    @classmethod
    def test_connection(cls, explicit_key: Optional[str] = None, model_name: str = DEFAULT_GROQ_MODEL) -> Dict[str, Any]:
        """Test API key connection and measure latency."""
        key = cls.get_api_key(explicit_key)
        if not key:
            return {"success": False, "error": "No API key provided.", "latency_ms": 0}

        try:
            start_t = time.time()
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Respond with 'OK'"}],
                max_tokens=5,
                timeout=10.0
            )
            latency = int((time.time() - start_t) * 1000)
            return {
                "success": True,
                "latency_ms": latency,
                "model": model_name,
                "response": resp.choices[0].message.content.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e), "latency_ms": 0}

    @classmethod
    def call_raw(
        cls,
        messages: List[Dict[str, str]],
        explicit_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL,
        temperature: float = 0.1,
        response_format: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """Synchronous completion call to Groq client."""
        key = cls.get_api_key(explicit_key)
        if not key:
            return None

        try:
            client = Groq(api_key=key)
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "timeout": 25.0
            }
            if response_format:
                kwargs["response_format"] = response_format

            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content
        except Exception:
            return None

    @classmethod
    def stream_raw(
        cls,
        messages: List[Dict[str, str]],
        explicit_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL,
        temperature: float = 0.2
    ) -> Iterator[str]:
        """True token-by-token streaming from Groq API."""
        key = cls.get_api_key(explicit_key)
        if not key:
            return

        try:
            client = Groq(api_key=key)
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                stream=True,
                timeout=30.0
            )
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"\n\n*[Streaming encountered an issue: {str(e)}]*"

    @classmethod
    def get_chat_model(
        cls,
        explicit_key: Optional[str] = None,
        model_name: str = DEFAULT_GROQ_MODEL,
        temperature: float = 0.1,
        streaming: bool = True
    ) -> Optional[ChatGroq]:
        """LangChain ChatGroq model instance."""
        key = cls.get_api_key(explicit_key)
        if not key:
            return None

        try:
            return ChatGroq(
                groq_api_key=key,
                model_name=model_name,
                temperature=temperature,
                streaming=streaming,
                max_retries=2,
                timeout=30.0
            )
        except Exception:
            return None
