"""
🛠️ Workspace Utilities - Helper Functions
For testing cross-file analysis capabilities
"""

def format_string(text: str) -> str:
    """Format string with proper capitalization"""
    return text.strip().capitalize()

def calculate_sum(numbers: list) -> int:
    """Calculate sum of numbers list"""
    return sum(numbers)

class StringHelper:
    """Helper class for string operations"""
    
    def __init__(self):
        self.processed_count = 0
    
    def clean_text(self, text: str) -> str:
        """Clean and process text"""
        self.processed_count += 1
        return text.strip().lower().replace('  ', ' ')
    
    def get_word_count(self, text: str) -> int:
        """Count words in text"""
        return len(text.split())

def validate_email(email: str) -> bool:
    """Simple email validation"""
    return '@' in email and '.' in email

# Math utilities
def factorial(n: int) -> int:
    """Calculate factorial"""
    if n <= 1:
        return 1
    return n * factorial(n - 1)