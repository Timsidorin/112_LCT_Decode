import fitz  # PyMuPDF
import os

pdf_path = "backend/scripts/manual_study_journal.pdf"
output_dir = "scratch/pdf_inspect"
os.makedirs(output_dir, exist_ok=True)

doc = fitz.open(pdf_path)
print(f"Number of pages: {len(doc)}")

for i in range(len(doc)):
    page = doc[i]
    text = page.get_text()
    with open(f"{output_dir}/page_{i+1}.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    # Save page as image to inspect screenshots
    pix = page.get_pixmap()
    pix.save(f"{output_dir}/page_{i+1}.png")
    
    # Check for images inside
    image_list = page.get_images(full=True)
    print(f"Page {i+1}: {len(image_list)} images")
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        with open(f"{output_dir}/page_{i+1}_img_{img_index}.{image_ext}", "wb") as f:
            f.write(image_bytes)

doc.close()
