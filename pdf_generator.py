import tempfile, os, re
from playwright.sync_api import sync_playwright

def build_html(r):
    def dot():
        return '<span class="dot"></span>'

    def org_row(org, role, location, date):
        return f'''
        <div class="org-row">
          <span class="org-name">{org} &mdash; {role}</span>
          <span class="org-location">{location}</span>
          <span style="flex:1"></span>
          <span class="org-date">{date}</span>
        </div>'''

    def bullet_list(bullets):
        items = "".join(f'<li>{dot()}{b}</li>' for b in bullets)
        return f'<ul class="bullets">{items}</ul>'

    # Build sections
    sections_html = ""
    for section in r.get("sections", []):
        entries_html = ""
        for i, entry in enumerate(section.get("entries", [])):
            mt = 'style="margin-top:4px;"' if i > 0 else ""
            entries_html += f'{org_row(entry["org"], entry["role"], entry.get("location",""), entry.get("date",""))} {bullet_list(entry.get("bullets",[]))}'
            if i > 0:
                entries_html = entries_html.replace('class="org-row"', f'class="org-row" style="margin-top:4px;"', 1)

        sections_html += f'''
        <div class="section">
          <div class="section-head">{section["title"]}</div>
          <hr class="section-rule">
          {entries_html}
        </div>'''

    # Education
    edu_html = ""
    for edu in r.get("education", []):
        degrees = "".join(f'<li>{dot()}{d}</li>' for d in edu.get("degrees", []))
        courses = f'<li>{dot()}{", ".join(edu["courses"])}</li>' if edu.get("courses") else ""
        edu_html += f'''
        <div class="org-row">
          <span class="org-name">{edu["school"]}</span>
          <span class="org-location">{edu.get("location","")}</span>
          <span style="flex:1"></span>
          <span class="org-date">{edu.get("date","")}</span>
        </div>
        <ul class="bullets">{degrees}{courses}</ul>'''

    # Skills
    skills = r.get("technical_skills", [])
    skills_html = "".join(
        f'<div class="skill-item">{dot()}{s}</div>' for s in skills
    )
    n_cols = len(skills) if skills else 3

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Carlito', 'Liberation Sans', sans-serif;
    font-size: 9.5pt; color: #1a1a1a; background: white;
    width: 7.72in; margin: 0 auto; padding: 0; line-height: 1.33;
  }}
  .name {{
    font-family: 'Lora', serif; font-size: 27pt; font-weight: 700;
    color: #1a2744; line-height: 1; margin-bottom: 3px; text-align: center;
  }}
  .tagline {{
    font-family: 'Lora', serif; font-size: 12pt; font-style: italic;
    color: #1a2744; margin-bottom: 7px; text-align: center;
  }}
  .header-rule {{ border: none; border-top: 0.75px solid #ccc; margin-bottom: 6px; }}
  .contact {{
    font-size: 9pt; color: #222; display: flex; gap: 20px;
    align-items: center; justify-content: center;
  }}
  .contact a {{ color: #1a2744; text-decoration: none; border-bottom: 0.5px solid #4472c4; }}
  .section {{ margin-top: 9px; }}
  .section-head {{
    font-family: 'Lora', serif; font-size: 12pt; font-style: italic;
    font-weight: 700; color: #1a2744; margin-bottom: 2px;
  }}
  .section-rule {{ border: none; border-top: 0.75px solid #ccc; margin-bottom: 5px; }}
  .org-row {{
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 2px; gap: 6px;
  }}
  .org-name {{ font-weight: 700; font-size: 9.3pt; color: #1a1a1a; flex-shrink: 0; }}
  .org-location {{ font-style: italic; font-size: 8.5pt; color: #666; white-space: nowrap; flex-shrink: 0; }}
  .org-date {{ font-size: 9pt; color: #1a1a1a; white-space: nowrap; flex-shrink: 0; }}
  .bullets {{ list-style: none; margin: 0; padding: 0; }}
  .bullets li {{
    display: flex; align-items: flex-start; gap: 6px; margin-bottom: 2px;
    text-align: justify; line-height: 1.35; font-size: 9.2pt;
  }}
  .dot {{
    display: inline-block; width: 6.5px; height: 6.5px; min-width: 6.5px;
    border-radius: 50%; border: 3.25px solid #4472c4;
    margin-top: 3.5px; flex-shrink: 0;
  }}
  .skills-grid {{
    display: grid;
    grid-template-columns: {'1fr ' * n_cols};
    gap: 5px 18px;
  }}
  .skill-item {{
    display: flex; align-items: flex-start; gap: 6px;
    font-size: 9.2pt; line-height: 1.35; text-align: justify;
  }}
</style>
</head>
<body>
<div class="name">Akhil Palanivelu</div>
<div class="tagline">{r.get("tagline", "Third-Year Aerospace Engineering Student")}</div>
<hr class="header-rule">
<div class="contact">
  <span>&#9993; <a href="mailto:akhilisamazing@gmail.com">akhilisamazing@gmail.com</a></span>
  <span>&#9990; 510) 737-2091</span>
  <span>&#8853; <a href="https://linkedin.com/in/akhil-palanivelu-6b7421311">linkedin.com/in/akhil-palanivelu-6b7421311</a></span>
</div>
<div class="section">
  <div class="section-head">Education</div>
  <hr class="section-rule">
  {edu_html}
</div>
{sections_html}
<div class="section">
  <div class="section-head">Technical Skills</div>
  <hr class="section-rule">
  <div class="skills-grid">{skills_html}</div>
</div>
</body>
</html>'''


def trim_to_fit(r, html, target_pages=1):
    """Iteratively trim bullets until PDF fits target pages."""
    with sync_playwright() as p:
        browser = p.chromium.launch()

        def get_pages(h):
            page = browser.new_page(viewport={"width": 816, "height": 1400})
            page.set_content(h, wait_until="networkidle")
            page.wait_for_timeout(500)
            margins = {"top": "0.39in", "bottom": "0.39in", "left": "0.39in", "right": "0.39in"}
            pdf = page.pdf(format="Letter", margin=margins, print_background=True)
            page.close()
            import re as re2
            counts = re2.findall(rb'/Count (\d+)', pdf)
            return int(counts[0]) if counts else 99, pdf

        pages, pdf_bytes = get_pages(html)

        # Trim bullets one at a time from least important entries until it fits
        attempts = 0
        while pages > target_pages and attempts < 20:
            attempts += 1
            trimmed = False
            # Find the section with the most bullets and trim the last one
            for section in r.get("sections", []):
                for entry in reversed(section.get("entries", [])):
                    if len(entry.get("bullets", [])) > 1:
                        entry["bullets"] = entry["bullets"][:-1]
                        trimmed = True
                        break
                if trimmed:
                    break
            if not trimmed:
                break
            html = build_html(r)
            pages, pdf_bytes = get_pages(html)

        browser.close()
        return pdf_bytes, pages


def generate_resume_pdf(resume_data):
    html = build_html(resume_data)
    pdf_bytes, pages = trim_to_fit(resume_data, html)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()
    return tmp.name
