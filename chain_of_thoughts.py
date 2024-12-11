import asyncio
import json
import logging
from typing import List, Dict, Any
import numpy as np
import tensorflow as tf
from datetime import datetime

from web_search import AdvancedWebSearcher

class ChainOfThoughtsSystem:
    def __init__(self, max_reasoning_steps=10, ai_caller=None):
        """
        Initialize Chain of Thoughts reasoning system
        
        Args:
            max_reasoning_steps (int): Maximum number of reasoning steps
            ai_caller (callable, optional): Function to call AI for reasoning
        """
        self.web_searcher = AdvancedWebSearcher()
        self.max_reasoning_steps = max_reasoning_steps
        self.logger = logging.getLogger(__name__)
        
        # Store AI caller for reasoning
        self.ai_caller = ai_caller
        
        # Reasoning history tracking
        self.reasoning_history = []
        
        # Reward model for evaluating reasoning quality
        self.reward_model = self._build_reward_model()
    
    def _build_reward_model(self):
        """
        Build a simple neural network to evaluate reasoning quality
        
        Returns:
            tf.keras.Model: Reward evaluation model
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(100,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam', 
            loss='binary_crossentropy', 
            metrics=['accuracy']
        )
        
        return model
    
    async def generate_chain_of_thoughts(self, initial_query: str) -> Dict[str, Any]:
        """
        Generate a comprehensive chain of thoughts using web search and reasoning
        
        Args:
            initial_query (str): The initial problem or query to reason about
        
        Returns:
            Dict containing reasoning steps, confidence, and final conclusion
        """
        self.reasoning_history = []
        current_context = initial_query
        
        for step in range(self.max_reasoning_steps):
            # Step 1: Web Search for Context
            web_results = self.web_searcher.web_search(current_context, max_results=5)
            
            # Step 2: Extract Key Information
            key_insights = self._extract_key_insights(web_results)
            
            # Step 3: Reasoning Step
            reasoning_step = await self._perform_reasoning_step(current_context, key_insights)
            
            # Step 4: Update Context
            current_context = reasoning_step['conclusion']
            
            # Step 5: Store Reasoning Step
            self.reasoning_history.append(reasoning_step)
            
            # Step 6: Evaluate Reasoning Quality
            step_reward = self._evaluate_reasoning_step(reasoning_step)
            
            # Optional: Break if high confidence or convergence
            if step_reward > 0.8 or step_reward < 0.2:
                break
        
        # Final Evaluation
        final_conclusion = self._synthesize_conclusion()
        
        return {
            "initial_query": initial_query,
            "reasoning_steps": self.reasoning_history,
            "final_conclusion": final_conclusion,
            "total_steps": len(self.reasoning_history)
        }
    
    def _extract_key_insights(self, web_results: List[Dict]) -> List[str]:
        """
        Extract key insights from web search results
        
        Args:
            web_results (List[Dict]): Web search results
        
        Returns:
            List of key insights
        """
        insights = []
        for result in web_results:
            insights.append(result.get('snippet', ''))
        return insights[:3]  # Limit to top 3 insights
    
    async def _perform_reasoning_step(self, context: str, insights: List[str]) -> Dict:
        """
        Perform a single reasoning step
        
        Args:
            context (str): Current reasoning context
            insights (List[str]): Web search insights
        
        Returns:
            Dict representing a reasoning step
        """
        # Prepare reasoning prompt
        reasoning_prompt = f"""
        Reasoning Context: {context}
        Web Insights: {' | '.join(insights)}

        Perform a systematic reasoning step:
        1. Analyze the current context
        2. Integrate web insights
        3. Generate a logical conclusion
        4. Identify potential next reasoning directions

        Provide a concise, clear, and insightful response.
        """
        
        # Use AI caller for reasoning (must be provided during initialization)
        if not self.ai_caller:
            raise ValueError("AI caller must be provided for reasoning")
        
        conclusion = await self.ai_caller(reasoning_prompt)
        
        return {
            "context": context,
            "insights": insights,
            "conclusion": conclusion,
            "reasoning_type": "web_integrated"
        }
    
    def _evaluate_reasoning_step(self, reasoning_step: Dict) -> float:
        """
        Evaluate the quality of a reasoning step
        
        Args:
            reasoning_step (Dict): A single reasoning step
        
        Returns:
            float: Reward/confidence score (0-1)
        """
        # Convert reasoning step to numerical representation
        input_vector = self._preprocess_reasoning_step(reasoning_step)
        
        # Predict reward using the reward model
        reward = self.reward_model.predict(input_vector.reshape(1, -1))[0][0]
        
        return float(reward)
    
    def _preprocess_reasoning_step(self, reasoning_step: Dict) -> np.ndarray:
        """
        Convert reasoning step to numerical vector
        
        Args:
            reasoning_step (Dict): Reasoning step to preprocess
        
        Returns:
            np.ndarray: Numerical representation
        """
        # Simple preprocessing - you'd want more sophisticated feature extraction
        features = [
            len(reasoning_step.get('context', '')),
            len(reasoning_step.get('conclusion', '')),
            len(' '.join(reasoning_step.get('insights', []))),
        ]
        
        # Pad or truncate to fixed size
        features += [0] * (100 - len(features))
        return np.array(features[:100], dtype=np.float32)
    
    def _synthesize_conclusion(self) -> str:
        """
        Synthesize final conclusion from reasoning history
        
        Returns:
            str: Synthesized conclusion
        """
        if not self.reasoning_history:
            return "No conclusive reasoning could be performed."
        
        # Take the last reasoning step's conclusion
        return self.reasoning_history[-1].get('conclusion', 'Inconclusive')
    
    def save_reasoning_trace(self, filename: str = 'reasoning_trace.json'):
        """
        Save reasoning trace to a file
        
        Args:
            filename (str): File to save reasoning trace
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "reasoning_history": self.reasoning_history,
                    "timestamp": str(datetime.now())
                }, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Reasoning trace saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving reasoning trace: {e}")
