"""
Base Agent Class
Provides shared configuration and LLM setup for all agents
"""

from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY, GPT_MODEL, GPT_TEMPERATURE, GPT_MAX_TOKENS
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseAgent:
    """Base class for all AI agents with shared GPT-4 configuration"""
    
    def __init__(self, agent_name: str, temperature: float = GPT_TEMPERATURE):
        """
        Initialize base agent
        
        Args:
            agent_name: Name of the agent (for logging)
            temperature: GPT temperature (0-1)
        """
        self.agent_name = agent_name
        self.temperature = temperature
        
        # Initialize ChatGPT model
        if not OPENAI_API_KEY:
            raise ValueError(f"{agent_name}: OPENAI_API_KEY not set in environment")
        
        self.llm = ChatOpenAI(
            model=GPT_MODEL,
            temperature=temperature,
            max_tokens=GPT_MAX_TOKENS,
            api_key=OPENAI_API_KEY
        )
        
        logger.info(f"{agent_name} initialized with {GPT_MODEL} (temp={temperature})")
    
    def get_llm(self):
        """Get the LLM instance"""
        return self.llm
