import pandas as pd
import os

# Function to translate text
def translate_text(text, translator):
    try:
        print(f"Translating: {text}")
        translated = translator.translate(text, src="en", dest="fr")
        print(f"Translated: {translated.text}")
        return translated.text
    except Exception as e:
        print(f"Error translating text: {e}")
        return text


# Main function
def translate_csv(file_path):
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Check if 'name' column exists
        if 'productName' not in df.columns:
            print("Error: 'name' column not found in the CSV file.")
            return

        # Translate the 'name' column
        from googletrans import Translator
        translator = Translator()

        df['productName'] = df['productName'].apply(lambda x: translate_text(x, translator))

        # Save to a new CSV file
        base, ext = os.path.splitext(file_path)
        new_file_path = f"{base}_translated{ext}"
        df.to_csv(new_file_path, index=False)
        print(f"Translated CSV saved as {new_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
file_path = input("Enter the path to the CSV file: ")
translate_csv(file_path)
