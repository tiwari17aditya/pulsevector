import os
import sys
import datetime
import pathlib
from dotenv import load_dotenv
from google import genai
from googlesearch import search

# Reconfigure stdout for UTF-8 to prevent encoding errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY not found in environment.")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def get_news_search_results_with_urls(query):
    print(f"Searching for: {query}")
    results = []
    try:
        search_results = search(query, num_results=10, advanced=True)
        for result in search_results:
            results.append(f"Title: {result.title}\nURL: {result.url}\nDescription: {result.description}")
    except Exception as e:
        print(f"Search error: {e}")
    return "\n---\n".join(results)

def main():
    target_date = datetime.datetime.now()
    date_str = target_date.strftime("%d %B %Y")
    print(f"Running POC for date: {date_str}")
    
    # 1. Search news
    search_query = f"current affairs news headlines {date_str}"
    news_context = get_news_search_results_with_urls(search_query)
    
    # 2. Define the new current affairs prompt instructing to include sources and reference URLs
    ca_prompt = (
        f"Act as a Social Media and Educational expert for the 'Pulse Vector' YouTube channel to generate Current Affairs content.\n"
        f"Today is {date_str}.\n"
        f"Generate 'Daily Current Affairs {date_str}' with exactly 15 numbered points. Each point MUST be under 25 words.\n"
        f"Crucially, for each point, identify the reputable news publisher/source from the context (e.g. BBC News, Reuters, Bloomberg, Times of India, etc.) and append it at the end of the point strictly in the format: '[Source: Publisher Name]'. Do not include URL inside the point's source brackets.\n"
        f"Example: '1. Government launches new national green hydrogen mission to boost renewable energy capacity. [Source: Reuters]'\n\n"
        f"Additionally, provide YouTube metadata at the end in this order:\n"
        f"- Title: 'Daily Current Affairs {date_str}'\n"
        f"- Reel Description: A Reel Description covering top highlights (max 25 words per point) formatted as 'Catch the top... [points] . . . . . [Hashtags]'\n"
        f"- Hashtags: 50 high-reach hashtags (separated by spaces, NOT as a numbered list) including popular, niche, and educational tags.\n"
        f"- Source URLs: Provide a list of the source URLs you used from the context, structured as:\n"
        f"  - Publisher Name: URL\n"
        f"Do NOT use numbers for headings, subheadings, or the hashtags list in the YouTube metadata section to avoid conflict with the current affairs points."
    )
    
    full_prompt = f"{ca_prompt}\n\nContext Data:\n{news_context}"
    
    model_name = 'gemini-2.5-flash'
    print(f"Sending request to Gemini model {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt
        )
        output_text = response.text
        
        output_dir = pathlib.Path("POC")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "sample_output_v1_3_0.txt"
        
        output_file.write_text(output_text, encoding='utf-8')
        print(f"\nSuccess! POC output generated and saved to: {output_file.absolute()}")
        print("\n--- Preview of Output ---")
        print(output_text[:1000] + "\n...")
    except Exception as e:
        print(f"Failed to generate content: {e}")

if __name__ == "__main__":
    main()
