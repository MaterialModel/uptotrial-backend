from app.services.template_manager import JinjaTemplateManager

template_manager = JinjaTemplateManager("./app/services/clinical_trials_agent/prompts")
__all__ = ["template_manager"]
