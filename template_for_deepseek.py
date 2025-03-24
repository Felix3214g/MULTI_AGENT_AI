from together import Together

# Initialize the Together client with your API key
client = Together(api_key="3405ce428ec69a2cf4c9f128064e9bc367b630fafc5968d2eff6bbdfaa462067")

def get_ai_response(prompt):
    """Function to get response from DeepSeek V3"""
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}]
        )
        
        if response and response.choices:
            return response.choices[0].message.content
        else:
            return "No response received from the API"
            
    except Exception as e:
        return f"Error occurred: {e}"

# Example usage
if __name__ == "__main__":
    user_prompt = "What is the meaning of life?"
    ai_response = get_ai_response(user_prompt)
    print(ai_response) 