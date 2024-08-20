import requests
from bs4 import BeautifulSoup
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import re

def fetch_html(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def clean_text(text):
    text = text.replace('_x000D_', '')
    text = text.replace('\r', '') 
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_lyrics(html_content):
    soup = BeautifulSoup(html_content, 'lxml')

    lyrics = []
    for p in soup.find_all('p'):
        if 'LYRICS:' in p.text:
            next_sibling = p.find_next_sibling()
            while next_sibling and next_sibling.name == 'p':
                cleaned_text = clean_text(next_sibling.text.strip())
                lyrics.append(cleaned_text)
                next_sibling = next_sibling.find_next_sibling()
            break
    
    lyrics_text = "\n".join(lyrics)
    return lyrics_text


def create_ppt(lyrics, output_file):
    prs = Presentation()

    verses = lyrics.split('\n\n')
    
    for verse in verses:
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # Use a blank slide layout
        textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5.5))
        text_frame = textbox.text_frame
        text_frame.text = verse.strip()
        
        # Center the text and make it bigger
        for paragraph in text_frame.paragraphs:
            paragraph.font.size = Pt(32)  # Set the font size
            paragraph.alignment = PP_ALIGN.CENTER  # Center the text
            paragraph.font.color.rgb = RGBColor(0, 0, 0)  # Optional: Set text color to black

        text_frame.word_wrap = True  # Ensure text wraps within the box
        textbox.left = Inches(1)  # Center the textbox horizontally
        textbox.top = Inches(1.5)  # Adjust the vertical position for better centering

    prs.save(output_file)

if __name__ == "__main__":
    url = "https://kksongs.org/songs/c/cikanakalagalayamala.html"

    html_content = fetch_html(url)

    lyrics = extract_lyrics(html_content)

    create_ppt(lyrics, 'lyrics_presentation.pptx')

    print("PowerPoint presentation created: lyrics_presentation.pptx")
