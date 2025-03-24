"""
Simple test script for DeepSeek V3 integration with Together API
"""
from together import Together

def test_deepseek_v3():
    """Test DeepSeek V3 integration with Together API"""
    # Initialize the Together client
    api_key = "3405ce428ec69a2cf4c9f128064e9bc367b630fafc5968d2eff6bbdfaa462067"
    client = Together(api_key=api_key)
    
    # Test prompt
    prompt = "Explain the difference between Python and JavaScript in 3 sentences."
    
    try:
        # Make the API call
        print(f"Sending request to DeepSeek V3...")
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        
        # Check and print the response
        if response and response.choices:
            print("\n--- DeepSeek V3 Response ---")
            print(response.choices[0].message.content)
            print("---------------------------")
            print("\nTest successful! DeepSeek V3 is working correctly.")
        else:
            print("\nWarning: No response received from the model.")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Test failed!")

if __name__ == "__main__":
    print("Testing DeepSeek V3 integration with Together API...")
    test_deepseek_v3() 