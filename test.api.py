from together import Together

client = Together(api_key="3405ce428ec69a2cf4c9f128064e9bc367b630fafc5968d2eff6bbdfaa462067")

try:
  response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3",
    messages=[{"role": "user", "content": "What is the meaning of life?"}],
  )
  
  print(response)  # Print the full response for debugging
  
  if response and response.choices:
    print(response.choices[0].message.content)
  else:
    print("No response received from the API")
    
except Exception as e:
  print(f"Error occurred: {e}")
