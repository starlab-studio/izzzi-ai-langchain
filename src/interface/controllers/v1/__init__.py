from . import analysis_controller, chatbot_controller, search_controller, feedback_controller

# Expose routers with shorter names
analysis = analysis_controller
chatbot = chatbot_controller
search = search_controller
feedback = feedback_controller

__all__ = ["analysis", "chatbot", "search", "feedback"]

