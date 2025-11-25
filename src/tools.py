from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """
    Useful for performing mathematical calculations. 
    Input should be a mathematical expression string (e.g., '200 + 500', '600 * 0.5').
    """
    try:
        # Safety: In production, use a safe math parser, not eval
        return str(eval(expression))
    except Exception as e:
        return f"Error calculating: {str(e)}"

@tool
def check_system_status(service_name: str) -> str:
    """
    Checks the status of a specific internal service.
    Use this if the user asks about 'PaymentRouter' or 'AuthService'.
    """
    # Simulating the "Missing Data" challenge
    import random
    if random.random() > 0.7:  # Simulate a 30% chance of failure
        return f"The '{service_name}' service is currently experiencing an outage. Our team has been notified and is working to resolve the issue."
    else:
        return f"The '{service_name}' service is operating normally. You may continue with your task."
