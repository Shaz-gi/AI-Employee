import sys
sys.path.insert(0, 'src')

from ai_linkedin_generator import AILinkedinGenerator

print("Testing AI LinkedIn Generator...")
g = AILinkedinGenerator('AI_Employee_Vault')

print(f"Client: {g.client}")
print(f"AI Client: {g.ai_client}")

if g.ai_client:
    print("\nGenerating post...")
    result = g.generate_post_with_ai('insight')
    print(f"Result: {result[:200] if result else 'None'}")
else:
    print("AI not configured!")
