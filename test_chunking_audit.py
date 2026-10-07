"""
Standalone audit script for Stage 2: Chunking Method Audit.
Chunks a real sample document and prints each chunk's token count,
character count, and first/last 10 words to verify natural sentence boundaries.
"""

import os
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compass_project.settings')
import django
django.setup()

from compass.services.extractors import extract_document_content
from compass.services.chunker import chunk_document_text, count_tokens_exact, get_model_tokenizer

def main():
    tokenizer = get_model_tokenizer()
    print(f"=== Stage 2 Chunking Audit ===")
    print(f"Tokenizer loaded: {tokenizer.__class__.__name__ if tokenizer else 'None (fallback)'}")

    # Use the real sample report docx in the project
    sample_file = BASE_DIR / "Project_Compass_Mini_Project_Report.docx"
    if not sample_file.exists():
        # Fallback to test markdown
        sample_file = BASE_DIR / ".pytest_cache" / "README.md"
    
    print(f"Testing on sample document: {sample_file.name}")
    sections = extract_document_content(str(sample_file))
    print(f"Extracted sections/pages: {len(sections)}")

    chunks = chunk_document_text(sections, chunk_size=600, chunk_overlap=100)
    print(f"Total chunks generated: {len(chunks)}\n")

    for i, c in enumerate(chunks[:10]):
        text = c["content"]
        tokens = c["metadata"]["token_count"]
        chars = c["metadata"]["char_count"]
        page = c["metadata"]["page"]
        section = c["metadata"]["section"]

        words = text.split()
        first_10 = " ".join(words[:10])
        last_10 = " ".join(words[-10:]) if len(words) > 10 else " ".join(words)

        starts_clean = text[0].isupper() or text[0] in ('#', '-', '*', '[')
        ends_clean = text[-1] in ('.', '!', '?', '"', "'", '`', ':', ';')

        print(f"--- Chunk #{i+1} (Page {page}, Section: '{section}') ---")
        print(f"Tokens: {tokens} | Chars: {chars} | Words: {len(words)}")
        print(f"  First 10 words: {first_10}")
        print(f"  Last 10 words:  {last_10}")
        print(f"  Starts with capital/heading: {starts_clean} | Ends with punctuation: {ends_clean}")
        print()

    print("=== Stage 2 Audit Test Complete ===")

if __name__ == "__main__":
    main()
