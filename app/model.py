import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

logger = logging.getLogger("qwen_api.model")

class QwenModelService:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = os.getenv("MODEL_NAME", "qwen-compliance")
        
    def load_model(self):
        """
        Loads the base Qwen model and attaches the fine-tuned LoRA adapter once at startup.
        """
        model_path = os.getenv("MODEL_PATH", ".")
        base_model_name = os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")

        # Resolve absolute path for clarity in logs
        abs_model_path = os.path.abspath(model_path)

        logger.info(f"Initializing Qwen model service on device: {self.device.upper()}")
        logger.info(f"Base model: {base_model_name}")
        logger.info(f"LoRA adapter directory: {abs_model_path}")

        # 1. Load Tokenizer
        try:
            logger.info(f"Attempting to load tokenizer from adapter directory: {abs_model_path}")
            self.tokenizer = AutoTokenizer.from_pretrained(abs_model_path, trust_remote_code=True)
        except Exception as err:
            logger.warning(f"Could not load tokenizer from {abs_model_path} ({err}). Loading from base model {base_model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 2. Load Base Causal Language Model
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        logger.info(f"Loading base model '{base_model_name}' (dtype: {torch_dtype})...")
        
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch_dtype,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )

        if self.device == "cpu":
            base_model = base_model.to("cpu")

        # 3. Attach LoRA Adapter if present
        adapter_config_file = os.path.join(abs_model_path, "adapter_config.json")
        if os.path.exists(adapter_config_file):
            logger.info(f"Found LoRA adapter config at '{adapter_config_file}'. Attaching adapter...")
            try:
                self.model = PeftModel.from_pretrained(base_model, abs_model_path)
                logger.info("LoRA adapter successfully attached to base model.")
            except Exception as e:
                logger.error(f"Failed to attach LoRA adapter from {abs_model_path}: {e}")
                raise e
        else:
            logger.warning(f"No adapter_config.json found at '{abs_model_path}'. Running with base model directly.")
            self.model = base_model

        self.model.eval()
        logger.info("Qwen fine-tuned model loading complete and ready to serve requests!")

    def generate_answer(self, user_message: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
        """
        Generates a compliance response for the user's message using the loaded model.
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model service is not loaded. Ensure load_model() was called on startup.")

        system_prompt = (
            "You are an expert cybersecurity compliance AI assistant. "
            "Provide accurate, authoritative, and concise answers regarding frameworks like "
            "NIST SP 800-53, CIS Controls, ISO 27001, and STIG Baselines."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # Use chat template if supported
        if hasattr(self.tokenizer, "apply_chat_template") and self.tokenizer.chat_template:
            prompt_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            prompt_text = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"

        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature if temperature > 0 else 0.1,
                do_sample=True if temperature > 0 else False,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Extract generated response excluding input prompt tokens
        generated_tokens = outputs[0][inputs.input_ids.shape[-1]:]
        answer = self.tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()
        return answer
