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
    if "paymentrouter" in service_name.lower():
        return "ERROR: Service 'PaymentRouter' not found in registry."
    return "Service is Operational."