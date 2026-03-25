import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from litellm import completion
from docx import Document
from docx.shared import Pt, RGBColor

# Initialize the FastAPI App
app = FastAPI(
    title="DPIA Enterprise API",
    description="The backend engine for generating Data Protection Impact Assessments.",
    version="1.0.0"
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any website to connect
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A simple welcome message so we know the server is awake!
@app.get("/")
def home():
    return {"message": "✅ DPIA Enterprise API is running 24/7!"}

class ProjectDetails(BaseModel):
    license_key: str = "FREE"
    project_name: str
    project_desc: str
    geo_scope: str # NEW
    data_subjects: str
    data_collected: str
    collection_source: str # NEW
    purpose_assessment: str # NEW
    transparency_measures: str # NEW
    data_minimization: str # NEW
    data_quality: str # NEW
    security_measures: str # NEW
    intl_transfers: str # NEW
    retention_policy: str # NEW
    individual_rights: str # NEW
    initial_risk: str

class FinalReportRequest(ProjectDetails):
    identified_risks: str

@app.post("/api/analyze")
async def analyze_risks(data: ProjectDetails):
    prompt = f"""
    Act as a Privacy Risk Assessor. Review the following project:
    - Name: {data.project_name}
    - Description: {data.project_desc}
    - Subjects: {data.data_subjects}
    - Data: {data.data_collected}
    - Retention: {data.retention}
    - Third Parties: {data.third_parties}
    
    Identify ALL relevant privacy risks for this project based on standard global privacy frameworks (like GDPR and Uganda DPPA). 
    For EACH risk, provide: 1. Risk Description. 2. Recommended Mitigation.
    Present this as a clean list. Do not use tables.
    """
    try:
        response = completion(model="gemini/gemini-2.5-flash", messages=[{"role": "user", "content": prompt}])
        return {"status": "success", "risks": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def add_formatted_text_to_word(doc, text):
    lines = text.split('\n')
    in_table = False
    table = None
    
    for line in lines:
        line = line.strip()
        if not line:
            in_table = False
            continue
            
        if line.startswith('|'):
            parts = line.split('|')
            cells = [p.strip() for p in parts[1:-1]]
            
            # --- THE FIX: Skip the row if it only contains dashes or colons ---
            if all(all(c in '-: ' for c in cell) for cell in cells) and len(cells) > 0:
                continue
                
            if not in_table:
                table = doc.add_table(rows=1, cols=len(cells))
                table.style = 'Table Grid'
                hdr_cells = table.rows[0].cells
                for i, cell_text in enumerate(cells):
                    clean_text = cell_text.replace('**', '').replace('<br>', '\n').strip()
                    hdr_cells[i].text = clean_text
                    if hdr_cells[i].paragraphs[0].runs:
                        hdr_cells[i].paragraphs[0].runs[0].bold = True 
                in_table = True
            else:
                row_cells = table.add_row().cells
                for i, cell_text in enumerate(cells):
                    if i < len(row_cells):
                        row_cells[i].text = cell_text.replace('**', '').replace('<br>', '\n').strip()
            continue
        else:
            in_table = False

        if line.startswith('## '):
            doc.add_heading(line[3:], level=2)
        elif line.startswith('# '):
            doc.add_heading(line[2:], level=1)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph(style='List Bullet')
            _add_bold_runs(p, line[2:])
        else:
            p = doc.add_paragraph()
            _add_bold_runs(p, line)
def _add_bold_runs(paragraph, text):
    parts = text.split('**')
    for i, part in enumerate(parts):
        run = paragraph.add_run(part)
        if i % 2 != 0: 
            run.bold = True

@app.post("/api/generate-report")
async def generate_final_report(data: FinalReportRequest):
    prompt = f"""
    Act as a Senior Privacy Counsel. Write a final Data Protection Impact Assessment (DPIA).
    Context:
    - Project: {data.project_name} ({data.project_desc})
    The initial assessment identified the following risks and mitigations:
    {data.identified_risks}
    
    Write the final DPIA report structured exactly like this using Markdown:
    ## 1. Executive Summary
    ## 2. Scope of Processing
    ## 3. Privacy Risks, Mitigation & Required Evidence
    (MUST draw a Markdown Table with exactly 3 columns: Privacy Risk | Recommended Mitigation | Evidence Required for Audit. Make a row for EVERY risk identified. No HTML tags.)
    ## 4. Final Risk Rating & Justification
    
    DO NOT use the words "AI", "AI recommendation", "Artificial Intelligence".
    """
    try:
        response = completion(model="gemini/gemini-2.5-flash", messages=[{"role": "user", "content": prompt}])
        ai_report = response.choices[0].message.content
        
        doc = Document()
        normal_style = doc.styles['Normal']
        normal_style.font.name = 'Arial'
        title_style = doc.styles['Title']
        title_style.font.name = 'Century Gothic'
        title_style.font.size = Pt(24)
        h2_style = doc.styles['Heading 2']
        h2_style.font.name = 'Century Gothic'
        h2_style.font.size = Pt(14)
        
        doc.add_paragraph('Data Protection Impact Assessment', style='Title')
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Light Shading'
        
        table.cell(0, 0).text = "Project Name:"
        table.cell(0, 0).paragraphs[0].runs[0].bold = True
        table.cell(0, 1).text = data.project_name
        
        table.cell(1, 0).text = "Data Subjects:"
        table.cell(1, 0).paragraphs[0].runs[0].bold = True
        table.cell(1, 1).text = data.data_subjects
        
        table.cell(2, 0).text = "Status:"
        table.cell(2, 0).paragraphs[0].runs[0].bold = True
        table.cell(2, 1).text = "Completed & Assessed"
        doc.add_paragraph()
        
        add_formatted_text_to_word(doc, ai_report)
        
        # Save to a temporary folder the cloud server uses
        file_name = f"/tmp/{data.project_name.replace(' ', '_')}_Final_DPIA.docx"
        doc.save(file_name)
        
        return FileResponse(path=file_name, filename=f"{data.project_name.replace(' ', '_')}_Final_DPIA.docx", media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        return {"status": "error", "message": str(e)}
