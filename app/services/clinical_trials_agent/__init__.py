from app.services.template_manager import JinjaTemplateManager

template_manager = JinjaTemplateManager("./app/services/clinical_trials_agent/prompts")
GPT_41_MINI = "gpt-4.1-mini"
__all__ = ["GPT_41_MINI", "template_manager"]
