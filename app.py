import os
import json
import re
from flask import Flask, request, jsonify, send_file, render_template
from openai import OpenAI
from pdfgenerator import generate_resume_pdf

app = Flask(__name__)

BACKGROUND = """
NAME: Akhil Palanivelu
EMAIL: akhilisamazing@gmail.com
PHONE: 510 737-2091
LINKEDIN: linkedin.com/in/akhil-palanivelu-6b7421311

EDUCATION:
San Jose State University, San Jose CA, Aug 2025 - May 2027
- B.S. Aerospace Engineering (in progress), GPA: 3.5
- Coursework: Thermodynamics, Materials Engineering, Statics, Physics, CAD, Rigid Body Dynamics, Aerodynamics (in progress)

ENGINEERING EXPERIENCE:
Spartan Racing - SJSU Formula SAE, Aerodynamics Intern, San Jose CA, Aug 2025 - Present
- Contribute to aerodynamic concept development for a student-built Formula race car, supporting design, simulation preparation, and composite manufacturing of aerodynamic components
- Basic CAD modeling and design iteration of aerodynamic elements including front wing, rear wing, and canards using SpaceClaim and SolidWorks
- Basic CFD workflow setup and aerodynamic analysis preparation using Siemens STAR-CCM+, developing familiarity with simulation boundary conditions, meshing strategies, and aerodynamic performance evaluation
- Participate in composite fabrication using carbon fiber layups, including epoxy and hardener mixing, multi-ply laminate construction, and vacuum bagging processes
- Prepare manufacturing molds through sanding, finishing, and surface treatment to ensure dimensional accuracy and high-quality composite part release
- Assist with hybrid composite manufacturing approaches using both wet layup and prepreg components
- Gain hands-on experience with lightweight structural materials, composite bonding techniques, and quality control inspection processes

NASA National Community College Aerospace Scholars (NCAS), Virtual, Aug 2024 - Oct 2024
- Completed a multi-mission online program providing an in-depth overview of NASA mission directorates and aerospace research initiatives
- Researched and developed an infographic detailing NASA's Orbiting Carbon Observatory (OCO) missions
- Collaborated in a team-based simulation project exploring lunar technologies, focusing on planning and logistics of material transport from Earth to Moon
- Gained practical exposure to systems integration, prioritization, and trade-off decision-making through NASA-style design challenges
- Achieved an 85% average score across knowledge assessments

PROFESSIONAL EXPERIENCE:
Panda Restaurant Group - Side Cook, Fremont CA, Sep 2025 - Present
- Execute high-throughput food production in a time-critical environment, maintaining consistent quality while managing multiple simultaneous cooking and preparation processes
- Operate and maintain industrial cooking equipment while adhering to strict safety and sanitation standards
- Manage real-time demand by adjusting production rates based on customer volume, minimizing downtime and preventing supply shortages
- Maintain operational readiness of workstation by restocking ingredients, monitoring inventory levels, and coordinating with team members
- Perform end-of-shift closeout procedures including full-facility cleaning, equipment sanitation, waste management, and compliance with corporate safety protocols
- Cross-trained in front-of-house customer operations including order fulfillment, POS transactions, and logistics coordination for online order systems

Burlington Stores - Shortage Control Associate, Fremont CA, Sep 2025 - Nov 2025
- Maintained front-of-store security operations by monitoring customer entry/exit points and sustaining a controlled and safe retail environment
- Demonstrated strong situational awareness and risk assessment by identifying suspicious behaviors and escalating potential security concerns to management
- Enforced company asset protection and compliance procedures by conducting employee bag inspections and documenting verification records
- Delivered consistent customer interaction through confident, high-visibility presence
- Collaborated with leadership and cross-functional staff to support shortage reduction initiatives

Brains & Motion Education - Instructor, San Francisco Bay Area, Mar 2025 - May 2025
- Led weekly after-school basketball classes as primary instructor for 11 students (ages 5-11), designing inclusive workouts accounting for age, size, skill, coordination, and interest differences
- Adjusted workouts in real time to maintain engagement and safety across diverse needs
- Conducted post-session feedback circles to review daily objectives, assess individual and group progress, and reinforce key lessons
- Took initiative to clarify operational breakdowns between school staff and company leadership during a scheduling conflict, facilitating creation of a direct line of communication
- Supported instruction at a second school as assistant coach

Whole Foods Market - In-Store E-Commerce Shopper, Fremont CA, Sep 2024 - Dec 2024
- Optimized fulfillment workflows by planning efficient in-store navigation paths for high-volume online orders (averaging 80 items/hour)
- Coordinated cross-functional operations across Bakery, Seafood, and Catering departments to deliver accurate, time-sensitive orders
- Implemented process improvement by identifying more efficient delivery methods
- Adapted rapidly across departments proving versatility and quick onboarding into unfamiliar systems
- Maintained concurrent priorities, balancing customer service duties with fulfillment quotas

SKILLS:
Materials & Manufacturing: Composite fabrication (carbon fiber layup, vacuum bagging), mold preparation, epoxy systems, laminate construction, surface finishing, quality inspection
Engineering Tools: SolidWorks, SpaceClaim, Siemens STAR-CCM+, Microsoft Excel, Word, PowerPoint
Experimental & Analytical: Meshing strategies, simulation preparation, design iteration, process optimization, documentation & reporting
Core Competencies: Systems thinking, cross-functional coordination, high-pressure execution, technical communication, rapid prototyping
"""

SYSTEM_PROMPT = """You are an expert resume writer and ATS specialist.

Given a candidate's background and a job description, produce a tailored resume as JSON.

STRICT RULES:
- Only use experience and skills that exist in the candidate's background — do NOT invent, fabricate, or imply experience they don't have
- Mirror exact keywords and language from the job description where they honestly apply
- Select the most relevant bullets for this role (max 5 per position)
- Rewrite bullets using strong action verbs
- Choose section titles that match the role (e.g. "Operations Experience" instead of "Engineering Experience" for non-engineering roles)
- Only include courses relevant to this specific job
- Tailor the tagline to the role level, not the role title
- For technical_skills: 3 columns, each one dense and specific, only real skills from the background

Return ONLY valid JSON, no backticks, no explanation:
{
  "job_title": "extracted job title",
  "company": "extracted company name",
  "tagline": "tailored one-line descriptor",
  "ats_keywords": ["kw1","kw2","kw3","kw4","kw5","kw6","kw7","kw8"],
  "education": [
    {
      "school": "San Jose State University",
      "location": "San Jose, CA",
      "date": "Aug 2025 – May 2027",
      "degrees": ["B.S. Aerospace Engineering (in progress) | GPA: 3.5"],
      "courses": ["only","relevant","courses"]
    }
  ],
  "sections": [
    {
      "title": "Section Title",
      "entries": [
        {
          "org": "Org name",
          "role": "Role title",
          "location": "City, ST",
          "date": "Mon Year – Mon Year",
          "bullets": ["bullet","bullet","bullet"]
        }
      ]
    }
  ],
  "technical_skills": [
    "Category: item, item, item",
    "Category: item, item, item",
    "Category: item, item, item"
  ]
}"""


def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return "ok", 200


@app.post("/generate")
def generate():
    data = request.get_json(silent=True) or {}
    job_description = data.get("job_description", "").strip()

    if not job_description:
        return jsonify({"error": "No job description provided"}), 400

    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            temperature=0.3,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Candidate background:\n{BACKGROUND}\n\nJob description:\n{job_description}"
                }
            ]
        )
        raw = response.choices[0].message.content or ""
        raw = re.sub(r"```json|```", "", raw).strip()
        resume_data = json.loads(raw)
    except json.JSONDecodeError as e:
        return jsonify({"error": f"AI returned invalid JSON: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"OpenAI request failed: {str(e)}"}), 500

    try:
        pdf_path = generate_resume_pdf(resume_data)
        job_title = resume_data.get("job_title", "Resume").replace(" ", "_")[:30]
        filename = f"Akhil_Palanivelu_{job_title}.pdf"

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )
    except Exception as e:
        return jsonify({
            "error": f"PDF generation failed: {str(e)}",
            "resume_data": resume_data
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
